"""
Accounts views — platform-level authentication endpoints.

Handles: registration, login, token refresh, profile, PIN verification, API keys.
Tenant-level RBAC management lives in apps.rbac.views.
"""
from drf_spectacular.utils import extend_schema, inline_serializer
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common.utils import verify_pin

from .models import User, UserTenantMapping
from .serializers import MeSerializer, VerifyPinSerializer
from .services import AccountService, UserSecretsService


# ── Re-usable inline schemas for Swagger ──────────────────────────
_TokensSchema = inline_serializer("Tokens", fields={
    "access": drf_serializers.CharField(),
    "refresh": drf_serializers.CharField(),
})
_UserBriefSchema = inline_serializer("UserBrief", fields={
    "id": drf_serializers.UUIDField(),
    "email": drf_serializers.EmailField(),
    "first_name": drf_serializers.CharField(),
    "last_name": drf_serializers.CharField(),
})
_TenantMappingSchema = inline_serializer("TenantMapping", fields={
    "id": drf_serializers.UUIDField(),
    "tenant_id": drf_serializers.UUIDField(),
    "tenant_name": drf_serializers.CharField(),
    "tenant_slug": drf_serializers.CharField(),
})


@method_decorator(ratelimit(key="ip", rate="5/m", block=True), name="post")
class RegisterView(APIView):
    """POST /api/v1/auth/register/ — register a new user."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=inline_serializer("RegisterInput", fields={
            "email": drf_serializers.EmailField(),
            "password": drf_serializers.CharField(),
            "first_name": drf_serializers.CharField(required=False),
            "last_name": drf_serializers.CharField(required=False),
        }),
        responses={201: inline_serializer("RegisterResponse", fields={
            "user": _UserBriefSchema,
            "tokens": _TokensSchema,
        })},
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        if not email or not password:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Email and password are required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": {"code": "USER_EXISTS", "message": "A user with this email already exists."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(ratelimit(key="ip", rate="5/m", block=True), name="post")
class LoginView(APIView):
    """POST /api/v1/auth/login/ — login with email/password."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=inline_serializer("LoginInput", fields={
            "email": drf_serializers.EmailField(),
            "password": drf_serializers.CharField(),
        }),
        responses={200: inline_serializer("LoginResponse", fields={
            "user": _UserBriefSchema,
            "tenants": drf_serializers.ListField(child=_TenantMappingSchema),
            "tokens": _TokensSchema,
        })},
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Email and password are required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email, is_deleted=False)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": {"code": "INACTIVE_USER", "message": "User account is deactivated."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        tenant_mappings = AccountService.get_user_tenant_mappings(user)

        # Update last_login
        from django.utils import timezone as tz
        user.last_login = tz.now()
        user.save(update_fields=["last_login"])

        return Response({
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "tenants": [
                {
                    "id": str(m.id),
                    "tenant_id": str(m.tenant_id),
                    "tenant_name": m.tenant.name,
                    "tenant_slug": m.tenant.slug,
                }
                for m in tenant_mappings
            ],
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        })


class TokenRefreshView(APIView):
    """POST /api/v1/auth/token/refresh/ — refresh access token."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=inline_serializer("TokenRefreshInput", fields={
            "refresh": drf_serializers.CharField(),
        }),
        responses={200: inline_serializer("TokenRefreshResponse", fields={
            "access": drf_serializers.CharField(),
        })},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                "access": str(refresh.access_token),
            })
        except Exception:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired refresh token."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeView(APIView):
    """GET /api/v1/auth/me/ — current user profile + tenant context.

    When accessed via a tenant domain, additionally returns the user's
    role and permissions within that tenant (WhiteMatter /auth/me pattern).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["auth"], responses={200: MeSerializer})
    def get(self, request):
        from django.db import connection

        user = request.user
        tenant_mappings = AccountService.get_user_tenant_mappings(user)

        data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at,
            "tenants": [
                {
                    "id": str(m.id),
                    "tenant_id": str(m.tenant_id),
                    "tenant_name": m.tenant.name,
                    "tenant_slug": m.tenant.slug,
                }
                for m in tenant_mappings
            ],
        }

        # If in tenant schema, include role and permissions (WhiteMatter pattern)
        if connection.schema_name != "public":
            from apps.rbac.permissions import get_tenant_user
            from apps.rbac.services import RBACService

            tenant_user = get_tenant_user(request)
            if tenant_user:
                data["tenant_context"] = {
                    "tenant_user_id": str(tenant_user.id),
                    "role": str(tenant_user.role_id),
                    "role_name": tenant_user.role.name,
                    "status": tenant_user.status,
                    "permissions": sorted(RBACService.get_user_permissions(tenant_user)),
                    "specialty": tenant_user.specialty,
                    "license_number": tenant_user.license_number,
                    "qualification": tenant_user.qualification,
                }

        return Response(data)

    @extend_schema(tags=["auth"], request=MeSerializer, responses={200: MeSerializer})
    def patch(self, request):
        user = request.user
        serializer = MeSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VerifyPinView(APIView):
    """POST /api/v1/auth/verify-pin/ — verify clinical quick-access PIN."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        request=VerifyPinSerializer,
        responses={200: inline_serializer("VerifyPinResponse", fields={
            "verified": drf_serializers.BooleanField(),
        })},
    )
    def post(self, request):
        serializer = VerifyPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            secrets = request.user.secrets
        except User.secrets.RelatedObjectDoesNotExist:
            return Response(
                {"error": {"code": "PIN_NOT_SET", "message": "No PIN configured."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not secrets.pin_hash:
            return Response(
                {"error": {"code": "PIN_NOT_SET", "message": "No PIN configured."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verify_pin(serializer.validated_data["pin"], secrets.pin_hash):
            return Response({"verified": True})

        return Response(
            {"error": {"code": "INVALID_PIN", "message": "Incorrect PIN."}},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ApiKeyView(APIView):
    """POST /api/v1/auth/api-keys/ — generate a new API key (shown once).
    DELETE /api/v1/auth/api-keys/ — revoke current API key."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        request=None,
        responses={201: inline_serializer("ApiKeyResponse", fields={
            "api_key": drf_serializers.CharField(),
            "message": drf_serializers.CharField(),
        })},
    )
    def post(self, request):
        raw_key = UserSecretsService.generate_api_key(request.user)
        return Response(
            {
                "api_key": raw_key,
                "message": "Store this key securely. It will not be shown again.",
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["auth"],
        responses={200: inline_serializer("ApiKeyRevokedResponse", fields={
            "message": drf_serializers.CharField(),
        })},
    )
    def delete(self, request):
        """Revoke the current API key."""
        try:
            secrets = request.user.secrets
        except User.secrets.RelatedObjectDoesNotExist:
            return Response(
                {"error": {"code": "NO_API_KEY", "message": "No API key to revoke."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not secrets.api_key_hash:
            return Response(
                {"error": {"code": "NO_API_KEY", "message": "No API key to revoke."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        secrets.api_key_hash = None
        secrets.save(update_fields=["api_key_hash", "updated_at"])
        return Response({"message": "API key revoked successfully."})


# ── Public Invitation Endpoints (WhiteMatter pattern) ─────────────
# These endpoints use the invitation token for authentication
# (no JWT required). Token format: {tenant_slug}.{random_token}


class InvitationInfoView(APIView):
    """
    GET /api/v1/auth/invitation/<token>/ — Get invitation info by token.

    Public endpoint — no authentication required.
    Returns invitation details for the acceptance form.
    (WhiteMatter: GET /auth/invitation/{token})
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        responses={200: inline_serializer("InvitationInfoResponse", fields={
            "email": drf_serializers.EmailField(),
            "role_name": drf_serializers.CharField(),
            "tenant_name": drf_serializers.CharField(),
            "expires_at": drf_serializers.DateTimeField(),
        })},
    )
    def get(self, request, token):
        from apps.rbac.services import InvitationService
        from apps.rbac.models import UserInvitation, InvitationStatus
        from django_tenants.utils import schema_context

        # Parse token to extract tenant slug
        try:
            tenant_slug, full_token = InvitationService.parse_token(token)
        except ValueError:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid invitation token format."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve tenant schema from slug
        from apps.tenants.models import Organization
        try:
            org = Organization.objects.get(slug=tenant_slug)
        except Organization.DoesNotExist:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid invitation token."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Look up invitation in tenant schema
        with schema_context(org.schema_name):
            try:
                invitation = UserInvitation.objects.select_related("role").get(
                    token=full_token,
                    status=InvitationStatus.PENDING,
                    is_deleted=False,
                )
            except UserInvitation.DoesNotExist:
                return Response(
                    {"error": {"code": "INVALID_TOKEN", "message": "Invitation not found or already used."}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check expiry
            from django.utils import timezone as tz
            if invitation.expires_at < tz.now():
                invitation.status = InvitationStatus.EXPIRED
                invitation.save(update_fields=["status", "updated_at"])
                return Response(
                    {"error": {"code": "EXPIRED", "message": "Invitation has expired."}},
                    status=status.HTTP_410_GONE,
                )

            return Response({
                "email": invitation.email,
                "role_name": invitation.role.name,
                "tenant_name": org.name,
                "expires_at": invitation.expires_at,
            })


class AcceptInvitationPublicView(APIView):
    """
    POST /api/v1/auth/invitation/<token>/accept/ — Accept an invitation.

    Public endpoint — no auth required. Creates user account and tenant user.
    (WhiteMatter: POST /auth/invitation/{token}/accept)

    Request body:
        {
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecureP@ss123!"
        }
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        request=inline_serializer("AcceptInvitationInput", fields={
            "first_name": drf_serializers.CharField(),
            "last_name": drf_serializers.CharField(),
            "password": drf_serializers.CharField(min_length=8),
        }),
        responses={201: inline_serializer("AcceptInvitationResponse", fields={
            "message": drf_serializers.CharField(),
            "email": drf_serializers.EmailField(),
            "user_id": drf_serializers.UUIDField(),
            "tenant_name": drf_serializers.CharField(),
        })},
    )
    def post(self, request, token):
        from apps.rbac.services import InvitationService, TenantUserService
        from apps.rbac.models import UserInvitation, InvitationStatus
        from apps.accounts.services import AccountService
        from django_tenants.utils import schema_context

        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        password = request.data.get("password")

        if not password or len(password) < 8:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Password must be at least 8 characters."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse token
        try:
            tenant_slug, full_token = InvitationService.parse_token(token)
        except ValueError:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid invitation token format."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Resolve tenant
        from apps.tenants.models import Organization
        try:
            org = Organization.objects.get(slug=tenant_slug)
        except Organization.DoesNotExist:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid invitation token."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Process invitation within tenant schema
        with schema_context(org.schema_name):
            try:
                invitation = UserInvitation.objects.select_related("role").get(
                    token=full_token,
                    status=InvitationStatus.PENDING,
                    is_deleted=False,
                )
            except UserInvitation.DoesNotExist:
                return Response(
                    {"error": {"code": "INVALID_TOKEN", "message": "Invitation not found or already used."}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check expiry
            from django.utils import timezone as tz
            if invitation.expires_at < tz.now():
                invitation.status = InvitationStatus.EXPIRED
                invitation.save(update_fields=["status", "updated_at"])
                return Response(
                    {"error": {"code": "EXPIRED", "message": "Invitation has expired."}},
                    status=status.HTTP_410_GONE,
                )

            # Create or get the user in public schema
            email = invitation.email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created:
                user.set_password(password)
                user.save()

            # Create UserTenantMapping (public schema)
            AccountService.add_tenant_mapping(
                user=user,
                tenant=org,
                email=email,
                username=user.username or email.split("@")[0],
            )

            # Create TenantUser in schema
            TenantUserService.get_or_create_tenant_user(
                user_id=user.id,
                email=email,
                role=invitation.role,
                first_name=first_name or user.first_name,
                last_name=last_name or user.last_name,
            )

            # Mark invitation as accepted
            invitation.status = InvitationStatus.ACCEPTED
            invitation.accepted_at = tz.now()
            invitation.save(update_fields=["status", "accepted_at", "updated_at"])

        return Response(
            {
                "message": "Invitation accepted successfully.",
                "email": email,
                "user_id": str(user.id),
                "tenant_name": org.name,
            },
            status=status.HTTP_201_CREATED,
        )
