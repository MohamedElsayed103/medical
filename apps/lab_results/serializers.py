"""
Lab serializers.
"""
from rest_framework import serializers

from .models import LabOrder, LabTest, TestResult


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = [
            "id",
            "value",
            "unit",
            "reference_range_low",
            "reference_range_high",
            "flag",
            "resulted_at",
            "interpretation",
        ]
        read_only_fields = ["id", "flag", "resulted_at"]


class TestResultInputSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=200)
    unit = serializers.CharField(max_length=50, required=False, default="")
    reference_range_low = serializers.DecimalField(
        max_digits=10, decimal_places=3, required=False, allow_null=True
    )
    reference_range_high = serializers.DecimalField(
        max_digits=10, decimal_places=3, required=False, allow_null=True
    )
    interpretation = serializers.CharField(required=False, default="")


class LabTestSerializer(serializers.ModelSerializer):
    result = TestResultSerializer(read_only=True)

    class Meta:
        model = LabTest
        fields = ["id", "test_name", "test_code", "specimen_type", "notes", "result"]
        read_only_fields = ["id"]


class LabTestInputSerializer(serializers.Serializer):
    test_name = serializers.CharField(max_length=200)
    test_code = serializers.CharField(max_length=50, required=False, default="")
    specimen_type = serializers.CharField(max_length=100, required=False, default="")
    notes = serializers.CharField(required=False, default="")


class LabOrderSerializer(serializers.ModelSerializer):
    tests = LabTestSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = LabOrder
        fields = [
            "id",
            "order_number",
            "patient",
            "patient_name",
            "doctor",
            "visit",
            "status",
            "priority",
            "clinical_notes",
            "ordered_at",
            "completed_at",
            "tests",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "status",
            "ordered_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class LabOrderCreateSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    doctor_id = serializers.UUIDField()
    visit_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.CharField(max_length=10, default="routine")
    clinical_notes = serializers.CharField(required=False, default="")
    tests = LabTestInputSerializer(many=True, min_length=1)


class LabOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    test_count = serializers.IntegerField(source="tests.count", read_only=True)

    class Meta:
        model = LabOrder
        fields = [
            "id",
            "order_number",
            "patient",
            "patient_name",
            "doctor",
            "status",
            "priority",
            "ordered_at",
            "test_count",
        ]
