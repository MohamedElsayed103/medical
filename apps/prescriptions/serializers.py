"""
Prescription serializers.
"""
from rest_framework import serializers

from .models import Medication, Prescription, PrescriptionItem


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "name", "generic_name", "form", "strength", "manufacturer", "is_active"]
        read_only_fields = ["id"]


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medication",
            "medication_name",
            "dosage",
            "frequency",
            "duration",
            "route",
            "quantity",
            "instructions",
            "is_prn",
        ]
        read_only_fields = ["id"]


class PrescriptionItemInputSerializer(serializers.Serializer):
    medication_id = serializers.UUIDField()
    dosage = serializers.CharField(max_length=100)
    frequency = serializers.CharField(max_length=100)
    duration = serializers.CharField(max_length=100)
    route = serializers.CharField(max_length=20, default="oral")
    quantity = serializers.IntegerField(min_value=1)
    instructions = serializers.CharField(required=False, default="")
    is_prn = serializers.BooleanField(default=False)


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "visit",
            "patient",
            "patient_name",
            "doctor",
            "prescribed_at",
            "notes",
            "is_dispensed",
            "dispensed_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "prescribed_at",
            "is_dispensed",
            "dispensed_at",
            "created_at",
            "updated_at",
        ]


class PrescriptionCreateSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    doctor_id = serializers.UUIDField()
    visit_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, default="")
    items = PrescriptionItemInputSerializer(many=True, min_length=1)


class PrescriptionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "prescribed_at",
            "is_dispensed",
            "item_count",
        ]
