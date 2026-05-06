"""
Audit middleware — captures request context and logs significant actions.
"""
import uuid

import structlog

from common.utils import get_client_ip

logger = structlog.get_logger(__name__)

_audit_context = {}


def get_audit_context() -> dict:
    """Retrieve the current request's audit context (set by middleware)."""
    import threading

    return getattr(threading.current_thread, "_audit_context", {})


def set_audit_context(context: dict):
    import threading

    threading.current_thread._audit_context = context


class AuditMiddleware:
    """
    Populates per-request audit context (user, IP, user-agent, request_id)
    available to signals and services via ``get_audit_context()``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.audit_request_id = request_id

        context = {
            "request_id": request_id,
            "user_id": str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else None,
            "user_email": getattr(request.user, "email", "") if hasattr(request, "user") else "",
            "ip_address": get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
        }
        set_audit_context(context)

        response = self.get_response(request)

        # Clear context after response
        set_audit_context({})

        return response
