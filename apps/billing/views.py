"""
Billing views.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers as drf_serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsBillingStaff, IsOwnerOrAdmin, IsReceptionistOrAbove
from apps.patients.models import Patient
from common.enums import InvoiceStatus

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

    @action(detail=False, methods=["get"], url_path="revenue-timeseries")
    def revenue_timeseries(self, request):
        """
        Returns daily revenue for the past N days (default 30).
        Query params: days (int, max 365), group_by (day|week|month)
        """
        from datetime import timedelta

        from django.db.models import Sum
        from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
        from django.utils import timezone as tz

        try:
            days = min(int(request.query_params.get("days", 30)), 365)
        except (ValueError, TypeError):
            days = 30

        group_by = request.query_params.get("group_by", "day")
        trunc_fn = {"week": TruncWeek, "month": TruncMonth}.get(group_by, TruncDay)

        since = tz.now() - timedelta(days=days)

        qs = (
            Invoice.objects.filter(
                status__in=[InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID],
                updated_at__gte=since,
            )
            .annotate(period=trunc_fn("updated_at"))
            .values("period")
            .annotate(revenue=Sum("amount_paid"))
            .order_by("period")
        )

        data = [
            {"date": row["period"].isoformat(), "revenue": float(row["revenue"] or 0)}
            for row in qs
        ]

        return Response({"results": data, "days": days})


class BillingSummaryView(APIView):
    """GET /api/v1/billing/summary/ — revenue dashboard."""

    permission_classes = [IsOwnerOrAdmin]

    @extend_schema(
        tags=["billing"],
        parameters=[
            OpenApiParameter(name="date_from", type=str, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter(name="date_to", type=str, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: inline_serializer("BillingSummaryResponse", fields={
            "total_invoiced": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
            "total_paid": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
            "total_outstanding": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
            "invoice_count": drf_serializers.IntegerField(),
            "paid_count": drf_serializers.IntegerField(),
            "overdue_count": drf_serializers.IntegerField(),
            "draft_count": drf_serializers.IntegerField(),
            "by_payment_method": drf_serializers.ListField(),
        })},
    )
    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        qs = Invoice.objects.all()

        if date_from:
            qs = qs.filter(issued_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(issued_at__date__lte=date_to)

        zero = Decimal("0.00")
        summary = qs.aggregate(
            total_invoiced=Coalesce(
                Sum("total"),
                Value(zero),
                output_field=DecimalField(),
            ),
            total_paid=Coalesce(
                Sum("amount_paid"),
                Value(zero),
                output_field=DecimalField(),
            ),
            total_outstanding=Coalesce(
                Sum(
                    "total",
                    filter=Q(status__in=[
                        InvoiceStatus.ISSUED,
                        InvoiceStatus.PARTIALLY_PAID,
                        InvoiceStatus.OVERDUE,
                    ]),
                ),
                Value(zero),
                output_field=DecimalField(),
            ),
            invoice_count=Count("id"),
            paid_count=Count("id", filter=Q(status=InvoiceStatus.PAID)),
            overdue_count=Count("id", filter=Q(status=InvoiceStatus.OVERDUE)),
            draft_count=Count("id", filter=Q(status=InvoiceStatus.DRAFT)),
        )

        # Payment method breakdown
        from .models import Payment
        payment_qs = Payment.objects.all()
        if date_from:
            payment_qs = payment_qs.filter(paid_at__date__gte=date_from)
        if date_to:
            payment_qs = payment_qs.filter(paid_at__date__lte=date_to)

        by_method = (
            payment_qs.values("method")
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Value(zero),
                    output_field=DecimalField(),
                ),
                count=Count("id"),
            )
            .order_by("-total")
        )

        return Response({
            **summary,
            "by_payment_method": list(by_method),
        })
