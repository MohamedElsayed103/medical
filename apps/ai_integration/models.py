"""
AI Integration models — tenant-scoped.

AIRequest   Tracks every request sent to the external AI service.
"""
from django.db import models

from apps.patients.models import Patient
from common.enums import AIRequestStatus, AIRequestType
from common.models import BaseModel


class AIRequest(BaseModel):
    """
    Record of a request to the external AI service.

    Stores the request payload, response, tokens used, latency, and error info
    for auditability and cost tracking.
    """

    AUDITED = True

    patient = models.ForeignKey(
        Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name="ai_requests"
    )
    requested_by_id = models.UUIDField(db_index=True, help_text="User ID of the requester")
    request_type = models.CharField(max_length=30, choices=AIRequestType.choices)
    status = models.CharField(
        max_length=20, choices=AIRequestStatus.choices, default=AIRequestStatus.PENDING
    )
    input_data = models.JSONField(default=dict, help_text="Sanitized input sent to AI service")
    output_data = models.JSONField(default=dict, blank=True, help_text="Response from AI service")
    model_name = models.CharField(max_length=100, blank=True)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0, help_text="Round-trip latency in ms")
    error_message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_integration_ai_request"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["request_type", "status"]),
            models.Index(fields=["requested_by_id", "requested_at"]),
        ]

    def __str__(self):
        return f"AI({self.request_type}, {self.status})"

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
