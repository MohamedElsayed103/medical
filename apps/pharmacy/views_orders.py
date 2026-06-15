"""
Pharmacy order views.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from apps.rbac.permissions import HasPermission
from common.exceptions import ServiceError
from .models import PharmacyOrder
from .serializers_orders import (
    BulkUploadSerializer,
    CompleteSaleSerializer,
    CreatePharmacyOrderSerializer,
    PharmacyOrderSerializer,
)
from .services import PharmacyOrderService


class PharmacyOrderViewSet(ModelViewSet):
    serializer_class = PharmacyOrderSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = PharmacyOrder.objects.select_related(
            "patient", "customer", "prescription", "invoice"
        ).prefetch_related("items__medication")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [HasPermission("pharmacy_orders:read")]
        return [HasPermission("pharmacy_orders:write")]

    def create(self, request, *args, **kwargs):
        ser = CreatePharmacyOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            order = PharmacyOrderService.create_order(
                created_by_id=str(request.user.id),
                patient_id=d.get("patient_id"),
                customer_id=d.get("customer_id"),
                customer_name=d.get("customer_name", ""),
                customer_phone=d.get("customer_phone", ""),
                prescription_id=d.get("prescription_id"),
                items=d["items"],
                notes=d.get("notes", ""),
            )
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PharmacyOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        order = self.get_object()
        try:
            order = PharmacyOrderService.checkout(order=order, created_by_id=str(request.user.id))
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PharmacyOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="fulfill")
    def fulfill(self, request, pk=None):
        order = self.get_object()
        try:
            order = PharmacyOrderService.fulfill(order=order, performed_by_id=str(request.user.id))
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PharmacyOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="complete-sale")
    def complete_sale(self, request, pk=None):
        order = self.get_object()
        ser = CompleteSaleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = PharmacyOrderService.complete_sale(
                order=order,
                amount=ser.validated_data["amount"],
                method=ser.validated_data.get("method", "cash"),
                received_by_id=str(request.user.id),
            )
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PharmacyOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order = PharmacyOrderService.cancel(order=order)
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PharmacyOrderSerializer(order).data)


class BulkUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [HasPermission("pharmacy:write")]

    def post(self, request, *args, **kwargs):
        ser = BulkUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = PharmacyOrderService.bulk_upload(
            file=ser.validated_data["file"],
            performed_by_id=str(request.user.id),
        )
        return Response(result, status=status.HTTP_200_OK)
