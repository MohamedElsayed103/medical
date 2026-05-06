from rest_framework.routers import DefaultRouter

from . import views

app_name = "appointments"

router = DefaultRouter()
router.register("doctors", views.DoctorProfileViewSet, basename="doctors")
router.register("", views.AppointmentViewSet, basename="appointments")

urlpatterns = router.urls
