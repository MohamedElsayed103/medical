from rest_framework.routers import DefaultRouter

from . import views

app_name = "medical_records"

router = DefaultRouter()
router.register("", views.VisitViewSet, basename="visits")

urlpatterns = router.urls
