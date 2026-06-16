"""
Global cross-resource search (tenant-scoped).

GET /api/v1/search/?q=<term>  → grouped results:
  { "patients": [...], "invoices": [...], "lab_orders": [...], "radiology_orders": [...] }
Each result: { id, label, sublabel, link }.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

PER_TYPE = 5


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < 2:
            return Response({"patients": [], "invoices": [], "lab_orders": [], "radiology_orders": []})

        from django.db.models import Q
        from apps.patients.models import Patient
        from apps.billing.models import Invoice
        from apps.lab_results.models import LabOrder

        results: dict[str, list] = {}

        patients = Patient.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
            | Q(phone__icontains=q) | Q(medical_record_number__icontains=q)
        )[:PER_TYPE]
        results["patients"] = [{
            "id": str(p.id), "label": p.full_name,
            "sublabel": f"MRN {p.medical_record_number}" if p.medical_record_number else (p.phone or ""),
            "link": f"/patients/{p.id}",
        } for p in patients]

        invoices = Invoice.objects.filter(invoice_number__icontains=q).select_related("patient")[:PER_TYPE]
        results["invoices"] = [{
            "id": str(i.id), "label": i.invoice_number,
            "sublabel": f"{i.patient.full_name if i.patient_id else ''} • {i.status}",
            "link": f"/billing/{i.id}",
        } for i in invoices]

        labs = LabOrder.objects.filter(order_number__icontains=q).select_related("patient")[:PER_TYPE]
        results["lab_orders"] = [{
            "id": str(o.id), "label": o.order_number,
            "sublabel": f"{o.patient.full_name if o.patient_id else ''} • {o.status}",
            "link": f"/lab-orders/{o.id}",
        } for o in labs]

        try:
            from apps.radiology.models import RadiologyOrder
            rays = RadiologyOrder.objects.filter(order_number__icontains=q).select_related("patient")[:PER_TYPE]
            results["radiology_orders"] = [{
                "id": str(o.id), "label": o.order_number,
                "sublabel": f"{o.orderer_name} • {o.status}",
                "link": f"/radiology/{o.id}",
            } for o in rays]
        except Exception:
            results["radiology_orders"] = []

        return Response(results)
