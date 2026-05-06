"""
Root URL configuration.

Tenant-aware: public schema routes include admin + tenant management.
Tenant schemas route to app-specific API endpoints.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # ── Admin ──
    path("admin/", admin.site.urls),
    # ── OpenAPI Schema ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # ── Health check ──
    path("health/", include("common.health.urls")),
    # ── Prometheus ──
    path("", include("django_prometheus.urls")),
    # ── API v1 ──
    path("api/v1/auth/", include("apps.accounts.urls", namespace="accounts")),
    path("api/v1/tenants/", include("apps.tenants.urls", namespace="tenants")),
    path("api/v1/patients/", include("apps.patients.urls", namespace="patients")),
    path("api/v1/appointments/", include("apps.appointments.urls", namespace="appointments")),
    path("api/v1/prescriptions/", include("apps.prescriptions.urls", namespace="prescriptions")),
    path("api/v1/visits/", include("apps.medical_records.urls", namespace="medical_records")),
    path("api/v1/lab-orders/", include("apps.lab_results.urls", namespace="lab_results")),
    path("api/v1/invoices/", include("apps.billing.urls", namespace="billing")),
    path("api/v1/notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("api/v1/ai/", include("apps.ai_integration.urls", namespace="ai_integration")),
    path("api/v1/audit-logs/", include("apps.audit.urls", namespace="audit")),
]
