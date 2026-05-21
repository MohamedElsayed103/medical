"""
Dynamic RBAC permission classes.

Replaces the old hardcoded role-based permission system with a
WhiteMatter-style resource:action permission check.

Usage in views:
    from apps.rbac.permissions import HasPermission, IsActiveTenantUser

    class PatientViewSet(ModelViewSet):
        permission_classes = [IsAuthenticated, IsActiveTenantUser]

        def get_permissions(self):
            if self.action in ['list', 'retrieve']:
                return [IsAuthenticated(), HasPermission('patients:read')]
            return [IsAuthenticated(), HasPermission('patients:write')]

    # Or use the WhiteMatter-style decorator (simpler):
    from apps.rbac.permissions import require_permission

    class PatientViewSet(ModelViewSet):
        @require_permission("patients:read")
        def list(self, request): ...

        @require_permission("patients:write")
        def create(self, request): ...
"""
from functools import wraps

from django.db import connection
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .models import TenantUser, TenantUserStatus


def get_tenant_user(request) -> TenantUser | None:
    """
    Retrieve (and cache on request) the TenantUser for the current
    authenticated user in the current tenant schema.
    """
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return None

    if hasattr(request, "_cached_tenant_user"):
        return request._cached_tenant_user

    schema_name = connection.schema_name
    if schema_name == "public":
        request._cached_tenant_user = None
        return None

    try:
        tenant_user = (
            TenantUser.objects.select_related("role")
            .get(
                user_id=request.user.id,
                is_deleted=False,
            )
        )
    except TenantUser.DoesNotExist:
        tenant_user = None

    request._cached_tenant_user = tenant_user
    return tenant_user


class IsActiveTenantUser(BasePermission):
    """
    User must have an active TenantUser profile in the current tenant.
    Passes through for public-schema endpoints.
    """

    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        if connection.schema_name == "public":
            return True
        tenant_user = get_tenant_user(request)
        if tenant_user is None:
            return False
        return tenant_user.status == TenantUserStatus.ACTIVE


class HasPermission(BasePermission):
    """
    Dynamic permission check: user's role must include the specified
    permission (resource:action pattern).

    Instantiate with the required permission name:
        HasPermission('patients:read')
    """

    def __init__(self, permission_name: str = ""):
        self.permission_name = permission_name

    def has_permission(self, request, view):
        if connection.schema_name == "public":
            return True

        tenant_user = get_tenant_user(request)
        if tenant_user is None:
            return False

        if tenant_user.status != TenantUserStatus.ACTIVE:
            return False

        # Cache permissions on request
        if not hasattr(request, "_cached_permissions"):
            from .services import RBACService
            request._cached_permissions = RBACService.get_user_permissions(tenant_user)

        return self.permission_name in request._cached_permissions


class IsPlatformAdmin(BasePermission):
    """User must be a platform superadmin (public schema level)."""

    message = "Platform administrator access required."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff)
        )


# ── Convenience permission factories ──────────────────────────────


def require_permission(permission_name: str):
    """
    Factory helper for use in get_permissions() overrides.

    Usage:
        def get_permissions(self):
            if self.action == 'list':
                return [IsAuthenticated(), require_permission('patients:read')]
            return [IsAuthenticated(), require_permission('patients:write')]
    """
    return HasPermission(permission_name)


# ── WhiteMatter-style decorator for DRF views ─────────────────────


def check_permission(permission: str):
    """
    Decorator that requires a specific permission.

    WhiteMatter pattern: @require_permission("assessments:read") on routes.
    Adapted for DRF: checks the tenant user's role permissions.

    Usage:
        @check_permission("patients:read")
        def list(self, request):
            ...

        @check_permission("roles:write")
        @action(detail=True, methods=["post"])
        def assign(self, request, pk=None):
            ...

    Raises:
        PermissionDenied: If user lacks the required permission
    """
    def decorator(func):
        @wraps(func)
        def wrapper(view_or_self, request, *args, **kwargs):
            # Skip in public schema
            if connection.schema_name == "public":
                return func(view_or_self, request, *args, **kwargs)

            tenant_user = get_tenant_user(request)
            if tenant_user is None:
                raise PermissionDenied("You are not a member of this organization.")

            if tenant_user.status != TenantUserStatus.ACTIVE:
                raise PermissionDenied("Your account is not active.")

            # Cache permissions on request
            if not hasattr(request, "_cached_permissions"):
                from .services import RBACService
                request._cached_permissions = RBACService.get_user_permissions(tenant_user)

            if permission not in request._cached_permissions:
                raise PermissionDenied(
                    f"Permission '{permission}' required."
                )

            return func(view_or_self, request, *args, **kwargs)
        return wrapper
    return decorator


# ── Legacy compatibility aliases (map old role checks to permissions) ─


class CanReadPatients(HasPermission):
    def __init__(self):
        super().__init__("patients:read")


class CanWritePatients(HasPermission):
    def __init__(self):
        super().__init__("patients:write")


class CanReadAppointments(HasPermission):
    def __init__(self):
        super().__init__("appointments:read")


class CanWriteAppointments(HasPermission):
    def __init__(self):
        super().__init__("appointments:write")


class CanReadMedicalRecords(HasPermission):
    def __init__(self):
        super().__init__("medical_records:read")


class CanWriteMedicalRecords(HasPermission):
    def __init__(self):
        super().__init__("medical_records:write")


class CanReadPrescriptions(HasPermission):
    def __init__(self):
        super().__init__("prescriptions:read")


class CanWritePrescriptions(HasPermission):
    def __init__(self):
        super().__init__("prescriptions:write")


class CanReadLabResults(HasPermission):
    def __init__(self):
        super().__init__("lab_results:read")


class CanWriteLabResults(HasPermission):
    def __init__(self):
        super().__init__("lab_results:write")


class CanReadBilling(HasPermission):
    def __init__(self):
        super().__init__("billing:read")


class CanWriteBilling(HasPermission):
    def __init__(self):
        super().__init__("billing:write")


class CanReadPharmacy(HasPermission):
    def __init__(self):
        super().__init__("pharmacy:read")


class CanWritePharmacy(HasPermission):
    def __init__(self):
        super().__init__("pharmacy:write")


class CanManageUsers(HasPermission):
    def __init__(self):
        super().__init__("users:write")


class CanManageRoles(HasPermission):
    def __init__(self):
        super().__init__("roles:write")


class CanSendInvitations(HasPermission):
    def __init__(self):
        super().__init__("invitations:write")
