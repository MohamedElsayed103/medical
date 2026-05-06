from rest_framework.routers import DefaultRouter

from . import views

app_name = "prescriptions"

router = DefaultRouter()
router.register("medications", views.MedicationViewSet, basename="medications")
router.register("", views.PrescriptionViewSet, basename="prescriptions")

urlpatterns = router.urls
