"""
Accounts serializers.
"""
from rest_framework import serializers

from common.enums import UserRole

from .models import TenantMembership, User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "is_active", "date_joined", "last_login"]


class TenantMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = TenantMembership
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "tenant",
            "tenant_name",
            "role",
            "is_active",
            "joined_at",
        ]
        read_only_fields = ["id", "joined_at"]


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices)


class VerifyPinSerializer(serializers.Serializer):
    pin = serializers.CharField(min_length=4, max_length=6)


class MeSerializer(serializers.ModelSerializer):
    memberships = TenantMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "memberships",
        ]
