from rest_framework.routers import DefaultRouter

from . import views

app_name = "ai_integration"

router = DefaultRouter()
router.register("", views.AIRequestViewSet, basename="ai-requests")

urlpatterns = router.urls
