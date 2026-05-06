"""
Medical records views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsDoctor, IsNurseOrAbove
from apps.appointments.models import Appointment, DoctorProfile
from apps.patients.models import Patient

from .models import Visit
from .serializers import (
    DiagnosisSerializer,
    VisitCreateSerializer,
    VisitListSerializer,
    VisitSerializer,
    VitalsSerializer,
)
from .services import VisitService


class VisitViewSet(ModelViewSet):
    """
    /api/v1/visits/

    Custom actions: sign, vitals, diagnoses
    """

    queryset = Visit.objects.select_related("patient", "doctor").prefetch_related(
        "vitals", "diagnoses"
    ).all()
    ordering_fields = ["visit_date", "created_at"]
    ordering = ["-visit_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return VisitListSerializer
        if self.action == "create":
            return VisitCreateSerializer
        return VisitSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "sign", "add_diagnosis"):
            return [IsDoctor()]
        if self.action in ("record_vitals",):
            return [IsNurseOrAbove()]
        return [IsDoctor()]

    def create(self, request, *args, **kwargs):
        serializer = VisitCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = Patient.objects.get(pk=data["patient_id"])
        doctor = DoctorProfile.objects.get(pk=data["doctor_id"])
        appointment = None
        if data.get("appointment_id"):
            appointment = Appointment.objects.get(pk=data["appointment_id"])

        visit = VisitService.create_visit(
            patient=patient,
            doctor=doctor,
            visit_date=data["visit_date"],
            chief_complaint=data["chief_complaint"],
            appointment=appointment,
            history_of_present_illness=data.get("history_of_present_illness", ""),
            examination_notes=data.get("examination_notes", ""),
            assessment=data.get("assessment", ""),
            plan=data.get("plan", ""),
            follow_up_date=data.get("follow_up_date"),
        )
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        visit = self.get_object()
        visit = VisitService.update_visit(visit, **request.data)
        return Response(VisitSerializer(visit).data)

    @action(detail=True, methods=["post"])
    def sign(self, request, pk=None):
        visit = self.get_object()
        visit = VisitService.sign_visit(visit)
        return Response(VisitSerializer(visit).data)

    @action(detail=True, methods=["post", "get"])
    def vitals(self, request, pk=None):
        visit = self.get_object()

        if request.method == "GET":
            serializer = VitalsSerializer(visit.vitals.all(), many=True)
            return Response(serializer.data)

        serializer = VitalsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vitals = VisitService.record_vitals(
            visit,
            recorded_by_id=str(request.user.id),
            **serializer.validated_data,
        )
        return Response(VitalsSerializer(vitals).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post", "get"])
    def diagnoses(self, request, pk=None):
        visit = self.get_object()

        if request.method == "GET":
            serializer = DiagnosisSerializer(visit.diagnoses.all(), many=True)
            return Response(serializer.data)

        serializer = DiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        diagnosis = VisitService.add_diagnosis(visit, **serializer.validated_data)
        return Response(DiagnosisSerializer(diagnosis).data, status=status.HTTP_201_CREATED)
