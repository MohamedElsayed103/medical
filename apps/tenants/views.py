"""
Tenant views — organization CRUD.

Member management has moved to the RBAC system (apps.rbac).
These views handle only organization-level operations.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts.models import User, UserTenantMapping

from .models import Organization
from .serializers import CreateOrganizationSerializer, OrganizationSerializer
from .services import TenantService


@extend_schema_view(
    list=extend_schema(tags=["tenants"], summary="List my organizations"),
    create=extend_schema(tags=["tenants"], summary="Create organization"),
    retrieve=extend_schema(tags=["tenants"], summary="Get organization details"),
    partial_update=extend_schema(tags=["tenants"], summary="Update organization"),
)
class OrganizationViewSet(
    ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet
):
    """
    /api/v1/tenants/organizations/
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Organization.objects.none()
        # Users can only see orgs they belong to
        return Organization.objects.filter(
            user_mappings__user=self.request.user,
            user_mappings__is_deleted=False,
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrganizationSerializer
        return OrganizationSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = TenantService.create_organization(
            owner=request.user,
            **serializer.validated_data,
        )
        return Response(
            OrganizationSerializer(org).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        org = self.get_object()
        # Only users with a mapping can update
        mapping = UserTenantMapping.objects.filter(
            user=request.user, tenant=org, is_deleted=False
        ).first()
        if not mapping:
            return Response(status=status.HTTP_403_FORBIDDEN)

        org = TenantService.update_organization(org, **request.data)
        return Response(OrganizationSerializer(org).data)
