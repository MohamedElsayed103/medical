"""
Accounts serializers — platform-level user identity.
"""
from rest_framework import serializers

from .models import User, UserTenantMapping


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "phone",
            "first_name",
            "last_name",
            "display_name",
            "full_name",
            "is_active",
            "last_login",
            "created_at",
        ]
        read_only_fields = ["id", "email", "is_active", "created_at", "last_login"]


class UserTenantMappingSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)

    class Meta:
        model = UserTenantMapping
        fields = [
            "id",
            "user",
            "tenant",
            "tenant_name",
            "tenant_slug",
            "email",
            "username",
            "keycloak_subject_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MeSerializer(serializers.ModelSerializer):
    """Current user profile with tenant mappings."""
    tenant_mappings = UserTenantMappingSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "phone",
            "first_name",
            "last_name",
            "display_name",
            "is_active",
            "created_at",
            "tenant_mappings",
        ]
        read_only_fields = ["id", "email", "is_active", "created_at"]


class VerifyPinSerializer(serializers.Serializer):
    pin = serializers.CharField(min_length=4, max_length=6)
