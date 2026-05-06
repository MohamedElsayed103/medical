"""
Shared validators for serializer and model fields.
"""
import re

from django.core.exceptions import ValidationError


def validate_phone(value: str) -> str:
    """Validates phone numbers: must be digits, optional leading +, 7-20 chars."""
    pattern = r"^\+?\d{7,20}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "Enter a valid phone number (7-20 digits, optional leading +)."
        )
    return value


def validate_file_size(max_mb: int = 10):
    """Returns a validator function that enforces a max file size."""

    def _validator(value):
        limit = max_mb * 1024 * 1024
        if value.size > limit:
            raise ValidationError(f"File size must not exceed {max_mb} MB.")

    return _validator


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def validate_medical_file_type(value):
    """Ensures uploaded medical files are safe image types or PDF."""
    if hasattr(value, "content_type") and value.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported file type '{value.content_type}'. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
