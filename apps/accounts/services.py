"""
Accounts service layer — platform-level user identity management.

Tenant-level user management (roles, permissions, invitations) lives in
apps.rbac.services.
"""
import structlog
from django.utils import timezone

from common.utils import encrypt_field, generate_api_key, hash_pin

from .models import User, UserSecrets, UserTenantMapping

logger = structlog.get_logger(__name__)


class AccountService:
    """Platform-level user operations."""

    @staticmethod
    def get_user_tenant_mappings(user: User) -> list[UserTenantMapping]:
        """Get all tenant mappings for a user."""
        return list(
            UserTenantMapping.objects.filter(user=user, is_deleted=False)
            .select_related("tenant")
            .order_by("created_at")
        )

    @staticmethod
    def add_tenant_mapping(
        user: User,
        tenant,
        email: str | None = None,
        username: str | None = None,
        keycloak_subject_id: str | None = None,
    ) -> UserTenantMapping:
        """Add a user-tenant mapping (called when user joins a tenant)."""
        email = email or user.email
        username = username or user.username or email.split("@")[0]

        mapping, created = UserTenantMapping.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={
                "email": email,
                "username": username,
                "keycloak_subject_id": keycloak_subject_id,
            },
        )
        if not created and mapping.is_deleted:
            mapping.is_deleted = False
            mapping.deleted_at = None
            mapping.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

        logger.info(
            "tenant_mapping_added",
            user_id=str(user.id),
            tenant_id=str(tenant.id),
            created=created,
        )
        return mapping

    @staticmethod
    def remove_tenant_mapping(mapping: UserTenantMapping):
        """Soft-delete a user-tenant mapping."""
        mapping.is_deleted = True
        mapping.deleted_at = timezone.now()
        mapping.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
        logger.info("tenant_mapping_removed", mapping_id=str(mapping.id))


class UserSecretsService:
    """Manage application-level secrets for a user."""

    @staticmethod
    def get_or_create_secrets(user: User) -> UserSecrets:
        secrets, _ = UserSecrets.objects.get_or_create(user=user)
        return secrets

    @staticmethod
    def set_pin(user: User, pin: str) -> None:
        secrets = UserSecretsService.get_or_create_secrets(user)
        secrets.pin_hash = hash_pin(pin)
        secrets.status = "active"
        secrets.save(update_fields=["pin_hash", "status", "updated_at"])

    @staticmethod
    def generate_api_key(user: User) -> str:
        """Generate a new API key. Returns the raw key (shown once)."""
        secrets = UserSecretsService.get_or_create_secrets(user)
        raw_key, hashed_key = generate_api_key()
        secrets.api_key_hash = hashed_key
        secrets.status = "active"
        secrets.last_rotated_at = timezone.now()
        secrets.save(update_fields=["api_key_hash", "status", "last_rotated_at", "updated_at"])
        logger.info("api_key_generated", user_id=str(user.id))
        return raw_key

    @staticmethod
    def revoke_secrets(user: User) -> None:
        """Revoke all secrets for a user."""
        try:
            secrets = user.secrets
            secrets.status = "revoked"
            secrets.api_key_hash = None
            secrets.pin_hash = None
            secrets.save(update_fields=["status", "api_key_hash", "pin_hash", "updated_at"])
            logger.info("secrets_revoked", user_id=str(user.id))
        except UserSecrets.DoesNotExist:
            pass
