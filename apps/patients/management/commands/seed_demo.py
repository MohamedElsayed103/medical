"""
Idempotent demo-data seeder for a tenant schema.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.development \\
      venv_new/bin/python manage.py seed_demo --schema demo_clinic

Safe to run repeatedly: every object is get_or_create'd or guarded by a marker.
Seeds a baseline formulary + Mon–Fri availability for existing doctors, and
(if a patient + doctor exist) one demo visit with a linked prescription + lab
order so the Patient-360 timeline and visit "linked orders" have data to show.
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import schema_context

MEDICATIONS = [
    ("Amoxicillin", "Amoxicillin", "capsule", "500mg"),
    ("Paracetamol", "Acetaminophen", "tablet", "500mg"),
    ("Ibuprofen", "Ibuprofen", "tablet", "400mg"),
    ("Metformin", "Metformin HCl", "tablet", "850mg"),
    ("Atorvastatin", "Atorvastatin", "tablet", "20mg"),
    ("Amlodipine", "Amlodipine", "tablet", "5mg"),
    ("Salbutamol", "Albuterol", "inhaler", "100mcg"),
    ("Omeprazole", "Omeprazole", "capsule", "20mg"),
]


class Command(BaseCommand):
    help = "Seed idempotent demo data into a tenant schema."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="demo_clinic", help="Tenant schema name")

    def handle(self, *args, **opts):
        schema = opts["schema"]
        with schema_context(schema):
            self._seed(schema)

    def _seed(self, schema):
        from apps.prescriptions.models import Medication
        from apps.appointments.models import DoctorProfile, DoctorAvailability
        from apps.patients.models import Patient

        # 1) Formulary
        created_meds = 0
        for name, generic, form, strength in MEDICATIONS:
            _, created = Medication.objects.get_or_create(
                name=name, strength=strength,
                defaults={"generic_name": generic, "form": form},
            )
            created_meds += int(created)
        self.stdout.write(f"[{schema}] medications: +{created_meds} (total {Medication.objects.count()})")

        # 2) Mon–Fri 09:00–17:00 availability — ONLY for doctors with no schedule
        #    yet. Never expand a doctor who already configured their hours.
        windows_added = 0
        for doc in DoctorProfile.objects.all():
            if DoctorAvailability.objects.filter(doctor=doc).exists():
                continue
            for dow in range(5):  # Mon–Fri
                DoctorAvailability.objects.create(
                    doctor=doc, day_of_week=dow,
                    start_time=datetime.time(9, 0), end_time=datetime.time(17, 0),
                )
                windows_added += 1
        self.stdout.write(f"[{schema}] availability windows: +{windows_added}")

        # 3) One demo visit + linked prescription + lab order (guarded, best-effort)
        patient = Patient.objects.order_by("created_at").first()
        doctor = DoctorProfile.objects.first()
        if patient and doctor:
            self._seed_demo_encounter(schema, patient, doctor)
        else:
            self.stdout.write(f"[{schema}] skipped demo encounter (need ≥1 patient and ≥1 doctor)")

        self.stdout.write(self.style.SUCCESS(f"[{schema}] seed complete"))

    def _seed_demo_encounter(self, schema, patient, doctor):
        from apps.medical_records.models import Visit
        from apps.prescriptions.models import Medication, Prescription

        marker = "SEED_DEMO encounter"
        if Visit.objects.filter(patient=patient, chief_complaint=marker).exists():
            self.stdout.write(f"[{schema}] demo encounter already present")
            return

        try:
            from apps.medical_records.services import VisitService
            from apps.prescriptions.services import PrescriptionService
            from apps.lab_results.services import LabService

            visit = VisitService.create_visit(
                patient=patient, doctor=doctor, visit_date=timezone.now(),
                chief_complaint=marker, assessment="Demo encounter for showcasing linked orders.",
                plan="Start medication; order labs.",
            )
            med = Medication.objects.first()
            if med:
                PrescriptionService.create_prescription(
                    patient=patient, doctor=doctor, visit=visit, notes="Demo prescription",
                    items=[{
                        "medication_id": str(med.id), "dosage": "1 tab", "frequency": "twice daily",
                        "duration": "7 days", "quantity": 14, "route": "oral",
                    }],
                )
            LabService.create_order(
                patient=patient, doctor=doctor, visit=visit, priority="routine",
                clinical_notes="Demo lab order",
                tests=[{"test_name": "Complete Blood Count"}, {"test_name": "Fasting Glucose"}],
            )
            self.stdout.write(f"[{schema}] created demo encounter (visit {visit.id})")
        except Exception as e:  # don't let signature drift abort the whole seed
            self.stdout.write(self.style.WARNING(f"[{schema}] demo encounter skipped: {e}"))
