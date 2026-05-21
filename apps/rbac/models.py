"""
RBAC models — tenant schema.

These models live in tenant schemas (not public). Each tenant has its own
set of roles, permissions, users, and invitations — matching the WhiteMatter
architecture adapted for a medical platform.

Architecture:
    Role              Named role within a tenant (Admin, Doctor, Nurse, etc.)
    Permission        Resource-action pair ("patients:read", "prescriptions:write")
    RolePermission    M2M linking roles to permissions
    TenantUser        Per-tenant user profile linked to the public User identity
    UserInvitation    Token-based invitation flow for onboarding users
"""
import uuid

from django.conf import settings
from django.db import models


# ── Enums ──────────────────────────────────────────────────────────


class TenantUserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


class SecretStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"


# ── Abstract soft-delete mixin ─────────────────────────────────────


class SoftDeleteModel(models.Model):
    """Mixin providing soft-delete fields (WhiteMatter pattern)."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


# ── Role ───────────────────────────────────────────────────────────


class Role(SoftDeleteModel):
    """
    A named role within a tenant. System roles (is_system=True) are
    seeded on tenant creation and cannot be deleted.

    Examples: Admin, Doctor, Nurse, Receptionist, Lab Technician,
    Pharmacist, Billing Staff
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        ordering = ["-is_system", "name"]

    def __str__(self):
        return self.name


# ── Permission ─────────────────────────────────────────────────────


class Permission(SoftDeleteModel):
    """
    A resource-action permission.

    Convention: name = "resource:action"
    Examples: "patients:read", "prescriptions:write", "billing:export"
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    resource = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permissions"
        ordering = ["resource", "name"]

    def __str__(self):
        return self.name


# ── RolePermission ─────────────────────────────────────────────────


class RolePermission(SoftDeleteModel):
    """M2M mapping: which permissions a role grants."""

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role_permissions"
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name} → {self.permission.name}"


# ── TenantUser ─────────────────────────────────────────────────────


class TenantUser(SoftDeleteModel):
    """
    Per-tenant user profile. Links a public-schema User identity to a
    tenant with a role and medical-specific profile data.

    The `user_id` is a UUID referencing the public User.id — not a real
    FK because Django-tenants disallows cross-schema foreign keys.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True, help_text="FK to public schema accounts_user.id")
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True, default="")

    # Keycloak integration
    keycloak_subject_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True,
        help_text="Keycloak sub claim for this user in this tenant's realm",
    )

    # Role
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name="users",
    )

    # Medical professional fields
    specialty = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Medical specialty (e.g., Cardiology, Pediatrics, General Practice)",
    )
    license_number = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Professional medical license number",
    )
    qualification = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Professional qualification (MD, RN, PharmD, etc.)",
    )

    # Status & preferences
    status = models.CharField(
        max_length=20,
        choices=TenantUserStatus.choices,
        default=TenantUserStatus.ACTIVE,
        db_index=True,
    )
    locale = models.CharField(max_length=5, default="en")
    notification_preferences = models.JSONField(default=dict, blank=True)
    dashboard_configurations = models.JSONField(default=list, blank=True)

    # MFA
    mfa_enabled = models.BooleanField(default=False)
    mfa_configured_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["status"], name="idx_users_status"),
            models.Index(fields=["role"], name="idx_users_role_id"),
        ]

    def __str__(self):
        return f"{self.display_name or self.email} ({self.role.name})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.display_name


# ── UserInvitation ─────────────────────────────────────────────────


class UserInvitation(SoftDeleteModel):
    """
    Token-based invitation to join a tenant with a specific role.

    Flow:
        1. Admin creates invitation → token generated, status=PENDING
        2. Email sent with link containing token
        3. Invitee accepts → status=ACCEPTED, TenantUser created
        4. Token expires after `expires_at` → status=EXPIRED (via cron/check)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        TenantUser,
        on_delete=models.RESTRICT,
        related_name="sent_invitations",
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_invitations"
        indexes = [
            models.Index(
                fields=["email"],
                condition=models.Q(is_deleted=False),
                name="idx_invitations_email_active",
            ),
            models.Index(
                fields=["status"],
                condition=models.Q(is_deleted=False),
                name="idx_invitations_status_active",
            ),
            models.Index(
                fields=["expires_at"],
                condition=models.Q(status="PENDING", is_deleted=False),
                name="idx_invitations_pending_expiry",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(status="PENDING", is_deleted=False),
                name="uq_invitations_pending_email",
            ),
        ]

    def __str__(self):
        return f"Invitation: {self.email} → {self.role.name} ({self.status})"
