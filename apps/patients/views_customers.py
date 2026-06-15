from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from apps.rbac.permissions import HasPermission
from .models import Customer
from .serializers_customers import CustomerSerializer


class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    search_fields = ["full_name", "phone", "email"]
    ordering_fields = ["full_name", "created_at"]

    def get_queryset(self):
        return Customer.objects.all()

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), HasPermission("customers:read")]
        return [IsAuthenticated(), HasPermission("customers:write")]
