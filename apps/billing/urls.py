from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "billing"

router = DefaultRouter()
router.register("", views.InvoiceViewSet, basename="invoices")

urlpatterns = [
    path("summary/", views.BillingSummaryView.as_view(), name="billing-summary"),
] + router.urls
