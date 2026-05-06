"""
Health-check endpoints for load-balancer / orchestrator probes.
"""
from django.core.cache import cache
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def db_health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"status": "ok", "database": "connected"})
    except Exception as exc:
        return Response({"status": "error", "database": str(exc)}, status=503)


@api_view(["GET"])
@permission_classes([AllowAny])
def redis_health(request):
    try:
        cache.set("_health_check", "1", timeout=5)
        value = cache.get("_health_check")
        if value == "1":
            return Response({"status": "ok", "redis": "connected"})
        return Response({"status": "error", "redis": "read mismatch"}, status=503)
    except Exception as exc:
        return Response({"status": "error", "redis": str(exc)}, status=503)
