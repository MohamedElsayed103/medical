from rest_framework.routers import DefaultRouter

from . import views

app_name = "documents"

router = DefaultRouter()
router.register("", views.DocumentViewSet, basename="documents")

urlpatterns = router.urls
