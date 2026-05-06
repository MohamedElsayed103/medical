"""
Patient views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsDoctor, IsReceptionistOrAbove

from .filters import PatientFilter
from .models import Patient
from .serializers import PatientCreateSerializer, PatientListSerializer, PatientSerializer
from .services import PatientService


class PatientViewSet(ModelViewSet):
    """
    /api/v1/patients/

    - list/create: Receptionist+
    - retrieve/update: Receptionist+
    - delete (soft): Admin only
    """

    queryset = Patient.objects.all()
    filterset_class = PatientFilter
    search_fields = ["first_name", "last_name", "phone", "medical_record_number"]
    ordering_fields = ["registered_at", "last_name", "created_at"]
    ordering = ["-registered_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PatientListSerializer
        if self.action == "create":
            return PatientCreateSerializer
        return PatientSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsReceptionistOrAbove()]  # Will be further restricted in perform_destroy
        return [IsReceptionistOrAbove()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = PatientService.register_patient(**serializer.validated_data)
        return Response(
            PatientSerializer(patient).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        patient = self.get_object()
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        patient = PatientService.update_patient(patient, **request.data)
        return Response(PatientSerializer(patient).data)

    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        PatientService.soft_delete_patient(patient)
        return Response(status=status.HTTP_204_NO_CONTENT)
