from rest_framework.routers import DefaultRouter

from . import views

app_name = "patients"

router = DefaultRouter()
router.register("", views.PatientViewSet, basename="patients")

urlpatterns = router.urls
