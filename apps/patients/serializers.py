"""
Patient serializers.
"""
from rest_framework import serializers

from common.utils import decrypt_field, encrypt_field

from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    national_id = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "medical_record_number",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "national_id",
            "blood_type",
            "phone",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "allergies",
            "chronic_conditions",
            "insurance_provider",
            "insurance_number",
            "notes",
            "is_active",
            "registered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "medical_record_number",
            "is_active",
            "registered_at",
            "created_at",
            "updated_at",
        ]

    def get_national_id(self, obj) -> str:
        """Decrypt national_id for authorized readers."""
        if obj.national_id_encrypted:
            return decrypt_field(obj.national_id_encrypted)
        return ""


class PatientCreateSerializer(serializers.Serializer):
    """Explicit create serializer — decoupled from model to control input."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    date_of_birth = serializers.DateField()
    gender = serializers.CharField(max_length=10)
    phone = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=50, required=False, default="")
    blood_type = serializers.CharField(max_length=5, required=False, default="")
    email = serializers.EmailField(required=False, default="")
    address = serializers.CharField(required=False, default="")
    emergency_contact_name = serializers.CharField(max_length=255, required=False, default="")
    emergency_contact_phone = serializers.CharField(max_length=20, required=False, default="")
    allergies = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    chronic_conditions = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    insurance_provider = serializers.CharField(max_length=200, required=False, default="")
    insurance_number = serializers.CharField(max_length=100, required=False, default="")
    notes = serializers.CharField(required=False, default="")


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints (no sensitive fields)."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "medical_record_number",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "phone",
            "is_active",
            "registered_at",
        ]
