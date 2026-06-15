from rest_framework.routers import DefaultRouter
from .views import RadiologyOrderViewSet

app_name = "radiology"

router = DefaultRouter()
router.register("orders", RadiologyOrderViewSet, basename="radiology-order")

urlpatterns = router.urls
