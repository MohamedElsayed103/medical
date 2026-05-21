"""Insurance service layer."""
from django.utils import timezone

from apps.insurance.models import (
    ClaimStatus,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurance,
)


class InsuranceService:
    """Business logic for insurance claims."""

    VALID_TRANSITIONS = {
        ClaimStatus.DRAFT: [ClaimStatus.SUBMITTED],
        ClaimStatus.SUBMITTED: [ClaimStatus.IN_REVIEW],
        ClaimStatus.IN_REVIEW: [
            ClaimStatus.APPROVED,
            ClaimStatus.PARTIALLY_APPROVED,
            ClaimStatus.DENIED,
        ],
        ClaimStatus.DENIED: [ClaimStatus.APPEALED],
        ClaimStatus.APPEALED: [ClaimStatus.IN_REVIEW],
        ClaimStatus.APPROVED: [ClaimStatus.PAID],
        ClaimStatus.PARTIALLY_APPROVED: [ClaimStatus.PAID, ClaimStatus.APPEALED],
    }

    # ── Provider management ────────────────────────────────────────
    @staticmethod
    def create_provider(data: dict) -> InsuranceProvider:
        return InsuranceProvider.objects.create(**data)

    @staticmethod
    def update_provider(provider: InsuranceProvider, data: dict) -> InsuranceProvider:
        for field, value in data.items():
            setattr(provider, field, value)
        provider.save()
        return provider

    # ── Patient insurance ──────────────────────────────────────────
    @staticmethod
    def add_patient_insurance(data: dict) -> PatientInsurance:
        return PatientInsurance.objects.create(**data)

    # ── Claim workflow ─────────────────────────────────────────────
    @staticmethod
    def create_claim(*, invoice, patient_insurance, amount_claimed, notes=""):
        return InsuranceClaim.objects.create(
            invoice=invoice,
            patient_insurance=patient_insurance,
            amount_claimed=amount_claimed,
            notes=notes,
            status=ClaimStatus.DRAFT,
        )

    @classmethod
    def transition_claim(cls, claim: InsuranceClaim, new_status: str, **kwargs):
        allowed = cls.VALID_TRANSITIONS.get(claim.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot move claim from '{claim.status}' to '{new_status}'."
            )

        claim.status = new_status
        fields = ["status", "updated_at"]

        if new_status == ClaimStatus.SUBMITTED:
            claim.submitted_at = timezone.now()
            fields.append("submitted_at")

        if new_status in (
            ClaimStatus.APPROVED,
            ClaimStatus.PARTIALLY_APPROVED,
            ClaimStatus.DENIED,
        ):
            claim.reviewed_at = timezone.now()
            fields.append("reviewed_at")

        if new_status in (ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED):
            claim.amount_approved = kwargs.get("amount_approved", claim.amount_claimed)
            fields.append("amount_approved")

        if new_status == ClaimStatus.DENIED:
            claim.denial_reason = kwargs.get("denial_reason", "")
            fields.append("denial_reason")

        claim.save(update_fields=fields)
        return claim

    @staticmethod
    def get_claims_summary(queryset):
        """Return aggregate statistics for a queryset of claims."""
        from django.db.models import Count, Sum

        return queryset.aggregate(
            total_claims=Count("id"),
            total_claimed=Sum("amount_claimed"),
            total_approved=Sum("amount_approved"),
        )
