"""
Billing serializers.
"""
from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceItem, Payment


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "item_type",
            "description",
            "quantity",
            "unit_price",
            "total_price",
        ]
        read_only_fields = ["id", "total_price"]


class InvoiceItemInputSerializer(serializers.Serializer):
    item_type = serializers.CharField(max_length=20)
    description = serializers.CharField(max_length=500)
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"))


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "method",
            "reference_number",
            "paid_at",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "paid_at", "created_at"]


class PaymentInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    method = serializers.CharField(max_length=20)
    reference_number = serializers.CharField(max_length=100, required=False, default="")
    notes = serializers.CharField(required=False, default="")


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "patient_name",
            "issued_at",
            "due_date",
            "status",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total",
            "amount_paid",
            "balance_due",
            "notes",
            "items",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "issued_at",
            "status",
            "subtotal",
            "tax_amount",
            "total",
            "amount_paid",
            "created_at",
            "updated_at",
        ]


class InvoiceCreateSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField()
    due_date = serializers.DateField(required=False, allow_null=True)
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.00"), min_value=Decimal("0.00")
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), min_value=Decimal("0.00")
    )
    notes = serializers.CharField(required=False, default="")
    items = InvoiceItemInputSerializer(many=True, min_length=1)


class InvoiceListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "patient_name",
            "status",
            "total",
            "amount_paid",
            "balance_due",
            "issued_at",
        ]
