from rest_framework.routers import DefaultRouter

from . import views
from .views import DoctorAvailabilityViewSet, DoctorTimeOffViewSet

app_name = "appointments"

router = DefaultRouter()
router.register("doctors", views.DoctorProfileViewSet, basename="doctors")
router.register("availability", DoctorAvailabilityViewSet, basename="doctor-availability")
router.register("time-off", DoctorTimeOffViewSet, basename="doctor-time-off")
router.register("", views.AppointmentViewSet, basename="appointments")

urlpatterns = router.urls
