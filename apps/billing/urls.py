from rest_framework.routers import DefaultRouter

from . import views

app_name = "billing"

router = DefaultRouter()
router.register("", views.InvoiceViewSet, basename="invoices")

urlpatterns = router.urls
