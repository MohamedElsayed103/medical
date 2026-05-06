"""
Lab views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsDoctor, IsLabTech, IsNurseOrAbove
from apps.appointments.models import DoctorProfile
from apps.medical_records.models import Visit
from apps.patients.models import Patient

from .models import LabOrder, LabTest
from .serializers import (
    LabOrderCreateSerializer,
    LabOrderListSerializer,
    LabOrderSerializer,
    TestResultInputSerializer,
    TestResultSerializer,
)
from .services import LabService


class LabOrderViewSet(ModelViewSet):
    """
    /api/v1/lab-orders/

    Custom actions: collect, in_progress, complete, cancel, record_result
    """

    queryset = LabOrder.objects.select_related("patient", "doctor").prefetch_related(
        "tests__result"
    ).all()
    ordering_fields = ["ordered_at", "priority", "status"]
    ordering = ["-ordered_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return LabOrderListSerializer
        if self.action == "create":
            return LabOrderCreateSerializer
        return LabOrderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsDoctor()]
        if self.action in ("record_result",):
            return [IsLabTech()]
        if self.action in ("collect", "in_progress", "complete"):
            return [IsLabTech()]
        return [IsNurseOrAbove()]

    def create(self, request, *args, **kwargs):
        serializer = LabOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = Patient.objects.get(pk=data["patient_id"])
        doctor = DoctorProfile.objects.get(pk=data["doctor_id"])
        visit = Visit.objects.get(pk=data["visit_id"]) if data.get("visit_id") else None

        order = LabService.create_order(
            patient=patient,
            doctor=doctor,
            visit=visit,
            priority=data.get("priority", "routine"),
            clinical_notes=data.get("clinical_notes", ""),
            tests=data["tests"],
        )
        return Response(LabOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def collect(self, request, pk=None):
        order = self.get_object()
        order = LabService.transition_status(order, "collected")
        return Response(LabOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def in_progress(self, request, pk=None):
        order = self.get_object()
        order = LabService.transition_status(order, "in_progress")
        return Response(LabOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()
        order = LabService.transition_status(order, "completed")
        return Response(LabOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order = LabService.transition_status(order, "cancelled")
        return Response(LabOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path=r"tests/(?P<test_pk>[^/.]+)/result")
    def record_result(self, request, pk=None, test_pk=None):
        order = self.get_object()
        test = LabTest.objects.get(pk=test_pk, order=order)

        serializer = TestResultInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = LabService.record_result(
            test=test,
            resulted_by_id=str(request.user.id),
            **serializer.validated_data,
        )
        return Response(TestResultSerializer(result).data, status=status.HTTP_201_CREATED)
