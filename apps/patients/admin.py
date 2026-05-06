from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "medical_record_number",
        "first_name",
        "last_name",
        "gender",
        "phone",
        "is_active",
        "registered_at",
    )
    list_filter = ("gender", "is_active", "blood_type")
    search_fields = ("first_name", "last_name", "phone", "medical_record_number")
    readonly_fields = ("medical_record_number", "registered_at", "created_at", "updated_at")
