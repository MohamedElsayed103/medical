"""
RBAC views — manage roles, permissions, tenant users, and invitations.

These endpoints operate within a tenant schema context. They will return
empty results if accessed from the public schema (e.g., 127.0.0.1).
To use them, access via a tenant domain (e.g., al-noor-clinic.localhost:8000).
"""
from django.db import connection
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import (
    InvitationStatus,
    Permission,
    Role,
    TenantUser,
    TenantUserStatus,
    UserInvitation,
)
from .permissions import (
    HasPermission,
    IsActiveTenantUser,
    get_tenant_user,
)
from .serializers import (
    AcceptInvitationSerializer,
    CreateInvitationSerializer,
    PermissionSerializer,
    RoleCreateSerializer,
    RoleSerializer,
    RoleUpdateSerializer,
    TenantUserProfileSerializer,
    TenantUserSerializer,
    TenantUserUpdateSerializer,
    UserInvitationSerializer,
)
from .services import InvitationService, RBACService, TenantUserService


def _in_tenant_schema():
    """Check if we're in a tenant schema (not public)."""
    return connection.schema_name != "public"


# ── Permissions (read-only listing) ───────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["rbac"], summary="List all permissions"),
    retrieve=extend_schema(tags=["rbac"], summary="Get permission details"),
)
class PermissionViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    List available permissions. Read-only — permissions are system-defined.
    """

    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsActiveTenantUser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not _in_tenant_schema():
            return Permission.objects.none()
        return Permission.objects.filter(is_deleted=False)


# ── Roles ──────────────────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["rbac"], summary="List roles"),
    retrieve=extend_schema(tags=["rbac"], summary="Get role details"),
    create=extend_schema(tags=["rbac"], summary="Create custom role"),
    update=extend_schema(tags=["rbac"], summary="Update role"),
    partial_update=extend_schema(tags=["rbac"], summary="Partially update role"),
    destroy=extend_schema(tags=["rbac"], summary="Delete custom role"),
)
class RoleViewSet(ModelViewSet):
    """
    Manage roles. System roles cannot be deleted.
    Requires 'roles:read' for listing, 'roles:write' for mutations.
    """

    permission_classes = [IsAuthenticated, IsActiveTenantUser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not _in_tenant_schema():
            return Role.objects.none()
        return Role.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.action == "create":
            return RoleCreateSerializer
        if self.action in ("update", "partial_update"):
            return RoleUpdateSerializer
        return RoleSerializer

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system:
            return Response(
                {"error": {"code": "CANNOT_DELETE_SYSTEM_ROLE", "message": "System roles cannot be deleted."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Check if role is in use
        if TenantUser.objects.filter(role=role, is_deleted=False).exists():
            return Response(
                {"error": {"code": "ROLE_IN_USE", "message": "Cannot delete a role that is assigned to users."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Tenant Users ───────────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["rbac"], summary="List tenant users"),
    retrieve=extend_schema(tags=["rbac"], summary="Get tenant user details"),
    partial_update=extend_schema(tags=["rbac"], summary="Update tenant user"),
)
class TenantUserViewSet(
    ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet
):
    """
    Manage users within the current tenant.
    Requires 'users:read' for listing, 'users:write' for mutations.
    """

    permission_classes = [IsAuthenticated, IsActiveTenantUser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not _in_tenant_schema():
            return TenantUser.objects.none()
        return TenantUser.objects.filter(is_deleted=False).select_related("role")

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return TenantUserUpdateSerializer
        return TenantUserSerializer

    @extend_schema(tags=["rbac"], summary="Deactivate a tenant user")
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        tenant_user = self.get_object()
        TenantUserService.deactivate_user(tenant_user)
        return Response({"message": "User deactivated."})

    @extend_schema(tags=["rbac"], summary="Reactivate a tenant user")
    @action(detail=True, methods=["post"], url_path="reactivate")
    def reactivate(self, request, pk=None):
        tenant_user = self.get_object()
        tenant_user.status = TenantUserStatus.ACTIVE
        tenant_user.save(update_fields=["status", "updated_at"])
        return Response({"message": "User reactivated."})

    @extend_schema(tags=["rbac"], summary="Remove user from tenant (soft-delete)")
    @action(detail=True, methods=["post"], url_path="remove")
    def remove(self, request, pk=None):
        tenant_user = self.get_object()
        tenant_user.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Current User Profile (within tenant) ──────────────────────────


@extend_schema_view(
    get=extend_schema(tags=["rbac"], summary="Get my tenant profile"),
    patch=extend_schema(tags=["rbac"], summary="Update my tenant profile"),
)
class MyTenantProfileView(APIView):
    """
    GET/PATCH the current user's profile within the current tenant.
    """

    permission_classes = [IsAuthenticated, IsActiveTenantUser]

    def get(self, request):
        tenant_user = get_tenant_user(request)
        if not tenant_user:
            return Response(
                {"error": {"code": "NOT_A_MEMBER", "message": "You are not a member of this organization."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantUserProfileSerializer(tenant_user)
        return Response(serializer.data)

    def patch(self, request):
        tenant_user = get_tenant_user(request)
        if not tenant_user:
            return Response(
                {"error": {"code": "NOT_A_MEMBER", "message": "You are not a member of this organization."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantUserProfileSerializer(
            tenant_user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Invitations ────────────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["rbac"], summary="List invitations"),
    retrieve=extend_schema(tags=["rbac"], summary="Get invitation details"),
    create=extend_schema(tags=["rbac"], summary="Send invitation"),
)
class InvitationViewSet(
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    """
    Manage user invitations.
    Requires 'invitations:read' for listing, 'invitations:write' for creating.
    """

    permission_classes = [IsAuthenticated, IsActiveTenantUser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not _in_tenant_schema():
            return UserInvitation.objects.none()
        return (
            UserInvitation.objects.filter(is_deleted=False)
            .select_related("role", "invited_by")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return CreateInvitationSerializer
        return UserInvitationSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant_user = get_tenant_user(request)
        role = Role.objects.get(id=serializer.validated_data["role_id"])

        # Get tenant slug for token prefix (WhiteMatter pattern)
        tenant_slug = connection.schema_name.replace("_", "-")

        invitation = InvitationService.create_invitation(
            email=serializer.validated_data["email"],
            role=role,
            invited_by=tenant_user,
            tenant_slug=tenant_slug,
            metadata=serializer.validated_data.get("metadata"),
        )
        return Response(
            UserInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["rbac"], summary="Cancel an invitation")
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        invitation = self.get_object()
        try:
            InvitationService.cancel_invitation(invitation)
        except ValueError as e:
            return Response(
                {"error": {"code": "INVALID_ACTION", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Invitation cancelled."})

    @extend_schema(tags=["rbac"], summary="Resend an invitation (generates new token)")
    @action(detail=True, methods=["post"], url_path="resend")
    def resend(self, request, pk=None):
        invitation = self.get_object()
        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"error": {"code": "INVALID_ACTION", "message": "Can only resend pending invitations."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Create a new invitation (old one will be cancelled by the service)
        tenant_user = get_tenant_user(request)
        new_invitation = InvitationService.create_invitation(
            email=invitation.email,
            role=invitation.role,
            invited_by=tenant_user,
            metadata=invitation.metadata,
        )
        return Response(
            UserInvitationSerializer(new_invitation).data,
            status=status.HTTP_201_CREATED,
        )


# ── Accept Invitation (public endpoint) ───────────────────────────


class AcceptInvitationView(APIView):
    """
    POST /api/v1/rbac/invitations/accept/ — Accept an invitation.
    Requires authentication (user must have registered first).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["rbac"],
        request=AcceptInvitationSerializer,
        summary="Accept an invitation token",
    )
    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tenant_user = InvitationService.accept_invitation(
                token=serializer.validated_data["token"],
                user_id=request.user.id,
            )
        except ValueError as e:
            return Response(
                {"error": {"code": "INVALID_INVITATION", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            TenantUserSerializer(tenant_user).data,
            status=status.HTTP_201_CREATED,
        )


# ── Seed Roles (admin/setup endpoint) ─────────────────────────────


class SeedRolesView(APIView):
    """
    POST /api/v1/rbac/seed/ — Seed system roles and permissions.
    Only callable by platform admins. Idempotent.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["rbac"], summary="Seed system roles and permissions")
    def post(self, request):
        # Only allow platform admins or the first setup
        if not request.user.is_staff and TenantUser.objects.exists():
            return Response(
                {"error": {"code": "FORBIDDEN", "message": "Only platform admins can seed roles."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        roles, permissions = RBACService.seed_roles_and_permissions()
        return Response({
            "message": "Roles and permissions seeded successfully.",
            "roles_count": len(roles),
            "permissions_count": len(permissions),
        })
