"""
Role-based permission classes.

All permissions assume the request has been authenticated (user is set)
and that ``request.tenant`` is resolved by TenantMainMiddleware.
"""
from django.db import connection
from rest_framework.permissions import BasePermission

from common.enums import UserRole

from .models import TenantMembership


def _get_membership(request) -> TenantMembership | None:
    """Retrieve (and cache on request) the user's membership for the current tenant."""
    if hasattr(request, "_cached_membership"):
        return request._cached_membership

    schema_name = connection.schema_name
    if schema_name == "public":
        request._cached_membership = None
        return None

    try:
        membership = TenantMembership.objects.select_related("tenant").get(
            user=request.user,
            tenant__schema_name=schema_name,
            is_active=True,
        )
    except TenantMembership.DoesNotExist:
        membership = None

    request._cached_membership = membership
    return membership


class IsTenantMember(BasePermission):
    """User must be an active member of the current tenant."""

    message = "You are not a member of this organization."

    def has_permission(self, request, view):
        if connection.schema_name == "public":
            return True  # Public-schema endpoints handle their own auth
        return _get_membership(request) is not None


class HasRole(BasePermission):
    """
    Base class: user must have one of the allowed roles in the current tenant.

    Subclass and set ``allowed_roles``.
    """

    allowed_roles: list[str] = []
    message = "You do not have the required role for this action."

    def has_permission(self, request, view):
        membership = _get_membership(request)
        if membership is None:
            return False
        return membership.role in self.allowed_roles


class IsOwnerOrAdmin(HasRole):
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN]


class IsDoctor(HasRole):
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.DOCTOR]


class IsNurseOrAbove(HasRole):
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE]


class IsReceptionistOrAbove(HasRole):
    allowed_roles = [
        UserRole.OWNER,
        UserRole.ADMIN,
        UserRole.DOCTOR,
        UserRole.NURSE,
        UserRole.RECEPTIONIST,
    ]


class IsLabTech(HasRole):
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB_TECH]


class IsBillingStaff(HasRole):
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.BILLING_STAFF]
