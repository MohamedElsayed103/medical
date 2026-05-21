"""RBAC admin configuration."""
from django.contrib import admin

from .models import Permission, Role, RolePermission, TenantUser, UserInvitation


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "is_system", "is_deleted", "created_at"]
    list_filter = ["is_system", "is_deleted"]
    search_fields = ["name"]
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["name", "resource", "is_deleted"]
    list_filter = ["resource", "is_deleted"]
    search_fields = ["name", "resource"]


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ["email", "username", "role", "status", "is_deleted"]
    list_filter = ["status", "role", "is_deleted"]
    search_fields = ["email", "username", "first_name", "last_name"]


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "role", "status", "expires_at", "created_at"]
    list_filter = ["status", "role"]
    search_fields = ["email"]
