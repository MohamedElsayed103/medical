"""
Appointment django-filter FilterSet.
"""
import django_filters

from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="scheduled_at", lookup_expr="date")
    date_from = django_filters.DateTimeFilter(field_name="scheduled_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="scheduled_at", lookup_expr="lte")

    class Meta:
        model = Appointment
        fields = {
            "doctor": ["exact"],
            "patient": ["exact"],
            "status": ["exact"],
            "type": ["exact"],
        }
