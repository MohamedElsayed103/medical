"""Referrals serializers."""
from rest_framework import serializers

from apps.referrals.models import (
    FacilityConnection,
    Referral,
    ReferralNote,
)


# ── Connections ────────────────────────────────────────────────────
class FacilityConnectionSerializer(serializers.ModelSerializer):
    from_tenant_name = serializers.CharField(source="from_tenant.name", read_only=True)
    to_tenant_name = serializers.CharField(source="to_tenant.name", read_only=True)

    class Meta:
        model = FacilityConnection
        fields = [
            "id",
            "from_tenant",
            "from_tenant_name",
            "to_tenant",
            "to_tenant_name",
            "status",
            "established_at",
            "data_sharing_agreement",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "established_at", "created_at", "updated_at"]


class ConnectionRequestSerializer(serializers.Serializer):
    to_tenant = serializers.UUIDField()
    notes = serializers.CharField(required=False, default="")


# ── Referral ───────────────────────────────────────────────────────
class ReferralNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralNote
        fields = ["id", "author_id", "author_tenant", "content", "created_at"]
        read_only_fields = ["id", "author_id", "author_tenant", "created_at"]


class ReferralSerializer(serializers.ModelSerializer):
    notes = ReferralNoteSerializer(many=True, read_only=True)
    from_tenant_name = serializers.CharField(source="from_tenant.name", read_only=True)
    to_tenant_name = serializers.CharField(source="to_tenant.name", read_only=True)

    class Meta:
        model = Referral
        fields = [
            "id",
            "from_tenant",
            "from_tenant_name",
            "to_tenant",
            "to_tenant_name",
            "referring_doctor_id",
            "patient_summary",
            "reason",
            "priority",
            "status",
            "clinical_notes",
            "accepted_by_id",
            "accepted_at",
            "completed_at",
            "decline_reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_tenant",
            "referring_doctor_id",
            "status",
            "accepted_by_id",
            "accepted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class CreateReferralSerializer(serializers.Serializer):
    to_tenant = serializers.UUIDField()
    patient_summary = serializers.JSONField()
    reason = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=["routine", "urgent", "stat"], default="routine"
    )
    clinical_notes = serializers.CharField(required=False, default="")


class DeclineReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="")


class NoteInputSerializer(serializers.Serializer):
    content = serializers.CharField()
