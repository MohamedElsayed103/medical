"""
Appointment serializers.
"""
from rest_framework import serializers

from common.enums import AppointmentStatus, AppointmentType

from .models import Appointment, DoctorAvailability, DoctorProfile, DoctorTimeOff


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


def _resolve_doctor_name(doctor) -> str:
    """Resolve a DoctorProfile's display name via its cross-schema user_id."""
    if doctor is None:
        return ""
    from apps.accounts.models import User
    try:
        user = User.objects.get(pk=doctor.user_id)
        name = f"{user.first_name} {user.last_name}".strip()
        return f"Dr. {name}" if name else user.email
    except User.DoesNotExist:
        return "Unknown"


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
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

    def get_doctor_name(self, obj) -> str:
        return _resolve_doctor_name(obj.doctor)


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
    doctor_name = serializers.SerializerMethodField()
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "doctor_specialization",
            "scheduled_at",
            "duration_minutes",
            "status",
            "type",
        ]

    def get_doctor_name(self, obj) -> str:
        return _resolve_doctor_name(obj.doctor)


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    # `doctor_id` (the FK attname) is read-only by default in DRF; declare it
    # explicitly so the window can actually be assigned to a doctor on create.
    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor", queryset=DoctorProfile.objects.all()
    )

    class Meta:
        model = DoctorAvailability
        fields = ["id", "doctor_id", "day_of_week", "start_time", "end_time", "is_active"]


class DoctorTimeOffSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        source="doctor", queryset=DoctorProfile.objects.all()
    )

    class Meta:
        model = DoctorTimeOff
        fields = ["id", "doctor_id", "start_at", "end_at", "reason"]
