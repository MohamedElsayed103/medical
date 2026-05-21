from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "pharmacy"

router = DefaultRouter()
router.register("inventory", views.PharmacyInventoryViewSet, basename="inventory")

urlpatterns = [
    path("low-stock/", views.LowStockView.as_view(), name="low-stock"),
    path("dispense-queue/", views.DispenseQueueView.as_view(), name="dispense-queue"),
    path("dispense/", views.DispensePrescriptionView.as_view(), name="dispense"),
] + router.urls
