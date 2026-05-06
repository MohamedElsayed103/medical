"""
Tenant views — organization CRUD and member management.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.accounts.models import TenantMembership, User
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.accounts.serializers import InviteMemberSerializer, TenantMembershipSerializer
from apps.accounts.services import AccountService

from .models import Organization
from .serializers import CreateOrganizationSerializer, OrganizationSerializer
from .services import TenantService


class OrganizationViewSet(GenericViewSet):
    """
    /api/v1/tenants/
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see orgs they belong to
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).distinct()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
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

    def retrieve(self, request, pk=None):
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(OrganizationSerializer(org).data)

    def partial_update(self, request, pk=None):
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Only owner/admin can update
        membership = TenantMembership.objects.filter(
            user=request.user, tenant=org, is_active=True
        ).first()
        if not membership or membership.role not in ("owner", "admin"):
            return Response(status=status.HTTP_403_FORBIDDEN)

        org = TenantService.update_organization(org, **request.data)
        return Response(OrganizationSerializer(org).data)

    @action(detail=True, methods=["post"], url_path="invite")
    def invite_member(self, request, pk=None):
        """POST /api/v1/tenants/{id}/invite/ — invite a user by email."""
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": {"code": "USER_NOT_FOUND", "message": f"No user with email {email}."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        membership = AccountService.add_member(org, user, role)
        return Response(
            TenantMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="members")
    def list_members(self, request, pk=None):
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response(status=status.HTTP_404_NOT_FOUND)
        members = TenantMembership.objects.filter(
            tenant=org, is_active=True
        ).select_related("user")
        return Response(TenantMembershipSerializer(members, many=True).data)
