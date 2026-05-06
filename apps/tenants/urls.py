from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "tenants"

router = DefaultRouter()
router.register("", views.OrganizationViewSet, basename="organizations")

urlpatterns = router.urls
