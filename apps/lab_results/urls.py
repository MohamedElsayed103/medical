from rest_framework.routers import DefaultRouter

from . import views

app_name = "lab_results"

router = DefaultRouter()
router.register("", views.LabOrderViewSet, basename="lab-orders")

urlpatterns = router.urls
