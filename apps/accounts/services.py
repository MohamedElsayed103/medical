"""
Accounts service layer — business logic for user/membership management.
"""
import structlog
from django.utils import timezone

from common.utils import encrypt_field, generate_api_key, hash_pin

from .models import TenantMembership, User, UserSecrets

logger = structlog.get_logger(__name__)


class AccountService:
    """User and membership operations."""

    @staticmethod
    def get_user_memberships(user: User) -> list[TenantMembership]:
        return list(
            TenantMembership.objects.filter(user=user, is_active=True)
            .select_related("tenant")
            .order_by("joined_at")
        )

    @staticmethod
    def add_member(tenant, user: User, role: str) -> TenantMembership:
        membership, created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": role},
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.role = role
            membership.save(update_fields=["is_active", "role"])
        logger.info(
            "member_added",
            tenant_id=str(tenant.id),
            user_id=str(user.id),
            role=role,
            created=created,
        )
        return membership

    @staticmethod
    def remove_member(membership: TenantMembership):
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        logger.info("member_removed", membership_id=str(membership.id))

    @staticmethod
    def update_role(membership: TenantMembership, new_role: str) -> TenantMembership:
        old_role = membership.role
        membership.role = new_role
        membership.save(update_fields=["role"])
        logger.info(
            "role_updated",
            membership_id=str(membership.id),
            old_role=old_role,
            new_role=new_role,
        )
        return membership


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
        secrets.save(update_fields=["pin_hash", "updated_at"])

    @staticmethod
    def generate_api_key(user: User) -> str:
        """Generate a new API key. Returns the raw key (shown once)."""
        secrets = UserSecretsService.get_or_create_secrets(user)
        raw_key, hashed_key = generate_api_key()
        secrets.api_key_hash = hashed_key
        secrets.last_rotated_at = timezone.now()
        secrets.save(update_fields=["api_key_hash", "last_rotated_at", "updated_at"])
        logger.info("api_key_generated", user_id=str(user.id))
        return raw_key

    @staticmethod
    def store_refresh_token(user: User, refresh_token: str) -> None:
        secrets = UserSecretsService.get_or_create_secrets(user)
        secrets.refresh_token_encrypted = encrypt_field(refresh_token)
        secrets.save(update_fields=["refresh_token_encrypted", "updated_at"])
