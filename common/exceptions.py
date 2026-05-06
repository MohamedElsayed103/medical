"""
Custom DRF exception handler.

Normalizes all error responses to a consistent format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": { ... }  // optional
    }
}
"""
import structlog
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = structlog.get_logger(__name__)


def custom_exception_handler(exc, context):
    """Wraps DRF's default handler with consistent error format."""

    # Convert Django exceptions to DRF equivalents
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    elif isinstance(exc, Http404):
        exc = APIException(detail="Not found.", code="not_found")
        exc.status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PermissionDenied):
        exc = APIException(detail="Permission denied.", code="permission_denied")
        exc.status_code = status.HTTP_403_FORBIDDEN

    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — log and return 500
        logger.exception("unhandled_exception", exc_info=exc, view=str(context.get("view")))
        return Response(
            {"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalize the response body
    error_code = _get_error_code(exc)
    error_body = {"error": {"code": error_code, "message": _get_message(exc)}}

    if isinstance(exc, ValidationError):
        error_body["error"]["fields"] = response.data
    elif isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            error_body["error"]["message"] = str(detail)

    response.data = error_body
    return response


def _get_error_code(exc: Exception) -> str:
    if hasattr(exc, "default_code"):
        return str(exc.default_code).upper()
    return type(exc).__name__.upper()


def _get_message(exc: Exception) -> str:
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            return "; ".join(str(d) for d in detail)
    return str(exc)


class ServiceError(APIException):
    """Base exception for business logic errors raised from service layer."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A business logic error occurred."
    default_code = "SERVICE_ERROR"

    def __init__(self, message: str, code: str = None):
        self.detail = message
        if code:
            self.default_code = code
