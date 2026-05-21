from django.contrib import admin

from .models import DispenseItem, DispenseRecord, PharmacyInventory, StockTransaction


@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display = [
        "medication",
        "batch_number",
        "quantity_on_hand",
        "reorder_level",
        "expiry_date",
        "location",
        "is_active",
    ]
    list_filter = ["is_active", "expiry_date"]
    search_fields = ["medication__name", "batch_number"]


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "inventory",
        "transaction_type",
        "quantity",
        "balance_after",
        "performed_by_id",
        "created_at",
    ]
    list_filter = ["transaction_type"]


@admin.register(DispenseRecord)
class DispenseRecordAdmin(admin.ModelAdmin):
    list_display = ["prescription", "status", "dispensed_by_id", "dispensed_at"]
    list_filter = ["status"]


@admin.register(DispenseItem)
class DispenseItemAdmin(admin.ModelAdmin):
    list_display = ["dispense_record", "medication", "quantity_dispensed", "batch_number"]
