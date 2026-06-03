"""
RBAC service layer — business logic for role/permission management,
user provisioning within tenants, and invitation flow.

Follows WhiteMatter identity context patterns:
- Fixed Admin role UUID for deterministic provisioning
- Token format: {tenant_slug}.{random_token} for O(1) schema resolution
- 7-day invitation expiry
- Seeded permissions/roles during tenant creation
"""
import secrets
import uuid
from datetime import timedelta

import structlog
from django.utils import timezone

from .models import (
    InvitationStatus,
    Permission,
    Role,
    RolePermission,
    TenantUser,
    TenantUserStatus,
    UserInvitation,
)

logger = structlog.get_logger(__name__)

# Fixed Admin Role UUID — deterministic for tenant provisioning
# (WhiteMatter pattern: admin role always has this ID)
ADMIN_ROLE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Invitation token length
TOKEN_LENGTH = 64

# Invitation expiry (WhiteMatter: 7 days)
INVITATION_EXPIRY_DAYS = 7

# ── Default system roles and permissions for medical platform ─────

SYSTEM_ROLES = [
    {"name": "Admin", "description": "Full access to all resources in the organization"},
    {"name": "Doctor", "description": "Access to patients, appointments, records, prescriptions, lab results"},
    {"name": "Nurse", "description": "Access to patients, appointments, basic medical records"},
    {"name": "Receptionist", "description": "Access to patients, appointments, billing"},
    {"name": "Lab Technician", "description": "Access to lab orders, results, and patient info"},
    {"name": "Pharmacist", "description": "Access to prescriptions, pharmacy inventory, dispensing"},
    {"name": "Billing Staff", "description": "Access to billing, invoices, insurance claims"},
]

MEDICAL_PERMISSIONS = [
    # Patients
    ("patients:read", "patients", "View patient records"),
    ("patients:write", "patients", "Create/edit patient records"),
    ("patients:delete", "patients", "Delete patient records"),
    # Appointments
    ("appointments:read", "appointments", "View appointments"),
    ("appointments:write", "appointments", "Create/edit appointments"),
    ("appointments:delete", "appointments", "Cancel/delete appointments"),
    # Medical Records
    ("medical_records:read", "medical_records", "View medical records"),
    ("medical_records:write", "medical_records", "Create/edit medical records"),
    # Prescriptions
    ("prescriptions:read", "prescriptions", "View prescriptions"),
    ("prescriptions:write", "prescriptions", "Create/edit prescriptions"),
    # Lab Results
    ("lab_results:read", "lab_results", "View lab orders and results"),
    ("lab_results:write", "lab_results", "Create/edit lab orders and results"),
    # Billing
    ("billing:read", "billing", "View invoices and payments"),
    ("billing:write", "billing", "Create/edit invoices and payments"),
    ("billing:export", "billing", "Export billing reports"),
    # Pharmacy
    ("pharmacy:read", "pharmacy", "View pharmacy inventory"),
    ("pharmacy:write", "pharmacy", "Manage pharmacy inventory and dispensing"),
    # Users & Roles
    ("users:read", "users", "View user profiles"),
    ("users:write", "users", "Manage users (invite, deactivate)"),
    ("roles:read", "roles", "View roles and permissions"),
    ("roles:write", "roles", "Create/edit roles and permissions"),
    # Invitations
    ("invitations:read", "invitations", "View invitations"),
    ("invitations:write", "invitations", "Send and manage invitations"),
    # Notifications
    ("notifications:read", "notifications", "View notifications"),
    ("notifications:write", "notifications", "Manage notification settings"),
    # AI Integration
    ("ai:read", "ai", "View AI analysis results"),
    ("ai:write", "ai", "Request AI analysis"),
    # Reports
    ("reports:read", "reports", "View reports and analytics"),
    ("reports:export", "reports", "Export reports"),
    # Settings
    ("settings:read", "settings", "View organization settings"),
    ("settings:write", "settings", "Manage organization settings"),
    # Audit
    ("audit:read", "audit", "View audit logs"),
    # Insurance
    ("insurance:read", "insurance", "View insurance claims"),
    ("insurance:write", "insurance", "Manage insurance claims"),
]

# Map each system role to its permission names
ROLE_PERMISSION_MAP = {
    "Admin": [p[0] for p in MEDICAL_PERMISSIONS],  # All permissions
    "Doctor": [
        "patients:read", "patients:write",
        "appointments:read", "appointments:write",
        "medical_records:read", "medical_records:write",
        "prescriptions:read", "prescriptions:write",
        "lab_results:read",
        "pharmacy:read",
        "notifications:read", "notifications:write",
        "ai:read", "ai:write",
        "reports:read",
        "insurance:read",
    ],
    "Nurse": [
        "patients:read", "patients:write",
        "appointments:read", "appointments:write",
        "medical_records:read", "medical_records:write",
        "prescriptions:read",
        "lab_results:read",
        "pharmacy:read",
        "notifications:read", "notifications:write",
    ],
    "Receptionist": [
        "patients:read", "patients:write",
        "appointments:read", "appointments:write", "appointments:delete",
        "billing:read", "billing:write",
        "notifications:read",
        "insurance:read",
    ],
    "Lab Technician": [
        "patients:read",
        "lab_results:read", "lab_results:write",
        "notifications:read", "notifications:write",
        "reports:read",
    ],
    "Pharmacist": [
        "patients:read",
        "prescriptions:read",
        "pharmacy:read", "pharmacy:write",
        "notifications:read", "notifications:write",
    ],
    "Billing Staff": [
        "patients:read",
        "billing:read", "billing:write", "billing:export",
        "insurance:read", "insurance:write",
        "reports:read", "reports:export",
        "notifications:read",
    ],
}


class RBACService:
    """Core RBAC operations."""

    @staticmethod
    def seed_roles_and_permissions():
        """
        Seed system roles and permissions for a new tenant.
        Called during tenant provisioning.

        Admin role gets fixed UUID for deterministic provisioning
        (matches WhiteMatter pattern).
        """
        # Create permissions
        permissions = {}
        for name, resource, description in MEDICAL_PERMISSIONS:
            perm, _ = Permission.objects.get_or_create(
                name=name,
                defaults={"resource": resource, "description": description},
            )
            permissions[name] = perm

        # Create system roles (Admin uses fixed UUID)
        roles = {}
        for role_def in SYSTEM_ROLES:
            defaults = {"description": role_def["description"], "is_system": True}
            if role_def["name"] == "Admin":
                role, _ = Role.objects.get_or_create(
                    id=ADMIN_ROLE_ID,
                    defaults={"name": "Admin", **defaults},
                )
            else:
                role, _ = Role.objects.get_or_create(
                    name=role_def["name"],
                    defaults=defaults,
                )
            roles[role_def["name"]] = role

        # Assign permissions to roles
        for role_name, perm_names in ROLE_PERMISSION_MAP.items():
            role = roles.get(role_name)
            if not role:
                continue
            for perm_name in perm_names:
                perm = permissions.get(perm_name)
                if perm:
                    RolePermission.objects.get_or_create(role=role, permission=perm)

        logger.info("rbac_seeded", roles=len(roles), permissions=len(permissions))
        return roles, permissions

    @staticmethod
    def get_user_permissions(tenant_user: TenantUser) -> set[str]:
        """Get all permission names for a tenant user via their role."""
        return set(
            RolePermission.objects.filter(
                role=tenant_user.role,
                is_deleted=False,
            )
            .select_related("permission")
            .values_list("permission__name", flat=True)
        )

    @staticmethod
    def user_has_permission(tenant_user: TenantUser, permission_name: str) -> bool:
        """Check if a tenant user has a specific permission."""
        return RolePermission.objects.filter(
            role=tenant_user.role,
            permission__name=permission_name,
            is_deleted=False,
        ).exists()

    @staticmethod
    def get_role_permissions(role: Role) -> list[Permission]:
        """Get all permissions for a role."""
        return list(
            Permission.objects.filter(
                role_permissions__role=role,
                role_permissions__is_deleted=False,
                is_deleted=False,
            )
        )


class TenantUserService:
    """Manage tenant users."""

    @staticmethod
    def get_or_create_tenant_user(
        user_id: uuid.UUID,
        email: str,
        role: Role,
        first_name: str = "",
        last_name: str = "",
        **extra_fields,
    ) -> TenantUser:
        """Create a TenantUser profile within the current tenant schema."""
        try:
            return TenantUser.objects.get(user_id=user_id, is_deleted=False)
        except TenantUser.DoesNotExist:
            pass

        # Generate username from email
        username = email.split("@")[0]
        base_username = username
        counter = 1
        while TenantUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        display_name = f"{first_name} {last_name}".strip() or email.split("@")[0]

        tenant_user = TenantUser.objects.create(
            user_id=user_id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            role=role,
            **extra_fields,
        )
        logger.info(
            "tenant_user_created",
            tenant_user_id=str(tenant_user.id),
            email=email,
            role=role.name,
        )
        return tenant_user

    @staticmethod
    def deactivate_user(tenant_user: TenantUser):
        """Deactivate a tenant user."""
        tenant_user.status = TenantUserStatus.INACTIVE
        tenant_user.save(update_fields=["status", "updated_at"])
        logger.info("tenant_user_deactivated", tenant_user_id=str(tenant_user.id))

    @staticmethod
    def change_role(tenant_user: TenantUser, new_role: Role) -> TenantUser:
        """Change a tenant user's role."""
        old_role = tenant_user.role.name
        tenant_user.role = new_role
        tenant_user.save(update_fields=["role", "updated_at"])
        logger.info(
            "tenant_user_role_changed",
            tenant_user_id=str(tenant_user.id),
            old_role=old_role,
            new_role=new_role.name,
        )
        return tenant_user


class InvitationService:
    """Manage user invitations (WhiteMatter pattern)."""

    @staticmethod
    def generate_token(tenant_slug: str) -> str:
        """
        Generate a secure token prefixed with tenant slug.
        Format: {tenant_slug}.{random_token}

        This enables O(1) schema resolution from the token alone
        (WhiteMatter invitation entity pattern).
        """
        raw_token = secrets.token_urlsafe(TOKEN_LENGTH)
        return f"{tenant_slug}.{raw_token}"

    @staticmethod
    def parse_token(composite_token: str) -> tuple[str, str]:
        """
        Parse a composite invitation token into (tenant_slug, full_token).

        The full composite token is stored in DB and used for lookup.
        The tenant_slug prefix enables direct schema resolution
        without a public-schema query.

        Raises ValueError if token format is invalid.
        """
        dot_index = composite_token.find(".")
        if dot_index == -1:
            raise ValueError("Invalid invitation token format")
        tenant_slug = composite_token[:dot_index]
        return tenant_slug, composite_token

    @staticmethod
    def create_invitation(
        email: str,
        role: Role,
        invited_by: TenantUser,
        tenant_slug: str = "",
        metadata: dict | None = None,
    ) -> UserInvitation:
        """
        Create a new invitation. Auto-cancels any existing pending
        invitation for the same email (WhiteMatter pattern).
        """
        # Cancel any existing pending invitation for this email
        UserInvitation.objects.filter(
            email=email,
            status=InvitationStatus.PENDING,
            is_deleted=False,
        ).update(
            status=InvitationStatus.CANCELLED,
            cancelled_at=timezone.now(),
        )

        # Generate token with tenant slug prefix
        if not tenant_slug:
            from django.db import connection
            tenant_slug = connection.schema_name.replace("_", "-")

        token = InvitationService.generate_token(tenant_slug)
        expires_at = timezone.now() + timedelta(days=INVITATION_EXPIRY_DAYS)

        invitation = UserInvitation.objects.create(
            email=email,
            role=role,
            invited_by=invited_by,
            token=token,
            expires_at=expires_at,
            metadata=metadata,
        )
        logger.info(
            "invitation_created",
            invitation_id=str(invitation.id),
            email=email,
            role=role.name,
            expires_in_days=INVITATION_EXPIRY_DAYS,
        )

        # Send invitation email
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            invite_url = f"{getattr(settings, 'INVITATION_BASE_URL', 'http://localhost:3002/invitation')}/{token}"
            send_mail(
                subject=f"You've been invited to join as {role.name}",
                message=(
                    f"Hello,\n\n"
                    f"You have been invited to join as a {role.name}.\n\n"
                    f"Click the link below to accept your invitation:\n"
                    f"{invite_url}\n\n"
                    f"This invitation expires in {INVITATION_EXPIRY_DAYS} days.\n\n"
                    f"If you did not expect this invitation, you can ignore this email."
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@healthsaas.com'),
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info("invitation_email_sent", email=email)
        except Exception as e:
            logger.warning("invitation_email_failed", email=email, error=str(e))

        return invitation

    @staticmethod
    def accept_invitation(token: str, user_id: uuid.UUID) -> TenantUser:
        """
        Accept an invitation by token. Creates the TenantUser.
        Returns the created TenantUser or raises ValueError.
        """
        try:
            invitation = UserInvitation.objects.get(
                token=token,
                status=InvitationStatus.PENDING,
                is_deleted=False,
            )
        except UserInvitation.DoesNotExist:
            raise ValueError("Invalid or expired invitation token.")

        if invitation.expires_at < timezone.now():
            invitation.status = InvitationStatus.EXPIRED
            invitation.save(update_fields=["status", "updated_at"])
            raise ValueError("Invitation has expired.")

        # Create tenant user
        tenant_user = TenantUserService.get_or_create_tenant_user(
            user_id=user_id,
            email=invitation.email,
            role=invitation.role,
        )

        # Mark invitation as accepted
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at", "updated_at"])

        logger.info(
            "invitation_accepted",
            invitation_id=str(invitation.id),
            tenant_user_id=str(tenant_user.id),
        )
        return tenant_user

    @staticmethod
    def cancel_invitation(invitation: UserInvitation):
        """Cancel a pending invitation."""
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Can only cancel pending invitations.")
        invitation.status = InvitationStatus.CANCELLED
        invitation.cancelled_at = timezone.now()
        invitation.save(update_fields=["status", "cancelled_at", "updated_at"])
        logger.info("invitation_cancelled", invitation_id=str(invitation.id))

    @staticmethod
    def expire_stale_invitations() -> int:
        """Mark expired pending invitations. Call from a periodic task."""
        count = UserInvitation.objects.filter(
            status=InvitationStatus.PENDING,
            expires_at__lt=timezone.now(),
            is_deleted=False,
        ).update(status=InvitationStatus.EXPIRED)
        if count:
            logger.info("invitations_expired", count=count)
        return count
