"""
Tenant models — public schema.

Organization    The tenant entity (clinic / hospital / lab).
Domain          Maps hostnames to organizations (required by django-tenants).
"""
import uuid

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from common.enums import OrganizationType, SubscriptionPlan


class Organization(TenantMixin):
    """
    Each clinic / hospital / lab is an Organization with its own
    PostgreSQL schema.  ``TenantMixin`` provides ``schema_name``
    and the ``auto_create_schema`` mechanism.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=OrganizationType.choices)
    license_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_create_schema = True

    class Meta:
        db_table = "tenants_organization"
        verbose_name = "organization"
        verbose_name_plural = "organizations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Maps hostnames / subdomains to organizations.

    Example:
        clinic-abc.healthsaas.com  →  Organization(slug='clinic-abc')
    """

    class Meta:
        db_table = "tenants_domain"
        verbose_name = "domain"
        verbose_name_plural = "domains"
