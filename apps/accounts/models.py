"""
Accounts models — public schema.

User                Custom user model, linked to Keycloak via keycloak_id.
UserSecrets         Application-level secrets (WhiteMatter pattern).
UserTenantMapping   Lightweight mapping of user identity → tenant (public schema).

NOTE: Role-based access control (roles, permissions, tenant user profiles,
invitations) lives in the ``apps.rbac`` app within tenant schemas.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Platform-level user identity (public schema).

    Authentication is handled by Keycloak (OIDC). Django stores identity
    data and maps to Keycloak via ``keycloak_id`` (the OIDC *sub* claim).
    Passwords are set as unusable by default — Keycloak owns credential mgmt.

    This is analogous to WhiteMatter's ``superadmins`` + ``user_tenant_mapping``
    combined — the single source of identity across all tenants.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keycloak_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True, db_index=True,
        help_text="Keycloak subject (sub claim)",
    )
    email = models.EmailField("email address", unique=True)
    username = models.CharField(
        max_length=50, unique=True, null=True, blank=True,
        help_text="Optional username (auto-generated from email if blank)",
    )
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True, default="")
    national_id_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Fernet-encrypted national ID.",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Platform admin flag (equivalent to WhiteMatter superadmin).",
    )
    last_login = models.DateTimeField(null=True, blank=True)

    # Soft delete (WhiteMatter pattern)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["is_deleted"], name="idx_user_is_deleted"),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.display_name

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])


class UserSecrets(models.Model):
    """
    Application-level secrets (WhiteMatter pattern).

    Each user has at most one active secret. Status tracks lifecycle:
    pending → active → revoked.

    Also stores optional API key hash and clinical PIN for the medical
    platform's specific needs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="secrets")
    secret = models.TextField(
        blank=True, default="",
        help_text="Application secret (e.g., TOTP seed, recovery codes encrypted)",
    )
    status = models.CharField(
        max_length=20, default="pending",
        choices=[("pending", "Pending"), ("active", "Active"), ("revoked", "Revoked")],
    )
    api_key_hash = models.CharField(max_length=128, null=True, blank=True)
    pin_hash = models.CharField(max_length=128, null=True, blank=True)
    last_rotated_at = models.DateTimeField(null=True, blank=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user_secrets"
        verbose_name = "user secrets"
        verbose_name_plural = "user secrets"
        indexes = [
            models.Index(fields=["user"], name="idx_user_secrets_user_id"),
        ]

    def __str__(self):
        return f"Secrets for {self.user.email} ({self.status})"


class UserTenantMapping(models.Model):
    """
    Lightweight mapping of a user identity to a tenant (public schema).

    This is the WhiteMatter ``user_tenant_mapping`` equivalent — it records
    which tenants a user belongs to at the platform level. The detailed
    profile (role, permissions, etc.) lives in the tenant schema's
    ``rbac_tenant_users`` table.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tenant_mappings")
    tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="user_mappings",
    )
    email = models.EmailField(help_text="Email used for this tenant (may differ from primary)")
    username = models.CharField(max_length=50)
    keycloak_subject_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True,
        help_text="Keycloak sub for this user in this tenant's realm",
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user_tenant_mapping"
        unique_together = ("user", "tenant")
        verbose_name = "user-tenant mapping"
        verbose_name_plural = "user-tenant mappings"
        indexes = [
            models.Index(fields=["email"], name="idx_utm_email"),
            models.Index(fields=["keycloak_subject_id"], name="idx_utm_keycloak_subject"),
            models.Index(fields=["is_deleted"], name="idx_utm_is_deleted"),
        ]

    def __str__(self):
        return f"{self.email} → {self.tenant.name}"
