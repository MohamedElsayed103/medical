"""
Patient django-filter FilterSet.
"""
import django_filters

from .models import Patient


class PatientFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search", label="Search name/phone/MRN")
    registered_after = django_filters.DateFilter(field_name="registered_at", lookup_expr="gte")
    registered_before = django_filters.DateFilter(field_name="registered_at", lookup_expr="lte")

    class Meta:
        model = Patient
        fields = {
            "gender": ["exact"],
            "blood_type": ["exact"],
            "is_active": ["exact"],
        }

    def filter_search(self, queryset, name, value):
        """Search across first_name, last_name, phone, and MRN."""
        return queryset.filter(
            models.Q(first_name__icontains=value)
            | models.Q(last_name__icontains=value)
            | models.Q(phone__icontains=value)
            | models.Q(medical_record_number__icontains=value)
        )


# We need the models import for Q objects
from django.db import models  # noqa: E402
