from rest_framework.routers import DefaultRouter

from . import views

app_name = "audit"

router = DefaultRouter()
router.register("", views.AuditLogViewSet, basename="audit-logs")

urlpatterns = router.urls
