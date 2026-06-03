"""
RBAC serializers for roles, permissions, tenant users, and invitations.
"""
from rest_framework import serializers

from .models import (
    Permission,
    Role,
    RolePermission,
    TenantUser,
    UserInvitation,
)


# ── Permission ─────────────────────────────────────────────────────


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "resource", "description"]
        read_only_fields = ["id"]


# ── Role ───────────────────────────────────────────────────────────


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id", "name", "description", "is_system",
            "permissions", "user_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_permissions(self, obj):
        perms = Permission.objects.filter(
            role_permissions__role=obj,
            role_permissions__is_deleted=False,
            is_deleted=False,
        )
        return PermissionSerializer(perms, many=True).data

    def get_user_count(self, obj):
        return obj.users.filter(is_deleted=False).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=[],
    )

    class Meta:
        model = Role
        fields = ["name", "description", "permission_ids"]

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", [])
        role = Role.objects.create(**validated_data)

        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids, is_deleted=False)
            for perm in permissions:
                RolePermission.objects.create(role=role, permission=perm)

        return role


class RoleUpdateSerializer(serializers.ModelSerializer):
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name", "description", "permission_ids"]

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)

        if instance.is_system:
            # System roles can only have permissions changed, not name/description
            validated_data.pop("name", None)
            validated_data.pop("description", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if permission_ids is not None:
            # Replace all permissions
            RolePermission.objects.filter(role=instance).delete()
            permissions = Permission.objects.filter(id__in=permission_ids, is_deleted=False)
            for perm in permissions:
                RolePermission.objects.create(role=instance, permission=perm)

        return instance


# ── TenantUser ─────────────────────────────────────────────────────


class TenantUserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = TenantUser
        fields = [
            "id", "user_id", "email", "username",
            "first_name", "last_name", "display_name",
            "role", "role_name", "permissions",
            "specialty", "license_number", "qualification",
            "status", "locale",
            "notification_preferences", "dashboard_configurations",
            "mfa_enabled", "mfa_configured_at",
            "last_login", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "user_id", "email", "username",
            "created_at", "updated_at", "last_login",
        ]

    def get_permissions(self, obj):
        from .services import RBACService
        return sorted(RBACService.get_user_permissions(obj))


class TenantUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantUser
        fields = [
            "first_name", "last_name", "display_name",
            "role", "specialty", "license_number", "qualification",
            "status", "locale", "notification_preferences",
            "dashboard_configurations",
        ]


class TenantUserProfileSerializer(serializers.ModelSerializer):
    """For the current user to view/edit their own profile."""
    role_name = serializers.CharField(source="role.name", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = TenantUser
        fields = [
            "id", "user_id", "email", "username",
            "first_name", "last_name", "display_name",
            "role", "role_name", "permissions",
            "specialty", "license_number", "qualification",
            "status", "locale",
            "notification_preferences", "dashboard_configurations",
            "mfa_enabled",
            "last_login", "created_at",
        ]
        read_only_fields = [
            "id", "user_id", "email", "username", "role",
            "status", "created_at", "last_login",
        ]

    def get_permissions(self, obj):
        from .services import RBACService
        return sorted(RBACService.get_user_permissions(obj))


# ── UserInvitation ─────────────────────────────────────────────────


class UserInvitationSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    invited_by_name = serializers.CharField(
        source="invited_by.display_name", read_only=True
    )
    invite_url = serializers.SerializerMethodField()

    class Meta:
        model = UserInvitation
        fields = [
            "id", "email", "role", "role_name",
            "invited_by", "invited_by_name",
            "token", "expires_at", "status",
            "accepted_at", "cancelled_at", "metadata",
            "created_at", "invite_url",
        ]
        read_only_fields = [
            "id", "invited_by", "token", "expires_at",
            "status", "accepted_at", "cancelled_at", "created_at",
        ]

    def get_invite_url(self, obj):
        from django.conf import settings
        base = getattr(settings, 'INVITATION_BASE_URL', 'http://localhost:3002/invitation')
        return f"{base}/{obj.token}"


class CreateInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.UUIDField()
    metadata = serializers.JSONField(required=False, default=None)

    def validate_email(self, value):
        # Check if user already exists in this tenant
        if TenantUser.objects.filter(email=value, is_deleted=False).exists():
            raise serializers.ValidationError(
                "A user with this email already exists in this organization."
            )
        return value

    def validate_role_id(self, value):
        try:
            Role.objects.get(id=value, is_deleted=False)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Role not found.")
        return value


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
