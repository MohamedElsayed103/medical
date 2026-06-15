from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .views_orders import BulkUploadView, PharmacyOrderViewSet

app_name = "pharmacy"

router = DefaultRouter()
router.register("inventory", views.PharmacyInventoryViewSet, basename="inventory")
router.register("orders", PharmacyOrderViewSet, basename="pharmacy-order")

urlpatterns = [
    path("low-stock/", views.LowStockView.as_view(), name="low-stock"),
    path("dispense-queue/", views.DispenseQueueView.as_view(), name="dispense-queue"),
    path("dispense/", views.DispensePrescriptionView.as_view(), name="dispense"),
    path("bulk-upload/", BulkUploadView.as_view(), name="bulk-upload"),
] + router.urls
