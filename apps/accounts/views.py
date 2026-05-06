"""
Accounts views — authentication endpoints and user profile.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from common.utils import verify_pin

from .models import User
from .serializers import MeSerializer, VerifyPinSerializer
from .services import AccountService, UserSecretsService


class MeView(APIView):
    """GET /api/v1/auth/me/ — current user profile + memberships."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Prefetch memberships for the serializer
        memberships = AccountService.get_user_memberships(user)
        user.memberships = memberships  # attach for serializer
        serializer = MeSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = MeSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VerifyPinView(APIView):
    """POST /api/v1/auth/verify-pin/ — verify clinical quick-access PIN."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            secrets = request.user.secrets
        except User.secrets.RelatedObjectDoesNotExist:
            return Response(
                {"error": {"code": "PIN_NOT_SET", "message": "No PIN configured."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not secrets.pin_hash:
            return Response(
                {"error": {"code": "PIN_NOT_SET", "message": "No PIN configured."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verify_pin(serializer.validated_data["pin"], secrets.pin_hash):
            return Response({"verified": True})

        return Response(
            {"error": {"code": "INVALID_PIN", "message": "Incorrect PIN."}},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ApiKeyView(APIView):
    """POST /api/v1/auth/api-keys/ — generate a new API key (shown once)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_key = UserSecretsService.generate_api_key(request.user)
        return Response(
            {
                "api_key": raw_key,
                "message": "Store this key securely. It will not be shown again.",
            },
            status=status.HTTP_201_CREATED,
        )
