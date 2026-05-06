"""
Celery tasks for AI integration.

Dispatched to the 'ai_tasks' queue with retry and exponential backoff.
"""
from celery import shared_task

from .clients import AIClientError
from .services import AIService


@shared_task(
    name="ai_integration.process_ai_request",
    queue="ai_tasks",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(AIClientError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def process_ai_request_task(self, ai_request_id: str):
    """
    Process an AI request asynchronously.
    Retries with exponential backoff on transient failures.
    """
    AIService.process_request(ai_request_id)
