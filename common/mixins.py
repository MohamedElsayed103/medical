"""
Reusable serializer and viewset mixins.
"""
from rest_framework import serializers


class TimestampMixin(serializers.Serializer):
    """Read-only timestamp fields for any serializer."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SoftDeleteMixin(serializers.Serializer):
    """Adds soft-delete awareness to serializers."""

    is_active = serializers.BooleanField(read_only=True)
