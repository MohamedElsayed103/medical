"""
Accounts models — public schema.

User            Custom user model, linked to Keycloak via keycloak_id.
UserSecrets     Application-level secrets (API keys, PINs, encrypted tokens).
TenantMembership  Maps a user to an organization with a specific role.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from common.enums import UserRole

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.

    Authentication is handled by Keycloak (OIDC).  Django stores identity
    data and maps to Keycloak via ``keycloak_id`` (the OIDC *sub* claim).
    Passwords are set as unusable by default — Keycloak owns credential mgmt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keycloak_id = models.UUIDField(unique=True, null=True, blank=True, db_index=True)
    email = models.EmailField("email address", unique=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    national_id_encrypted = models.TextField(
        blank=True,
        default="",
        help_text="Fernet-encrypted national ID.",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class UserSecrets(models.Model):
    """
    Application-level secrets — NOT Keycloak credentials.

    * api_key_hash: for service-to-service auth (non-OIDC callers).
    * pin_hash: quick-access clinical PIN for sensitive confirmations.
    * refresh_token_encrypted: for Celery tasks acting on behalf of user.
    * mfa_backup_codes_encrypted: MFA recovery codes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="secrets")
    api_key_hash = models.CharField(max_length=128, null=True, blank=True)
    refresh_token_encrypted = models.TextField(null=True, blank=True)
    mfa_backup_codes_encrypted = models.TextField(null=True, blank=True)
    pin_hash = models.CharField(max_length=128, null=True, blank=True)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user_secrets"
        verbose_name = "user secrets"
        verbose_name_plural = "user secrets"

    def __str__(self):
        return f"Secrets for {self.user.email}"


class TenantMembership(models.Model):
    """
    Maps a user to an organization (tenant) with a single role.

    A user may belong to multiple tenants (e.g., a doctor working at
    two clinics), each with a different role.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=UserRole.choices)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_tenant_membership"
        unique_together = ("user", "tenant")
        verbose_name = "tenant membership"
        verbose_name_plural = "tenant memberships"

    def __str__(self):
        return f"{self.user.email} → {self.tenant} ({self.role})"
