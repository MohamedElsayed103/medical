"""Insurance URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.insurance.views import (
    InsuranceClaimViewSet,
    InsuranceProviderViewSet,
    PatientInsuranceViewSet,
)

router = DefaultRouter()
router.register("providers", InsuranceProviderViewSet, basename="provider")
router.register("policies", PatientInsuranceViewSet, basename="policy")
router.register("claims", InsuranceClaimViewSet, basename="claim")

app_name = "insurance"

urlpatterns = [
    path("", include(router.urls)),
]
