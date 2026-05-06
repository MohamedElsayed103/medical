"""
AI Integration serializers.
"""
from rest_framework import serializers

from .models import AIRequest


class AIRequestSerializer(serializers.ModelSerializer):
    total_tokens = serializers.IntegerField(read_only=True)

    class Meta:
        model = AIRequest
        fields = [
            "id",
            "patient",
            "requested_by_id",
            "request_type",
            "status",
            "input_data",
            "output_data",
            "model_name",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_ms",
            "error_message",
            "requested_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "output_data",
            "model_name",
            "prompt_tokens",
            "completion_tokens",
            "latency_ms",
            "error_message",
            "requested_at",
            "completed_at",
            "created_at",
        ]


class AIRequestCreateSerializer(serializers.Serializer):
    request_type = serializers.CharField(max_length=30)
    input_data = serializers.DictField()
    patient_id = serializers.UUIDField(required=False, allow_null=True)
