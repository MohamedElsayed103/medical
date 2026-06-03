"""
Appointment serializers.
"""
from rest_framework import serializers

from common.enums import AppointmentStatus, AppointmentType

from .models import Appointment, DoctorProfile


class DoctorProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "user_id",
            "user_name",
            "specialization",
            "license_number",
            "qualification",
            "years_of_experience",
            "consultation_fee",
            "bio",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_user_name(self, obj) -> str:
        from apps.accounts.models import User
        try:
            user = User.objects.get(pk=obj.user_id)
            name = f"{user.first_name} {user.last_name}".strip()
            return name or user.email
        except User.DoesNotExist:
            return "Unknown"


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_specialization",
            "scheduled_at",
            "duration_minutes",
            "status",
            "type",
            "reason",
            "cancellation_reason",
            "cancelled_by_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "cancellation_reason",
            "cancelled_by_id",
            "created_at",
            "updated_at",
        ]


class BookAppointmentSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    doctor_id = serializers.UUIDField()
    scheduled_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(default=30, min_value=10, max_value=240)
    type = serializers.ChoiceField(choices=AppointmentType.choices, default=AppointmentType.IN_PERSON)
    reason = serializers.CharField(required=False, default="", allow_blank=True)


class RescheduleSerializer(serializers.Serializer):
    scheduled_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(required=False, min_value=10, max_value=240)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="", allow_blank=True)


class AvailableSlotsSerializer(serializers.Serializer):
    doctor_id = serializers.UUIDField()
    date = serializers.DateField()
    duration_minutes = serializers.IntegerField(default=30, min_value=10, max_value=240)


class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_specialization",
            "scheduled_at",
            "duration_minutes",
            "status",
            "type",
        ]
