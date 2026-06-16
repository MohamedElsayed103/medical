"""
Radiology views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.rbac.permissions import HasPermission
from common.exceptions import ServiceError
from .models import RadiologyOrder, RadiologyStudy
from .serializers import (
    CreateRadiologyOrderSerializer,
    RadiologyOrderSerializer,
    RecordReportSerializer,
    TransitionStatusSerializer,
)
from .services import RadiologyService


class RadiologyOrderViewSet(ModelViewSet):
    serializer_class = RadiologyOrderSerializer

    def get_queryset(self):
        qs = RadiologyOrder.objects.select_related(
            "patient", "customer", "doctor", "visit", "invoice"
        ).prefetch_related("studies__report")

        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [HasPermission("radiology:read")]
        return [HasPermission("radiology:write")]

    def create(self, request, *args, **kwargs):
        ser = CreateRadiologyOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        patient = None
        customer = None

        if d.get("patient_id"):
            from apps.patients.models import Patient
            try:
                patient = Patient.objects.get(id=d["patient_id"])
            except Patient.DoesNotExist:
                return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
        elif d.get("customer_id"):
            from apps.patients.models import Customer
            try:
                customer = Customer.objects.get(id=d["customer_id"])
            except Customer.DoesNotExist:
                return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        elif d.get("customer_name") and d.get("customer_phone"):
            from apps.patients.services_customers import CustomerService
            customer = CustomerService.get_or_create_by_phone(
                full_name=d["customer_name"], phone=d["customer_phone"]
            )
        else:
            return Response(
                {"detail": "Must provide patient_id, customer_id, or customer_name+customer_phone."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor = None
        if d.get("doctor_id"):
            from apps.appointments.models import DoctorProfile
            try:
                doctor = DoctorProfile.objects.get(id=d["doctor_id"])
            except DoctorProfile.DoesNotExist:
                pass

        visit = None
        if d.get("visit_id"):
            from apps.medical_records.models import Visit
            try:
                visit = Visit.objects.get(id=d["visit_id"])
            except Visit.DoesNotExist:
                pass

        try:
            order = RadiologyService.create_order(
                patient=patient,
                customer=customer,
                doctor=doctor,
                visit=visit,
                studies=d["studies"],
                priority=d.get("priority", "routine"),
                clinical_notes=d.get("clinical_notes", ""),
                created_by_id=str(request.user.id),
            )
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RadiologyOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        order = self.get_object()
        ser = TransitionStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = RadiologyService.transition_status(
                order=order,
                new_status=ser.validated_data["status"],
                performed_by_id=str(request.user.id),
            )
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RadiologyOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="report")
    def report(self, request, pk=None):
        self.check_permissions(request)
        order = self.get_object()
        ser = RecordReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            study = RadiologyStudy.objects.get(id=d["study_id"], order=order)
        except RadiologyStudy.DoesNotExist:
            return Response({"detail": "Study not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            rpt = RadiologyService.record_report(
                study=study,
                findings=d["findings"],
                impression=d.get("impression", ""),
                is_critical=d.get("is_critical", False),
                reported_by_id=str(request.user.id),
                image_object_key=d.get("image_object_key", ""),
            )
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        from .serializers import RadiologyReportSerializer
        return Response(RadiologyReportSerializer(rpt).data, status=status.HTTP_201_CREATED)

    def get_report_permissions(self):
        return [HasPermission("radiology:result")]
