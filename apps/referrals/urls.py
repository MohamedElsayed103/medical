"""Referrals URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.referrals.views import FacilityConnectionViewSet, ReferralViewSet

router = DefaultRouter()
router.register("connections", FacilityConnectionViewSet, basename="connection")
router.register("", ReferralViewSet, basename="referral")

app_name = "referrals"

urlpatterns = [
    path("", include(router.urls)),
]
