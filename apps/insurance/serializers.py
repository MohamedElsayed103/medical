"""Insurance serializers."""
from rest_framework import serializers

from apps.insurance.models import (
    ClaimDocument,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurance,
)


class InsuranceProviderSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = InsuranceProvider
        fields = [
            "id", "name", "code", "contact_email",
            "contact_phone", "address", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        if not value:
            # Auto-generate code from name
            import uuid
            name = self.initial_data.get("name", "")
            base = name.upper().replace(" ", "_")[:20] if name else "PROV"
            value = f"{base}_{uuid.uuid4().hex[:6].upper()}"
        return value


class PatientInsuranceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    # Accept frontend field aliases
    start_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    end_date = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = PatientInsurance
        fields = [
            "id", "patient", "provider", "provider_name",
            "policy_number", "group_number",
            "subscriber_name", "subscriber_relationship",
            "effective_date", "expiration_date",
            "is_primary", "is_active",
            "start_date", "end_date",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "effective_date": {"required": False},
            "expiration_date": {"required": False, "allow_null": True},
            "group_number": {"required": False, "allow_blank": True},
            "subscriber_name": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        # Map start_date/end_date to effective_date/expiration_date
        if "start_date" in attrs:
            if attrs["start_date"]:
                attrs["effective_date"] = attrs.pop("start_date")
            else:
                attrs.pop("start_date")
        if "end_date" in attrs:
            if attrs["end_date"]:
                attrs["expiration_date"] = attrs.pop("end_date")
            else:
                attrs.pop("end_date")
        # Default effective_date to today if not provided
        if not attrs.get("effective_date"):
            from django.utils import timezone
            attrs["effective_date"] = timezone.now().date()
        return attrs


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
    invoice = serializers.UUIDField(required=False, allow_null=True)
    patient_insurance = serializers.UUIDField(required=False, allow_null=True)
    # Frontend aliases
    policy = serializers.UUIDField(required=False, allow_null=True)
    amount_claimed = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    notes = serializers.CharField(required=False, default="", allow_blank=True)
    diagnosis = serializers.CharField(required=False, default="", allow_blank=True)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    service_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        # Map frontend aliases
        if not attrs.get("patient_insurance") and attrs.get("policy"):
            attrs["patient_insurance"] = attrs.pop("policy")
        else:
            attrs.pop("policy", None)
        if not attrs.get("amount_claimed") and attrs.get("amount"):
            attrs["amount_claimed"] = attrs.pop("amount")
        else:
            attrs.pop("amount", None)
        # Build notes from diagnosis/description
        parts = []
        if attrs.get("diagnosis"):
            parts.append(f"Diagnosis: {attrs.pop('diagnosis')}")
        else:
            attrs.pop("diagnosis", None)
        if attrs.get("description"):
            parts.append(attrs.pop("description"))
        else:
            attrs.pop("description", None)
        if parts and not attrs.get("notes"):
            attrs["notes"] = "\n".join(parts)
        attrs.pop("service_date", None)

        if not attrs.get("patient_insurance"):
            raise serializers.ValidationError({"patient_insurance": "This field is required."})
        if not attrs.get("amount_claimed"):
            raise serializers.ValidationError({"amount_claimed": "This field is required."})
        return attrs


class ClaimAmountSerializer(serializers.Serializer):
    amount_approved = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )


class DenialReasonSerializer(serializers.Serializer):
    denial_reason = serializers.CharField(required=False, default="")
