"""
Appointment views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsDoctor, IsReceptionistOrAbove
from apps.patients.models import Patient
from common.enums import AppointmentStatus

from .filters import AppointmentFilter
from .models import Appointment, DoctorProfile
from .serializers import (
    AppointmentListSerializer,
    AppointmentSerializer,
    AvailableSlotsSerializer,
    BookAppointmentSerializer,
    CancelSerializer,
    DoctorProfileSerializer,
    RescheduleSerializer,
)
from .services import AppointmentService


class DoctorProfileViewSet(ModelViewSet):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsReceptionistOrAbove]
    search_fields = ["specialization"]
    ordering_fields = ["specialization", "consultation_fee", "created_at"]


class AppointmentViewSet(ModelViewSet):
    """
    /api/v1/appointments/

    Custom actions: confirm, start, complete, cancel, no-show, available-slots
    """

    queryset = Appointment.objects.select_related("patient", "doctor").all()
    filterset_class = AppointmentFilter
    ordering_fields = ["scheduled_at", "created_at", "status"]
    ordering = ["-scheduled_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        if self.action == "create":
            return BookAppointmentSerializer
        return AppointmentSerializer

    def get_permissions(self):
        if self.action in ("confirm", "start", "complete", "cancel", "no_show"):
            return [IsReceptionistOrAbove()]
        return [IsReceptionistOrAbove()]

    def create(self, request, *args, **kwargs):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = Patient.objects.get(pk=data["patient_id"])
        doctor = DoctorProfile.objects.get(pk=data["doctor_id"])

        appointment = AppointmentService.book(
            patient=patient,
            doctor=doctor,
            scheduled_at=data["scheduled_at"],
            duration_minutes=data["duration_minutes"],
            appointment_type=data["type"],
            reason=data.get("reason", ""),
        )
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        appointment = self.get_object()
        serializer = RescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = AppointmentService.reschedule(
            appointment,
            new_scheduled_at=serializer.validated_data["scheduled_at"],
            new_duration=serializer.validated_data.get("duration_minutes"),
        )
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        appointment = AppointmentService.transition_status(appointment, AppointmentStatus.CONFIRMED)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        appointment = self.get_object()
        appointment = AppointmentService.transition_status(appointment, AppointmentStatus.IN_PROGRESS)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        appointment = AppointmentService.transition_status(appointment, AppointmentStatus.COMPLETED)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = AppointmentService.transition_status(
            appointment,
            AppointmentStatus.CANCELLED,
            cancelled_by_id=str(request.user.id),
            cancellation_reason=serializer.validated_data.get("reason", ""),
        )
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request, pk=None):
        appointment = self.get_object()
        appointment = AppointmentService.transition_status(appointment, AppointmentStatus.NO_SHOW)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=False, methods=["get"], url_path="available-slots")
    def available_slots(self, request):
        serializer = AvailableSlotsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        doctor = DoctorProfile.objects.get(pk=data["doctor_id"])
        slots = AppointmentService.get_available_slots(
            doctor=doctor,
            date=data["date"],
            duration_minutes=data["duration_minutes"],
        )
        return Response({"slots": [s.isoformat() for s in slots]})
