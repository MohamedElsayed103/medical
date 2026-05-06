from django.contrib import admin

from .models import Medication, Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "prescribed_at", "is_dispensed"]
    list_filter = ["is_dispensed"]
    inlines = [PrescriptionItemInline]
    date_hierarchy = "prescribed_at"


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ["name", "generic_name", "form", "strength", "is_active"]
    list_filter = ["form", "is_active"]
    search_fields = ["name", "generic_name"]
