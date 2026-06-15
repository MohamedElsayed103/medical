from .models import Customer


class CustomerService:
    @staticmethod
    def get_or_create_by_phone(*, full_name: str, phone: str, email: str = "") -> Customer:
        """Reuse a walk-in by phone so repeat customers accumulate history."""
        customer, created = Customer.objects.get_or_create(
            phone=phone, defaults={"full_name": full_name, "email": email}
        )
        if not created and full_name and customer.full_name != full_name:
            customer.full_name = full_name
            customer.save(update_fields=["full_name", "updated_at"])
        return customer
