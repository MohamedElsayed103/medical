"""
HTTP client for the external AI service.

All calls go through this client so we have a single point for
timeouts, retries, auth headers, and error handling.
"""
import time

import httpx
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


class AIClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class AIClient:
    """
    Synchronous HTTP client for the AI microservice.
    Used inside Celery tasks (not in request-response cycle).
    """

    def __init__(self):
        self.base_url = settings.AI_SERVICE_BASE_URL
        self.api_key = getattr(settings, "AI_SERVICE_API_KEY", "")
        self.timeout = getattr(settings, "AI_SERVICE_TIMEOUT", 30)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def request(self, endpoint: str, payload: dict) -> dict:
        """
        Send a POST request to the AI service.
        Returns parsed JSON response.
        Raises AIClientError on failure.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start = time.monotonic()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=self._headers())
            latency_ms = int((time.monotonic() - start) * 1000)

            if response.status_code >= 400:
                logger.error(
                    "ai_client_error",
                    url=url,
                    status_code=response.status_code,
                    body=response.text[:500],
                    latency_ms=latency_ms,
                )
                raise AIClientError(
                    f"AI service returned {response.status_code}",
                    status_code=response.status_code,
                )

            result = response.json()
            result["_latency_ms"] = latency_ms
            logger.info("ai_client_success", url=url, latency_ms=latency_ms)
            return result

        except httpx.TimeoutException as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error("ai_client_timeout", url=url, latency_ms=latency_ms)
            raise AIClientError("AI service request timed out") from exc
        except httpx.RequestError as exc:
            logger.error("ai_client_connection_error", url=url, error=str(exc))
            raise AIClientError(f"Connection error: {exc}") from exc
