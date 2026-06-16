"""
Appointment django-filter FilterSet.
"""
import django_filters

from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="scheduled_at", lookup_expr="date")
    date_from = django_filters.DateTimeFilter(field_name="scheduled_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="scheduled_at", lookup_expr="lte")
    # Frontend (and the rest of the API) refer to the doctor by `doctor_id`.
    doctor_id = django_filters.UUIDFilter(field_name="doctor")
    specialization = django_filters.CharFilter(
        field_name="doctor__specialization", lookup_expr="iexact"
    )

    class Meta:
        model = Appointment
        fields = {
            "doctor": ["exact"],
            "patient": ["exact"],
            "status": ["exact"],
            "type": ["exact"],
        }
