"""
Tenant service layer — provisioning and management.
"""
import structlog
from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import User, UserTenantMapping
from apps.accounts.services import AccountService

from .models import Domain, Organization

logger = structlog.get_logger(__name__)


class TenantService:

    @staticmethod
    @transaction.atomic
    def create_organization(
        *,
        name: str,
        owner: User,
        type: str,
        license_number: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
        domain_url: str = "",
    ) -> Organization:
        """
        Provision a new tenant organization.

        1. Create the Organization (django-tenants auto-creates the schema).
        2. Create a Domain for hostname routing.
        3. Create a UserTenantMapping for the owner.
        4. Seed RBAC roles/permissions in the new tenant schema.
        5. Create a TenantUser with Admin role for the owner.
        """
        slug = slugify(name)
        schema_name = slug.replace("-", "_")

        org = Organization.objects.create(
            name=name,
            slug=slug,
            schema_name=schema_name,
            type=type,
            license_number=license_number,
            phone=phone,
            email=email,
            address=address,
        )

        # Domain for tenant resolution
        domain_host = domain_url or f"{slug}.localhost"
        Domain.objects.create(
            domain=domain_host,
            tenant=org,
            is_primary=True,
        )

        # UserTenantMapping — public schema record that user belongs to this tenant
        AccountService.add_tenant_mapping(
            user=owner,
            tenant=org,
            email=owner.email,
            username=owner.username or owner.email.split("@")[0],
        )

        # Seed RBAC and create admin user in tenant schema
        from django.db import connection
        from django_tenants.utils import schema_context

        with schema_context(schema_name):
            from apps.rbac.services import RBACService, TenantUserService
            roles, _ = RBACService.seed_roles_and_permissions()
            admin_role = roles.get("Admin")
            if admin_role:
                TenantUserService.get_or_create_tenant_user(
                    user_id=owner.id,
                    email=owner.email,
                    role=admin_role,
                    first_name=owner.first_name,
                    last_name=owner.last_name,
                )

        logger.info(
            "organization_created",
            org_id=str(org.id),
            name=name,
            schema=schema_name,
            owner_id=str(owner.id),
        )
        return org

    @staticmethod
    def update_organization(org: Organization, **fields) -> Organization:
        allowed = {"name", "phone", "email", "address", "license_number", "subscription_plan"}
        update_fields = []
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(org, key, value)
                update_fields.append(key)
        if update_fields:
            org.save(update_fields=update_fields + ["updated_at"])
        return org

    @staticmethod
    def deactivate_organization(org: Organization) -> Organization:
        org.is_active = False
        org.save(update_fields=["is_active", "updated_at"])
        logger.warning("organization_deactivated", org_id=str(org.id))
        return org
