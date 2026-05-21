"""Referrals views."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.referrals.models import (
    FacilityConnection,
    Referral,
    ReferralStatus,
)
from apps.referrals.serializers import (
    ConnectionRequestSerializer,
    CreateReferralSerializer,
    DeclineReasonSerializer,
    FacilityConnectionSerializer,
    NoteInputSerializer,
    ReferralSerializer,
)
from apps.referrals.services import ReferralService


class FacilityConnectionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Manage facility connections.

    list – All connections involving the current tenant.
    request_connection – POST to propose a new connection.
    accept / suspend – Status transitions.
    """

    serializer_class = FacilityConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FacilityConnection.objects.none()
        from django.db.models import Q

        tenant = self.request.tenant
        return FacilityConnection.objects.filter(
            Q(from_tenant=tenant) | Q(to_tenant=tenant)
        ).select_related("from_tenant", "to_tenant")

    @action(detail=False, methods=["post"], url_path="request")
    def request_connection(self, request):
        ser = ConnectionRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from apps.tenants.models import Organization

        try:
            to_tenant = Organization.objects.get(pk=ser.validated_data["to_tenant"])
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Target organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            conn = ReferralService.request_connection(
                from_tenant=request.tenant,
                to_tenant=to_tenant,
                notes=ser.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            FacilityConnectionSerializer(conn).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        conn = self.get_object()
        try:
            conn = ReferralService.accept_connection(conn)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(FacilityConnectionSerializer(conn).data)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        conn = self.get_object()
        try:
            conn = ReferralService.suspend_connection(conn)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(FacilityConnectionSerializer(conn).data)


class ReferralViewSet(viewsets.ModelViewSet):
    """
    Referral CRUD + workflow actions.

    Only shows referrals where the current tenant is sender or receiver.
    """

    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Referral.objects.none()
        from django.db.models import Q

        tenant = self.request.tenant
        return (
            Referral.objects.filter(Q(from_tenant=tenant) | Q(to_tenant=tenant))
            .select_related("from_tenant", "to_tenant")
            .prefetch_related("notes__author_tenant")
        )

    def create(self, request, *args, **kwargs):
        ser = CreateReferralSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from apps.tenants.models import Organization

        try:
            to_tenant = Organization.objects.get(pk=ser.validated_data["to_tenant"])
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Target organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            referral = ReferralService.create_referral(
                from_tenant=request.tenant,
                to_tenant=to_tenant,
                referring_doctor_id=request.user.id,
                data=ser.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            ReferralSerializer(referral).data, status=status.HTTP_201_CREATED
        )

    # ── Status transition actions ──────────────────────────────────
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition(request, pk, ReferralStatus.SUBMITTED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._transition(
            request, pk, ReferralStatus.ACCEPTED, accepted_by_id=request.user.id
        )

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        ser = DeclineReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._transition(
            request,
            pk,
            ReferralStatus.DECLINED,
            decline_reason=ser.validated_data.get("reason", ""),
        )

    @action(detail=True, methods=["post"], url_path="start")
    def start_progress(self, request, pk=None):
        return self._transition(request, pk, ReferralStatus.IN_PROGRESS)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._transition(request, pk, ReferralStatus.COMPLETED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, pk, ReferralStatus.CANCELLED)

    def _transition(self, request, pk, new_status, **kwargs):
        referral = self.get_object()
        try:
            referral = ReferralService.transition(referral, new_status, **kwargs)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(ReferralSerializer(referral).data)

    # ── Notes ──────────────────────────────────────────────────────
    @action(detail=True, methods=["post", "get"], url_path="notes")
    def notes(self, request, pk=None):
        referral = self.get_object()
        if request.method == "GET":
            from apps.referrals.serializers import ReferralNoteSerializer

            qs = referral.notes.select_related("author_tenant").all()
            return Response(ReferralNoteSerializer(qs, many=True).data)

        ser = NoteInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ReferralService.add_note(
            referral=referral,
            author_id=request.user.id,
            author_tenant=request.tenant,
            content=ser.validated_data["content"],
        )
        from apps.referrals.serializers import ReferralNoteSerializer

        return Response(
            ReferralNoteSerializer(note).data, status=status.HTTP_201_CREATED
        )
