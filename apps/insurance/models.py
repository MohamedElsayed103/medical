"""
Insurance models — tenant-scoped.

InsuranceProvider   Reference table for payers.
PatientInsurance    Patient ↔ Provider link with policy details.
InsuranceClaim      Claim filed against an invoice.
ClaimDocument       Supporting documents uploaded to MinIO.
"""
import uuid

from django.db import models

from common.models import BaseModel


class ClaimStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    IN_REVIEW = "in_review", "In Review"
    APPROVED = "approved", "Approved"
    PARTIALLY_APPROVED = "partially_approved", "Partially Approved"
    DENIED = "denied", "Denied"
    APPEALED = "appealed", "Appealed"
    PAID = "paid", "Paid"


class InsuranceProvider(BaseModel):
    """
    Insurance company / payer.
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True, help_text="Payer ID / code")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "insurance_provider"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PatientInsurance(BaseModel):
    """
    Link between a patient and their insurance provider.
    """

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="insurance_policies",
    )
    provider = models.ForeignKey(
        InsuranceProvider,
        on_delete=models.PROTECT,
        related_name="patient_policies",
    )
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    subscriber_name = models.CharField(max_length=255, blank=True)
    subscriber_relationship = models.CharField(
        max_length=30,
        choices=[
            ("self", "Self"),
            ("spouse", "Spouse"),
            ("child", "Child"),
            ("other", "Other"),
        ],
        default="self",
    )
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)

    class Meta:
        db_table = "insurance_patient_insurance"
        ordering = ["-is_primary", "-effective_date"]

    def __str__(self):
        return f"{self.patient} – {self.provider.name} ({self.policy_number})"

    @property
    def is_active(self):
        from django.utils import timezone

        today = timezone.now().date()
        if self.expiration_date and self.expiration_date < today:
            return False
        return self.effective_date <= today


class InsuranceClaim(BaseModel):
    """
    Insurance claim linked to an invoice.
    """

    invoice = models.ForeignKey(
        "billing.Invoice",
        on_delete=models.CASCADE,
        related_name="insurance_claims",
    )
    patient_insurance = models.ForeignKey(
        PatientInsurance,
        on_delete=models.PROTECT,
        related_name="claims",
    )
    claim_number = models.CharField(
        max_length=100, unique=True, blank=True, help_text="Auto-generated"
    )
    status = models.CharField(
        max_length=25,
        choices=ClaimStatus.choices,
        default=ClaimStatus.DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    amount_claimed = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    denial_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    AUDITED = True

    class Meta:
        db_table = "insurance_claim"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["patient_insurance", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.claim_number = f"CLM-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Claim {self.claim_number} ({self.status})"


class ClaimDocument(BaseModel):
    """
    Supporting document for a claim (stored in MinIO).
    """

    claim = models.ForeignKey(
        InsuranceClaim,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(
        max_length=500, help_text="MinIO object key"
    )
    content_type = models.CharField(max_length=100, default="application/pdf")
    uploaded_by_id = models.UUIDField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = "insurance_claim_document"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name} (Claim {self.claim.claim_number})"
