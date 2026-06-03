"""Insurance views."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.insurance.models import (
    ClaimStatus,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurance,
)
from apps.insurance.serializers import (
    ClaimAmountSerializer,
    ClaimDocumentSerializer,
    CreateClaimSerializer,
    DenialReasonSerializer,
    InsuranceClaimSerializer,
    InsuranceProviderSerializer,
    PatientInsuranceSerializer,
)
from apps.insurance.services import InsuranceService


class InsuranceProviderViewSet(viewsets.ModelViewSet):
    """CRUD for insurance providers."""

    queryset = InsuranceProvider.objects.all()
    serializer_class = InsuranceProviderSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "code"]
    filterset_fields = ["is_active"]


class PatientInsuranceViewSet(viewsets.ModelViewSet):
    """CRUD for patient insurance policies."""

    serializer_class = PatientInsuranceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PatientInsurance.objects.select_related("provider").all()


class InsuranceClaimViewSet(viewsets.ModelViewSet):
    """
    Insurance claims with workflow actions.

    create – File a new claim (draft).
    submit / review / approve / deny / appeal / mark_paid – Status transitions.
    """

    serializer_class = InsuranceClaimSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["status", "patient_insurance"]

    def get_queryset(self):
        return (
            InsuranceClaim.objects.select_related(
                "invoice", "patient_insurance__provider"
            )
            .prefetch_related("documents")
            .all()
        )

    def create(self, request, *args, **kwargs):
        ser = CreateClaimSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        from apps.billing.models import Invoice

        invoice = None
        if ser.validated_data.get("invoice"):
            try:
                invoice = Invoice.objects.get(pk=ser.validated_data["invoice"])
            except Invoice.DoesNotExist:
                return Response(
                    {"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND
                )

        try:
            patient_ins = PatientInsurance.objects.get(
                pk=ser.validated_data["patient_insurance"]
            )
        except PatientInsurance.DoesNotExist:
            return Response(
                {"detail": "Patient insurance not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        claim = InsuranceService.create_claim(
            invoice=invoice,
            patient_insurance=patient_ins,
            amount_claimed=ser.validated_data["amount_claimed"],
            notes=ser.validated_data.get("notes", ""),
        )
        return Response(
            InsuranceClaimSerializer(claim).data, status=status.HTTP_201_CREATED
        )

    # ── Status transition actions ──────────────────────────────────
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition(pk, ClaimStatus.SUBMITTED)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        return self._transition(pk, ClaimStatus.IN_REVIEW)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        ser = ClaimAmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._transition(pk, ClaimStatus.APPROVED, **ser.validated_data)

    @action(detail=True, methods=["post"], url_path="partial-approve")
    def partial_approve(self, request, pk=None):
        ser = ClaimAmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._transition(
            pk, ClaimStatus.PARTIALLY_APPROVED, **ser.validated_data
        )

    @action(detail=True, methods=["post"])
    def deny(self, request, pk=None):
        ser = DenialReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return self._transition(pk, ClaimStatus.DENIED, **ser.validated_data)

    @action(detail=True, methods=["post"])
    def appeal(self, request, pk=None):
        return self._transition(pk, ClaimStatus.APPEALED)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        return self._transition(pk, ClaimStatus.PAID)

    def _transition(self, pk, new_status, **kwargs):
        claim = self.get_object()
        try:
            claim = InsuranceService.transition_claim(claim, new_status, **kwargs)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(InsuranceClaimSerializer(claim).data)

    # ── Documents ──────────────────────────────────────────────────
    @action(detail=True, methods=["get", "post"], url_path="documents")
    def documents(self, request, pk=None):
        claim = self.get_object()
        if request.method == "GET":
            return Response(
                ClaimDocumentSerializer(claim.documents.all(), many=True).data
            )

        from apps.insurance.models import ClaimDocument

        doc = ClaimDocument.objects.create(
            claim=claim,
            file_name=request.data.get("file_name", ""),
            file_path=request.data.get("file_path", ""),
            content_type=request.data.get("content_type", "application/pdf"),
            uploaded_by_id=request.user.id,
            description=request.data.get("description", ""),
        )
        return Response(
            ClaimDocumentSerializer(doc).data, status=status.HTTP_201_CREATED
        )

    # ── Summary ────────────────────────────────────────────────────
    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset()
        data = InsuranceService.get_claims_summary(qs)
        return Response(data)
