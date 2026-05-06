"""
Lab service layer.
"""
import random
import string

import structlog
from django.db import transaction
from django.utils import timezone

from common.enums import LabOrderStatus
from common.exceptions import ServiceError

from .models import LabOrder, LabTest, TestResult

logger = structlog.get_logger(__name__)


def _generate_order_number() -> str:
    date_part = timezone.now().strftime("%Y%m%d")
    rand = "".join(random.choices(string.digits, k=5))
    return f"LAB-{date_part}-{rand}"


class LabService:

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        patient,
        doctor,
        visit=None,
        priority: str = "routine",
        clinical_notes: str = "",
        tests: list[dict],
    ) -> LabOrder:
        """
        Create a lab order with its tests atomically.

        ``tests`` is a list of dicts: {test_name, test_code?, specimen_type?, notes?}
        """
        order = LabOrder.objects.create(
            patient=patient,
            doctor=doctor,
            visit=visit,
            order_number=_generate_order_number(),
            priority=priority,
            clinical_notes=clinical_notes,
        )

        for test_data in tests:
            LabTest.objects.create(
                order=order,
                test_name=test_data["test_name"],
                test_code=test_data.get("test_code", ""),
                specimen_type=test_data.get("specimen_type", ""),
                notes=test_data.get("notes", ""),
            )

        logger.info(
            "lab_order_created",
            order_id=str(order.id),
            order_number=order.order_number,
            test_count=len(tests),
        )
        return order

    @staticmethod
    def transition_status(order: LabOrder, new_status: str) -> LabOrder:
        valid_transitions = {
            LabOrderStatus.PENDING: [LabOrderStatus.COLLECTED, LabOrderStatus.CANCELLED],
            LabOrderStatus.COLLECTED: [LabOrderStatus.IN_PROGRESS, LabOrderStatus.CANCELLED],
            LabOrderStatus.IN_PROGRESS: [LabOrderStatus.COMPLETED, LabOrderStatus.CANCELLED],
        }
        allowed = valid_transitions.get(order.status, [])
        if new_status not in allowed:
            raise ServiceError(
                f"Cannot transition from {order.status} to {new_status}.",
                code="INVALID_STATUS_TRANSITION",
            )

        order.status = new_status
        update_fields = ["status", "updated_at"]

        if new_status == LabOrderStatus.COMPLETED:
            order.completed_at = timezone.now()
            update_fields.append("completed_at")

        order.save(update_fields=update_fields)
        logger.info(
            "lab_order_status_changed",
            order_id=str(order.id),
            new_status=new_status,
        )
        return order

    @staticmethod
    def record_result(
        *,
        test: LabTest,
        value: str,
        unit: str = "",
        reference_range_low=None,
        reference_range_high=None,
        resulted_by_id: str,
        interpretation: str = "",
    ) -> TestResult:
        if hasattr(test, "result"):
            raise ServiceError("Result already recorded for this test.", code="RESULT_EXISTS")

        result = TestResult(
            test=test,
            value=value,
            unit=unit,
            reference_range_low=reference_range_low,
            reference_range_high=reference_range_high,
            resulted_by_id=resulted_by_id,
            interpretation=interpretation,
        )
        result.flag = result.auto_flag()
        result.save()

        logger.info(
            "test_result_recorded",
            test_id=str(test.id),
            flag=result.flag,
        )

        # Check if all tests in the order have results → auto-complete
        order = test.order
        total_tests = order.tests.count()
        completed_tests = TestResult.objects.filter(test__order=order).count()
        if total_tests == completed_tests and order.status != LabOrderStatus.COMPLETED:
            LabService.transition_status(order, LabOrderStatus.COMPLETED)

        return result
