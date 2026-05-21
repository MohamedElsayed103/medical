"""Insurance serializers."""
from rest_framework import serializers

from apps.insurance.models import (
    ClaimDocument,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurance,
)


class InsuranceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProvider
        fields = [
            "id", "name", "code", "contact_email",
            "contact_phone", "address", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PatientInsuranceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = PatientInsurance
        fields = [
            "id", "patient", "provider", "provider_name",
            "policy_number", "group_number",
            "subscriber_name", "subscriber_relationship",
            "effective_date", "expiration_date",
            "is_primary", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClaimDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimDocument
        fields = [
            "id", "file_name", "file_path", "content_type",
            "uploaded_by_id", "description", "created_at",
        ]
        read_only_fields = ["id", "uploaded_by_id", "created_at"]


class InsuranceClaimSerializer(serializers.ModelSerializer):
    documents = ClaimDocumentSerializer(many=True, read_only=True)
    patient_insurance_detail = PatientInsuranceSerializer(
        source="patient_insurance", read_only=True
    )

    class Meta:
        model = InsuranceClaim
        fields = [
            "id", "invoice", "patient_insurance", "patient_insurance_detail",
            "claim_number", "status",
            "submitted_at", "reviewed_at",
            "amount_claimed", "amount_approved",
            "denial_reason", "notes",
            "documents",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "claim_number", "status",
            "submitted_at", "reviewed_at",
            "amount_approved", "denial_reason",
            "created_at", "updated_at",
        ]


class CreateClaimSerializer(serializers.Serializer):
    invoice = serializers.UUIDField()
    patient_insurance = serializers.UUIDField()
    amount_claimed = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, default="")


class ClaimAmountSerializer(serializers.Serializer):
    amount_approved = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )


class DenialReasonSerializer(serializers.Serializer):
    denial_reason = serializers.CharField(required=False, default="")
