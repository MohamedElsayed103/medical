"""
Radiology serializers.
"""
from rest_framework import serializers
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport


class RadiologyStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyStudy
        fields = ["id", "modality", "body_part", "description", "performed_by_id", "performed_at"]


class RadiologyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyReport
        fields = ["id", "findings", "impression", "is_critical", "reported_by_id", "reported_at", "image_object_key"]


class RadiologyStudyWithReportSerializer(RadiologyStudySerializer):
    report = RadiologyReportSerializer(read_only=True)

    class Meta(RadiologyStudySerializer.Meta):
        fields = RadiologyStudySerializer.Meta.fields + ["report"]


class RadiologyOrderSerializer(serializers.ModelSerializer):
    studies = RadiologyStudyWithReportSerializer(many=True, read_only=True)
    orderer_name = serializers.CharField(read_only=True)
    orderer_type = serializers.CharField(read_only=True)

    class Meta:
        model = RadiologyOrder
        fields = [
            "id", "order_number", "status", "priority",
            "patient_id", "customer_id", "doctor_id", "visit_id",
            "orderer_name", "orderer_type",
            "clinical_notes", "invoice_id",
            "ordered_at", "completed_at",
            "studies",
        ]


class CreateRadiologyOrderSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    doctor_id = serializers.UUIDField(required=False, allow_null=True)
    visit_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.CharField(required=False, default="routine")
    clinical_notes = serializers.CharField(required=False, allow_blank=True, default="")
    studies = serializers.ListField(child=serializers.DictField(), min_length=1)


class TransitionStatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class RecordReportSerializer(serializers.Serializer):
    study_id = serializers.UUIDField()
    findings = serializers.CharField()
    impression = serializers.CharField(required=False, allow_blank=True, default="")
    is_critical = serializers.BooleanField(required=False, default=False)
    image_object_key = serializers.CharField(required=False, allow_blank=True, default="")
