"""
Account permissions — re-exports from apps.rbac for backward compatibility.

The old hardcoded role-based permission classes are replaced by the
dynamic RBAC system in apps.rbac.permissions. This module re-exports
the key classes so existing imports continue to work.
"""
from apps.rbac.permissions import (  # noqa: F401
    CanManageRoles,
    CanManageUsers,
    CanReadBilling,
    CanReadLabResults,
    CanReadPatients,
    CanReadPharmacy,
    CanWriteBilling,
    CanWriteLabResults,
    CanWritePatients,
    CanWritePharmacy,
    HasPermission,
    IsActiveTenantUser,
    IsPlatformAdmin,
    get_tenant_user,
)


# Legacy aliases for backward compatibility with existing views
IsTenantMember = IsActiveTenantUser
IsOwnerOrAdmin = CanManageUsers
IsLabTech = CanWriteLabResults
IsBillingStaff = CanWriteBilling


class IsDoctor(HasPermission):
    def __init__(self):
        super().__init__("medical_records:write")


class IsNurseOrAbove(HasPermission):
    def __init__(self):
        super().__init__("patients:write")


class IsReceptionistOrAbove(HasPermission):
    def __init__(self):
        super().__init__("appointments:write")
