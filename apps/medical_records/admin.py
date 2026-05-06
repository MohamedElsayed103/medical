from django.contrib import admin

from .models import Diagnosis, Visit, Vitals


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "visit_date", "is_signed"]
    list_filter = ["is_signed"]
    date_hierarchy = "visit_date"


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ["id", "visit", "heart_rate", "temperature", "recorded_at"]


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ["id", "visit", "icd_code", "diagnosis_type"]
    list_filter = ["diagnosis_type"]
