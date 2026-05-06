"""
Medical records serializers.
"""
from rest_framework import serializers

from .models import Diagnosis, Visit, Vitals


class VitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vitals
        fields = [
            "id",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "temperature",
            "respiratory_rate",
            "oxygen_saturation",
            "weight_kg",
            "height_cm",
            "recorded_at",
            "recorded_by_id",
        ]
        read_only_fields = ["id", "recorded_at", "recorded_by_id"]


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ["id", "icd_code", "description", "type", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class VisitSerializer(serializers.ModelSerializer):
    vitals = VitalsSerializer(many=True, read_only=True)
    diagnoses = DiagnosisSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id",
            "appointment",
            "patient",
            "patient_name",
            "doctor",
            "visit_date",
            "chief_complaint",
            "history_of_present_illness",
            "examination_notes",
            "assessment",
            "plan",
            "follow_up_date",
            "is_signed",
            "signed_at",
            "vitals",
            "diagnoses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_signed", "signed_at", "created_at", "updated_at"]


class VisitCreateSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    doctor_id = serializers.UUIDField()
    appointment_id = serializers.UUIDField(required=False, allow_null=True)
    visit_date = serializers.DateTimeField()
    chief_complaint = serializers.CharField()
    history_of_present_illness = serializers.CharField(required=False, default="")
    examination_notes = serializers.CharField(required=False, default="")
    assessment = serializers.CharField(required=False, default="")
    plan = serializers.CharField(required=False, default="")
    follow_up_date = serializers.DateField(required=False, allow_null=True)


class VisitListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "visit_date",
            "chief_complaint",
            "is_signed",
            "created_at",
        ]
