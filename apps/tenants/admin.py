from django.contrib import admin

from .models import Domain, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "type", "is_active", "subscription_plan", "created_at")
    list_filter = ("type", "is_active", "subscription_plan")
    search_fields = ("name", "slug", "email")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
