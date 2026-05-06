from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import TenantMembership, User, UserSecrets


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone", "keycloak_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2")}),
    )


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "tenant__name")


@admin.register(UserSecrets)
class UserSecretsAdmin(admin.ModelAdmin):
    list_display = ("user", "last_rotated_at", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("api_key_hash", "pin_hash", "refresh_token_encrypted", "mfa_backup_codes_encrypted")
