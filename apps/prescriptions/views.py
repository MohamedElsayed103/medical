"""
Prescription views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsDoctor, IsReceptionistOrAbove
from apps.appointments.models import DoctorProfile
from apps.medical_records.models import Visit
from apps.patients.models import Patient

from .models import Medication, Prescription
from .serializers import (
    MedicationSerializer,
    PrescriptionCreateSerializer,
    PrescriptionListSerializer,
    PrescriptionSerializer,
)
from .services import PrescriptionService


class MedicationViewSet(ModelViewSet):
    queryset = Medication.objects.filter(is_active=True)
    serializer_class = MedicationSerializer
    permission_classes = [IsReceptionistOrAbove]
    search_fields = ["name", "generic_name"]
    ordering_fields = ["name", "generic_name"]


class PrescriptionViewSet(ModelViewSet):
    """
    /api/v1/prescriptions/

    Custom actions: dispense
    """

    queryset = Prescription.objects.select_related("patient", "doctor").prefetch_related(
        "items__medication"
    ).all()
    ordering_fields = ["prescribed_at", "created_at"]
    ordering = ["-prescribed_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PrescriptionListSerializer
        if self.action == "create":
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsDoctor()]
        if self.action == "dispense":
            return [IsReceptionistOrAbove()]
        return [IsDoctor()]

    def create(self, request, *args, **kwargs):
        serializer = PrescriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = Patient.objects.get(pk=data["patient_id"])
        doctor = DoctorProfile.objects.get(pk=data["doctor_id"])
        visit = Visit.objects.get(pk=data["visit_id"]) if data.get("visit_id") else None

        prescription = PrescriptionService.create_prescription(
            patient=patient,
            doctor=doctor,
            visit=visit,
            notes=data.get("notes", ""),
            items=data["items"],
        )
        return Response(
            PrescriptionSerializer(prescription).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def dispense(self, request, pk=None):
        prescription = self.get_object()
        prescription = PrescriptionService.dispense(prescription)
        return Response(PrescriptionSerializer(prescription).data)
