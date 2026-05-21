"""
Referrals models — PUBLIC schema (cross-tenant).

FacilityConnection   Bi-directional connection between organizations.
Referral             Patient referral between facilities.
ReferralNote         Notes / communication on a referral.
"""
import uuid

from django.db import models

from common.models import BaseModel


class ConnectionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"


class ReferralStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    DECLINED = "declined", "Declined"
    CANCELLED = "cancelled", "Cancelled"


class ReferralPriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "Stat"


class FacilityConnection(BaseModel):
    """
    Bi-directional connection between two organizations.
    Must be accepted by the receiving facility.
    """

    from_tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="outbound_connections",
    )
    to_tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="inbound_connections",
    )
    status = models.CharField(
        max_length=20,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.PENDING,
    )
    established_at = models.DateTimeField(null=True, blank=True)
    data_sharing_agreement = models.BooleanField(
        default=False,
        help_text="Whether a data sharing agreement is in place",
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "referrals_facility_connection"
        unique_together = ("from_tenant", "to_tenant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_tenant.name} → {self.to_tenant.name} ({self.status})"


class Referral(BaseModel):
    """
    Patient referral between facilities.

    Patient data is stored as a JSON summary (not FK) because patients
    are tenant-scoped. This respects data isolation.
    """

    from_tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="outbound_referrals",
    )
    to_tenant = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="inbound_referrals",
    )
    referring_doctor_id = models.UUIDField(
        help_text="User ID of the referring doctor"
    )
    patient_summary = models.JSONField(
        help_text="Anonymized patient clinical summary (not an FK — HIPAA compliant)",
        default=dict,
    )
    reason = models.TextField(help_text="Reason for referral")
    priority = models.CharField(
        max_length=10,
        choices=ReferralPriority.choices,
        default=ReferralPriority.ROUTINE,
    )
    status = models.CharField(
        max_length=20,
        choices=ReferralStatus.choices,
        default=ReferralStatus.DRAFT,
    )
    clinical_notes = models.TextField(blank=True)
    accepted_by_id = models.UUIDField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True)

    AUDITED = True

    class Meta:
        db_table = "referrals_referral"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["from_tenant", "status"]),
            models.Index(fields=["to_tenant", "status"]),
            models.Index(fields=["priority", "-created_at"]),
        ]

    def __str__(self):
        return f"Referral({self.from_tenant.name}→{self.to_tenant.name}) [{self.status}]"


class ReferralNote(BaseModel):
    """Communication note on a referral."""

    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="notes"
    )
    author_id = models.UUIDField()
    author_tenant = models.ForeignKey(
        "tenants.Organization", on_delete=models.CASCADE
    )
    content = models.TextField()

    class Meta:
        db_table = "referrals_note"
        ordering = ["created_at"]

    def __str__(self):
        return f"Note on Referral {self.referral_id} by {self.author_id}"
