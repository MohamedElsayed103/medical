"""
Billing views.
"""
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsBillingStaff, IsReceptionistOrAbove
from apps.patients.models import Patient

from .models import Invoice
from .serializers import (
    InvoiceCreateSerializer,
    InvoiceListSerializer,
    InvoiceSerializer,
    PaymentInputSerializer,
    PaymentSerializer,
)
from .services import BillingService


class InvoiceViewSet(ModelViewSet):
    """
    /api/v1/invoices/

    Custom actions: finalize, pay, cancel, void, payments (list)
    """

    queryset = Invoice.objects.select_related("patient").prefetch_related(
        "items", "payments"
    ).all()
    ordering_fields = ["issued_at", "total", "status"]
    ordering = ["-issued_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return InvoiceListSerializer
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def get_permissions(self):
        return [IsBillingStaff()]

    def create(self, request, *args, **kwargs):
        serializer = InvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = Patient.objects.get(pk=data["patient_id"])

        invoice = BillingService.create_invoice(
            patient=patient,
            items=data["items"],
            tax_rate=data.get("tax_rate", Decimal("0.00")),
            discount_amount=data.get("discount_amount", Decimal("0.00")),
            due_date=data.get("due_date"),
            notes=data.get("notes", ""),
        )
        return Response(
            InvoiceSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        invoice = self.get_object()
        invoice = BillingService.finalize_invoice(invoice)
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        invoice = self.get_object()
        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = BillingService.record_payment(
            invoice=invoice,
            received_by_id=str(request.user.id),
            **serializer.validated_data,
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        invoice = BillingService.cancel_invoice(invoice)
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        invoice = self.get_object()
        invoice = BillingService.void_invoice(invoice)
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        invoice = self.get_object()
        serializer = PaymentSerializer(invoice.payments.all(), many=True)
        return Response(serializer.data)
