"""
Patient views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsBillingStaff, IsDoctor, IsLabTech, IsReceptionistOrAbove

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
        patient = PatientService.update_patient(patient, **serializer.validated_data)
        return Response(PatientSerializer(patient).data)

    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        PatientService.soft_delete_patient(patient)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Sub-resource endpoints ──

    @action(detail=True, methods=["get"], permission_classes=[IsDoctor])
    def visits(self, request, pk=None):
        """GET /api/v1/patients/{id}/visits/ — patient visit history."""
        from apps.medical_records.models import Visit
        from apps.medical_records.serializers import VisitListSerializer

        patient = self.get_object()
        visits = Visit.objects.filter(patient=patient).select_related(
            "doctor"
        ).order_by("-visit_date")
        page = self.paginate_queryset(visits)
        if page is not None:
            return self.get_paginated_response(VisitListSerializer(page, many=True).data)
        return Response(VisitListSerializer(visits, many=True).data)

    @action(detail=True, methods=["get"], permission_classes=[IsDoctor])
    def prescriptions(self, request, pk=None):
        """GET /api/v1/patients/{id}/prescriptions/ — patient prescription history."""
        from apps.prescriptions.models import Prescription
        from apps.prescriptions.serializers import PrescriptionListSerializer

        patient = self.get_object()
        prescriptions = Prescription.objects.filter(patient=patient).select_related(
            "doctor"
        ).order_by("-prescribed_at")
        page = self.paginate_queryset(prescriptions)
        if page is not None:
            return self.get_paginated_response(PrescriptionListSerializer(page, many=True).data)
        return Response(PrescriptionListSerializer(prescriptions, many=True).data)

    @action(detail=True, methods=["get"], url_path="lab-results", permission_classes=[IsDoctor])
    def lab_results(self, request, pk=None):
        """GET /api/v1/patients/{id}/lab-results/ — patient lab order history."""
        from apps.lab_results.models import LabOrder
        from apps.lab_results.serializers import LabOrderListSerializer

        patient = self.get_object()
        orders = LabOrder.objects.filter(patient=patient).select_related(
            "doctor"
        ).order_by("-ordered_at")
        page = self.paginate_queryset(orders)
        if page is not None:
            return self.get_paginated_response(LabOrderListSerializer(page, many=True).data)
        return Response(LabOrderListSerializer(orders, many=True).data)

    @action(detail=True, methods=["get"], permission_classes=[IsBillingStaff])
    def invoices(self, request, pk=None):
        """GET /api/v1/patients/{id}/invoices/ — patient billing history."""
        from apps.billing.models import Invoice
        from apps.billing.serializers import InvoiceListSerializer

        patient = self.get_object()
        invoices = Invoice.objects.filter(patient=patient).order_by("-issued_at")
        page = self.paginate_queryset(invoices)
        if page is not None:
            return self.get_paginated_response(InvoiceListSerializer(page, many=True).data)
        return Response(InvoiceListSerializer(invoices, many=True).data)
