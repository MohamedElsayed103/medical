"""
Accounts views — authentication endpoints and user profile.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from common.utils import verify_pin

from .models import User
from .serializers import MeSerializer, VerifyPinSerializer
from .services import AccountService, UserSecretsService


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — register a new user (dev mode)."""

    permission_classes = [AllowAny]

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


class LoginView(APIView):
    """POST /api/v1/auth/login/ — login with email/password (dev mode)."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Email and password are required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
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
        memberships = AccountService.get_user_memberships(user)

        return Response({
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "memberships": [
                {
                    "id": str(m.id),
                    "tenant_id": str(m.tenant_id),
                    "tenant_name": m.tenant.name,
                    "tenant_slug": m.tenant.slug,
                    "role": m.role,
                }
                for m in memberships
            ],
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        })


class TokenRefreshView(APIView):
    """POST /api/v1/auth/token/refresh/ — refresh access token."""

    permission_classes = [AllowAny]

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
    """GET /api/v1/auth/me/ — current user profile + memberships."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        memberships = AccountService.get_user_memberships(user)
        return Response({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "memberships": [
                {
                    "id": str(m.id),
                    "tenant_id": str(m.tenant_id),
                    "tenant_name": m.tenant.name,
                    "tenant_slug": m.tenant.slug,
                    "role": m.role,
                }
                for m in memberships
            ],
        })

    def patch(self, request):
        user = request.user
        serializer = MeSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VerifyPinView(APIView):
    """POST /api/v1/auth/verify-pin/ — verify clinical quick-access PIN."""

    permission_classes = [IsAuthenticated]

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
    """POST /api/v1/auth/api-keys/ — generate a new API key (shown once)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_key = UserSecretsService.generate_api_key(request.user)
        return Response(
            {
                "api_key": raw_key,
                "message": "Store this key securely. It will not be shown again.",
            },
            status=status.HTTP_201_CREATED,
        )
