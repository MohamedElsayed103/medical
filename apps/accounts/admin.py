from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserSecrets, UserTenantMapping


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "is_active", "is_staff", "is_deleted", "created_at")
    list_filter = ("is_active", "is_staff", "is_deleted")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("username", "first_name", "last_name", "display_name", "phone", "keycloak_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Soft Delete", {"fields": ("is_deleted", "deleted_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2")}),
    )


@admin.register(UserTenantMapping)
class UserTenantMappingAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "email", "username", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("user__email", "tenant__name", "email")


@admin.register(UserSecrets)
class UserSecretsAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "last_rotated_at", "is_deleted", "created_at")
    list_filter = ("status", "is_deleted")
    search_fields = ("user__email",)
    readonly_fields = ("api_key_hash", "pin_hash", "secret")
