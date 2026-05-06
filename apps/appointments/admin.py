from django.contrib import admin

from .models import DoctorProfile, Appointment


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "specialization", "is_available", "consultation_fee"]
    list_filter = ["is_available", "specialization"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "scheduled_at", "status", "type"]
    list_filter = ["status", "type"]
    search_fields = ["patient__first_name", "patient__last_name"]
    date_hierarchy = "scheduled_at"
