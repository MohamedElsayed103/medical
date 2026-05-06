"""
AI Integration service layer.

Orchestrates: create AIRequest → dispatch Celery task → (task calls AI client) → update AIRequest.
"""
import structlog
from django.utils import timezone

from common.enums import AIRequestStatus
from common.exceptions import ServiceError

from .clients import AIClient, AIClientError
from .models import AIRequest

logger = structlog.get_logger(__name__)


class AIService:

    @staticmethod
    def submit_request(
        *,
        requested_by_id: str,
        request_type: str,
        input_data: dict,
        patient=None,
    ) -> AIRequest:
        """
        Create an AIRequest record and return it.
        The actual processing is done asynchronously via Celery.
        """
        ai_request = AIRequest.objects.create(
            patient=patient,
            requested_by_id=requested_by_id,
            request_type=request_type,
            input_data=input_data,
        )
        logger.info(
            "ai_request_submitted",
            ai_request_id=str(ai_request.id),
            request_type=request_type,
        )
        return ai_request

    @staticmethod
    def process_request(ai_request_id: str) -> AIRequest:
        """
        Called by the Celery task. Sends the request to the AI service
        and updates the AIRequest record with the response.
        """
        ai_request = AIRequest.objects.get(pk=ai_request_id)

        if ai_request.status != AIRequestStatus.PENDING:
            raise ServiceError(
                f"AIRequest {ai_request_id} is not pending (status={ai_request.status}).",
                code="NOT_PENDING",
            )

        ai_request.status = AIRequestStatus.PROCESSING
        ai_request.save(update_fields=["status", "updated_at"])

        endpoint_map = {
            "diagnosis_suggestion": "/v1/diagnose",
            "drug_interaction": "/v1/drug-interaction",
            "lab_interpretation": "/v1/interpret-labs",
            "clinical_summary": "/v1/summarize",
            "treatment_plan": "/v1/treatment-plan",
        }
        endpoint = endpoint_map.get(ai_request.request_type, "/v1/general")

        client = AIClient()
        try:
            result = client.request(endpoint, ai_request.input_data)

            ai_request.output_data = result
            ai_request.model_name = result.get("model", "")
            ai_request.prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
            ai_request.completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
            ai_request.latency_ms = result.get("_latency_ms", 0)
            ai_request.status = AIRequestStatus.COMPLETED
            ai_request.completed_at = timezone.now()
            ai_request.save(update_fields=[
                "output_data",
                "model_name",
                "prompt_tokens",
                "completion_tokens",
                "latency_ms",
                "status",
                "completed_at",
                "updated_at",
            ])

            logger.info(
                "ai_request_completed",
                ai_request_id=str(ai_request.id),
                tokens=ai_request.total_tokens,
                latency_ms=ai_request.latency_ms,
            )
        except AIClientError as exc:
            ai_request.status = AIRequestStatus.FAILED
            ai_request.error_message = str(exc)
            ai_request.completed_at = timezone.now()
            ai_request.save(update_fields=[
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ])
            logger.error(
                "ai_request_failed",
                ai_request_id=str(ai_request.id),
                error=str(exc),
            )
            raise

        return ai_request
