from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "notifications"

router = DefaultRouter()
router.register("", views.NotificationViewSet, basename="notifications")

# Preferences is a singleton — accessed without pk
urlpatterns = [
    path(
        "preferences/",
        views.NotificationPreferenceViewSet.as_view({"get": "retrieve", "patch": "update"}),
        name="notification-preferences",
    ),
] + router.urls
