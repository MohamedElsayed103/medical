"""
Pharmacy views.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import serializers as drf_serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsNurseOrAbove, IsReceptionistOrAbove
from apps.prescriptions.models import Medication, Prescription

from .models import DispenseRecord, PharmacyInventory
from .serializers import (
    AdjustStockSerializer,
    DispensePrescriptionSerializer,
    DispenseRecordSerializer,
    PharmacyInventoryCreateSerializer,
    PharmacyInventorySerializer,
    ReceiveStockSerializer,
    StockTransactionSerializer,
)
from .services import PharmacyService


class PharmacyInventoryViewSet(ModelViewSet):
    """
    /api/v1/pharmacy/inventory/

    Custom actions: receive, adjust
    """

    serializer_class = PharmacyInventorySerializer
    permission_classes = [IsNurseOrAbove]
    search_fields = ["medication__name", "medication__generic_name", "batch_number"]
    ordering_fields = ["medication__name", "quantity_on_hand", "expiry_date"]
    ordering = ["medication__name"]

    def get_queryset(self):
        qs = PharmacyInventory.objects.select_related("medication").all()
        if self.request.query_params.get("low_stock"):
            from django.db.models import F
            qs = qs.filter(quantity_on_hand__lte=F("reorder_level"))
        if self.request.query_params.get("expired"):
            from django.utils import timezone
            qs = qs.filter(expiry_date__lte=timezone.now().date())
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return PharmacyInventoryCreateSerializer
        return PharmacyInventorySerializer

    def create(self, request, *args, **kwargs):
        serializer = PharmacyInventoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Remove non-model fields
        name = data.pop("name", "")
        generic_name = data.pop("generic_name", "")

        if data.get("medication_id"):
            medication = Medication.objects.get(pk=data.pop("medication_id"))
        else:
            # Find or create medication by name
            medication, _ = Medication.objects.get_or_create(
                name=name,
                defaults={
                    "generic_name": generic_name or name,
                    "form": "tablet",
                    "strength": "N/A",
                },
            )
            data.pop("medication_id", None)

        inventory = PharmacyInventory.objects.create(
            medication=medication, **data
        )
        return Response(
            PharmacyInventorySerializer(inventory).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """POST /api/v1/pharmacy/inventory/{id}/receive/ — receive stock."""
        inventory = self.get_object()
        serializer = ReceiveStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        txn = PharmacyService.receive_stock(
            inventory=inventory,
            performed_by_id=str(request.user.id),
            **serializer.validated_data,
        )
        return Response(
            StockTransactionSerializer(txn).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def adjust(self, request, pk=None):
        """POST /api/v1/pharmacy/inventory/{id}/adjust/ — manual adjustment."""
        inventory = self.get_object()
        serializer = AdjustStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        txn = PharmacyService.adjust_stock(
            inventory=inventory,
            performed_by_id=str(request.user.id),
            **serializer.validated_data,
        )
        return Response(
            StockTransactionSerializer(txn).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """GET /api/v1/pharmacy/inventory/{id}/transactions/ — stock history."""
        inventory = self.get_object()
        txns = inventory.transactions.all().order_by("-created_at")
        page = self.paginate_queryset(txns)
        if page is not None:
            return self.get_paginated_response(
                StockTransactionSerializer(page, many=True).data
            )
        return Response(StockTransactionSerializer(txns, many=True).data)

    @action(detail=True, methods=["post"])
    def dispense(self, request, pk=None):
        """POST /api/v1/pharmacy/inventory/{id}/dispense/ — dispense stock."""
        inventory = self.get_object()
        quantity = request.data.get("quantity")
        if not quantity or int(quantity) <= 0:
            return Response(
                {"detail": "A positive quantity is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        quantity = int(quantity)
        if quantity > inventory.quantity_on_hand:
            return Response(
                {"detail": "Insufficient stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = request.data.get("notes") or "Dispensed"
        txn = PharmacyService.adjust_stock(
            inventory=inventory,
            performed_by_id=str(request.user.id),
            quantity=-quantity,
            reason=reason,
        )
        return Response(
            StockTransactionSerializer(txn).data,
            status=status.HTTP_200_OK,
        )


class LowStockView(APIView):
    """GET /api/v1/pharmacy/low-stock/ — items below reorder level."""

    permission_classes = [IsNurseOrAbove]

    @extend_schema(
        tags=["pharmacy"],
        responses={200: PharmacyInventorySerializer(many=True)},
    )
    def get(self, request):
        from django.db.models import F

        items = PharmacyInventory.objects.filter(
            is_active=True,
            quantity_on_hand__lte=F("reorder_level"),
        ).select_related("medication")
        return Response(PharmacyInventorySerializer(items, many=True).data)


class DispenseQueueView(APIView):
    """GET /api/v1/pharmacy/dispense-queue/ — pending prescriptions to dispense."""

    permission_classes = [IsNurseOrAbove]

    @extend_schema(
        tags=["pharmacy"],
        responses={200: drf_serializers.ListSerializer(child=drf_serializers.DictField())},
    )
    def get(self, request):
        from apps.prescriptions.serializers import PrescriptionListSerializer

        pending = Prescription.objects.filter(
            is_dispensed=False,
        ).select_related("patient", "doctor").order_by("prescribed_at")
        page_size = 25
        return Response(PrescriptionListSerializer(pending[:page_size], many=True).data)


class DispensePrescriptionView(APIView):
    """POST /api/v1/pharmacy/dispense/ — dispense a prescription."""

    permission_classes = [IsNurseOrAbove]

    @extend_schema(
        tags=["pharmacy"],
        request=DispensePrescriptionSerializer,
        responses={201: DispenseRecordSerializer},
    )
    def post(self, request):
        serializer = DispensePrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prescription = Prescription.objects.get(
            pk=serializer.validated_data["prescription_id"]
        )

        record = PharmacyService.dispense_prescription(
            prescription=prescription,
            dispensed_by_id=str(request.user.id),
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(
            DispenseRecordSerializer(record).data,
            status=status.HTTP_201_CREATED,
        )
