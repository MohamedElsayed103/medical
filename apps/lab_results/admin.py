from django.contrib import admin

from .models import LabOrder, LabTest, TestResult


class LabTestInline(admin.TabularInline):
    model = LabTest
    extra = 0


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "patient", "doctor", "status", "priority", "ordered_at"]
    list_filter = ["status", "priority"]
    search_fields = ["order_number"]
    inlines = [LabTestInline]
    date_hierarchy = "ordered_at"


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ["test", "value", "unit", "flag", "resulted_at"]
    list_filter = ["flag"]
