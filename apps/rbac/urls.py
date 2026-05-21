"""RBAC URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "rbac"

router = DefaultRouter()
router.register(r"permissions", views.PermissionViewSet, basename="permissions")
router.register(r"roles", views.RoleViewSet, basename="roles")
router.register(r"users", views.TenantUserViewSet, basename="tenant-users")
router.register(r"invitations", views.InvitationViewSet, basename="invitations")

urlpatterns = [
    path("", include(router.urls)),
    path("me/", views.MyTenantProfileView.as_view(), name="my-profile"),
    path("invitations/accept/", views.AcceptInvitationView.as_view(), name="accept-invitation"),
    path("seed/", views.SeedRolesView.as_view(), name="seed-roles"),
]
