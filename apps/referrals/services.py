"""Referrals service layer."""
from django.utils import timezone

from apps.referrals.models import (
    ConnectionStatus,
    FacilityConnection,
    Referral,
    ReferralNote,
    ReferralStatus,
)


class ReferralService:
    """Business logic for the referral workflow."""

    # ── Connection management ──────────────────────────────────────
    @staticmethod
    def request_connection(*, from_tenant, to_tenant, notes: str = ""):
        if from_tenant == to_tenant:
            raise ValueError("Cannot create a connection to your own organization.")
        conn, created = FacilityConnection.objects.get_or_create(
            from_tenant=from_tenant,
            to_tenant=to_tenant,
            defaults={"notes": notes, "status": ConnectionStatus.PENDING},
        )
        if not created:
            raise ValueError("Connection already exists.")
        return conn

    @staticmethod
    def accept_connection(connection: FacilityConnection):
        if connection.status != ConnectionStatus.PENDING:
            raise ValueError("Only pending connections can be accepted.")
        connection.status = ConnectionStatus.ACTIVE
        connection.established_at = timezone.now()
        connection.save(update_fields=["status", "established_at", "updated_at"])
        return connection

    @staticmethod
    def suspend_connection(connection: FacilityConnection):
        if connection.status != ConnectionStatus.ACTIVE:
            raise ValueError("Only active connections can be suspended.")
        connection.status = ConnectionStatus.SUSPENDED
        connection.save(update_fields=["status", "updated_at"])
        return connection

    # ── Referral workflow ──────────────────────────────────────────
    VALID_TRANSITIONS = {
        ReferralStatus.DRAFT: [ReferralStatus.SUBMITTED, ReferralStatus.CANCELLED],
        ReferralStatus.SUBMITTED: [
            ReferralStatus.ACCEPTED,
            ReferralStatus.DECLINED,
            ReferralStatus.CANCELLED,
        ],
        ReferralStatus.ACCEPTED: [
            ReferralStatus.IN_PROGRESS,
            ReferralStatus.CANCELLED,
        ],
        ReferralStatus.IN_PROGRESS: [
            ReferralStatus.COMPLETED,
            ReferralStatus.CANCELLED,
        ],
    }

    @classmethod
    def create_referral(cls, *, from_tenant, to_tenant, referring_doctor_id, data: dict):
        # Ensure an active connection exists
        connection_exists = FacilityConnection.objects.filter(
            from_tenant=from_tenant,
            to_tenant=to_tenant,
            status=ConnectionStatus.ACTIVE,
        ).exists() or FacilityConnection.objects.filter(
            from_tenant=to_tenant,
            to_tenant=from_tenant,
            status=ConnectionStatus.ACTIVE,
        ).exists()

        if not connection_exists:
            raise ValueError(
                "An active connection with the target facility is required."
            )

        return Referral.objects.create(
            from_tenant=from_tenant,
            to_tenant=to_tenant,
            referring_doctor_id=referring_doctor_id,
            patient_summary=data.get("patient_summary", {}),
            reason=data.get("reason", ""),
            priority=data.get("priority", "routine"),
            clinical_notes=data.get("clinical_notes", ""),
            status=ReferralStatus.DRAFT,
        )

    @classmethod
    def transition(cls, referral: Referral, new_status: str, **kwargs):
        allowed = cls.VALID_TRANSITIONS.get(referral.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot move from '{referral.status}' to '{new_status}'."
            )

        referral.status = new_status
        fields = ["status", "updated_at"]

        if new_status == ReferralStatus.ACCEPTED:
            referral.accepted_at = timezone.now()
            referral.accepted_by_id = kwargs.get("accepted_by_id")
            fields += ["accepted_at", "accepted_by_id"]

        if new_status == ReferralStatus.COMPLETED:
            referral.completed_at = timezone.now()
            fields.append("completed_at")

        if new_status == ReferralStatus.DECLINED:
            referral.decline_reason = kwargs.get("decline_reason", "")
            fields.append("decline_reason")

        referral.save(update_fields=fields)
        return referral

    @staticmethod
    def add_note(*, referral: Referral, author_id, author_tenant, content: str):
        return ReferralNote.objects.create(
            referral=referral,
            author_id=author_id,
            author_tenant=author_tenant,
            content=content,
        )
