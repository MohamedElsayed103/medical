"""
Tenant serializers.
"""
from rest_framework import serializers

from common.enums import OrganizationType

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "license_number",
            "address",
            "phone",
            "email",
            "is_active",
            "subscription_plan",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]


class CreateOrganizationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    type = serializers.ChoiceField(choices=OrganizationType.choices)
    license_number = serializers.CharField(max_length=100, required=False, default="")
    phone = serializers.CharField(max_length=20, required=False, default="")
    email = serializers.EmailField(required=False, default="")
    address = serializers.CharField(required=False, default="")
    domain_url = serializers.CharField(max_length=253, required=False, default="")
