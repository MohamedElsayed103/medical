"""
AI Integration views.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins

from apps.accounts.permissions import IsDoctor
from apps.patients.models import Patient

from .models import AIRequest
from .serializers import AIRequestCreateSerializer, AIRequestSerializer
from .services import AIService
from .tasks import process_ai_request_task


class AIRequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    /api/v1/ai-requests/

    POST  → submit a new AI request (dispatches async Celery task)
    GET   → list user's AI requests
    GET /:id → retrieve single request (poll for completion)
    """

    serializer_class = AIRequestSerializer
    permission_classes = [IsDoctor]
    ordering = ["-requested_at"]

    def get_queryset(self):
        return AIRequest.objects.filter(requested_by_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = AIRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient = None
        if data.get("patient_id"):
            patient = Patient.objects.get(pk=data["patient_id"])

        ai_request = AIService.submit_request(
            requested_by_id=str(request.user.id),
            request_type=data["request_type"],
            input_data=data["input_data"],
            patient=patient,
        )

        # Dispatch to Celery
        process_ai_request_task.delay(str(ai_request.id))

        return Response(
            AIRequestSerializer(ai_request).data,
            status=status.HTTP_202_ACCEPTED,
        )
