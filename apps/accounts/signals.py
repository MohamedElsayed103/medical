"""
Post-save/login signals for account lifecycle events.
"""
import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserSecrets

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=User)
def create_user_secrets(sender, instance, created, **kwargs):
    """Auto-create a UserSecrets row for every new user."""
    if created:
        UserSecrets.objects.create(user=instance)
        logger.info("user_secrets_created", user_id=str(instance.id))
