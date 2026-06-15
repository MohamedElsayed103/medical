"""
Pharmacy order serializers.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import PharmacyOrder, PharmacyOrderItem


class PharmacyOrderItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PharmacyOrderItem
        fields = ["id", "medication_id", "medication_name", "quantity", "unit_price", "line_total"]


class PharmacyOrderSerializer(serializers.ModelSerializer):
    items = PharmacyOrderItemSerializer(many=True, read_only=True)
    orderer_name = serializers.CharField(read_only=True)
    orderer_type = serializers.CharField(read_only=True)

    class Meta:
        model = PharmacyOrder
        fields = [
            "id", "order_number", "status",
            "patient_id", "customer_id", "prescription_id", "invoice_id",
            "orderer_name", "orderer_type",
            "notes", "created_by_id",
            "created_at", "updated_at",
            "items",
        ]


class OrderItemInputSerializer(serializers.Serializer):
    medication_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class CreatePharmacyOrderSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")
    customer_phone = serializers.CharField(required=False, allow_blank=True, default="")
    prescription_id = serializers.UUIDField(required=False, allow_null=True)
    items = OrderItemInputSerializer(many=True, min_length=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CompleteSaleSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    method = serializers.CharField(default="cash")


class BulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
