"""Insurance admin."""
from django.contrib import admin

from apps.insurance.models import (
    ClaimDocument,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurance,
)


@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(PatientInsurance)
class PatientInsuranceAdmin(admin.ModelAdmin):
    list_display = ("patient", "provider", "policy_number", "is_primary", "effective_date")
    list_filter = ("is_primary",)
    raw_id_fields = ("patient", "provider")


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_number", "status", "amount_claimed", "amount_approved", "created_at")
    list_filter = ("status",)
    search_fields = ("claim_number",)
    raw_id_fields = ("invoice", "patient_insurance")


@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "claim", "content_type", "created_at")
    raw_id_fields = ("claim",)
