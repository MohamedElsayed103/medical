"""
Pharmacy serializers.
"""
from rest_framework import serializers

from .models import DispenseItem, DispenseRecord, PharmacyInventory, StockTransaction


class PharmacyInventorySerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)
    medication_generic = serializers.CharField(
        source="medication.generic_name", read_only=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = PharmacyInventory
        fields = [
            "id",
            "medication",
            "medication_name",
            "medication_generic",
            "batch_number",
            "expiry_date",
            "quantity_on_hand",
            "reorder_level",
            "reorder_quantity",
            "unit_cost",
            "location",
            "is_active",
            "is_low_stock",
            "total_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PharmacyInventoryCreateSerializer(serializers.Serializer):
    medication_id = serializers.UUIDField()
    batch_number = serializers.CharField(max_length=100, required=False, default="")
    expiry_date = serializers.DateField(required=False, allow_null=True)
    quantity_on_hand = serializers.IntegerField(min_value=0, default=0)
    reorder_level = serializers.IntegerField(min_value=0, default=10)
    reorder_quantity = serializers.IntegerField(min_value=0, default=50)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = serializers.CharField(max_length=200, required=False, default="")


class StockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "inventory",
            "transaction_type",
            "quantity",
            "balance_after",
            "reference",
            "reason",
            "performed_by_id",
            "created_at",
        ]


class ReceiveStockSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(max_length=255, required=False, default="")
    reason = serializers.CharField(required=False, default="")


class AdjustStockSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    reason = serializers.CharField()


class DispenseItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)

    class Meta:
        model = DispenseItem
        fields = [
            "id",
            "medication",
            "medication_name",
            "inventory",
            "quantity_dispensed",
            "batch_number",
        ]


class DispenseRecordSerializer(serializers.ModelSerializer):
    items = DispenseItemSerializer(many=True, read_only=True)

    class Meta:
        model = DispenseRecord
        fields = [
            "id",
            "prescription",
            "status",
            "dispensed_by_id",
            "dispensed_at",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]


class DispensePrescriptionSerializer(serializers.Serializer):
    prescription_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, default="")
