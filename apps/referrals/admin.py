"""Referrals admin."""
from django.contrib import admin

from apps.referrals.models import FacilityConnection, Referral, ReferralNote


@admin.register(FacilityConnection)
class FacilityConnectionAdmin(admin.ModelAdmin):
    list_display = ("from_tenant", "to_tenant", "status", "established_at")
    list_filter = ("status",)
    search_fields = ("from_tenant__name", "to_tenant__name")


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_tenant",
        "to_tenant",
        "priority",
        "status",
        "created_at",
    )
    list_filter = ("status", "priority")
    search_fields = ("reason",)


@admin.register(ReferralNote)
class ReferralNoteAdmin(admin.ModelAdmin):
    list_display = ("referral", "author_id", "created_at")
    raw_id_fields = ("referral",)
