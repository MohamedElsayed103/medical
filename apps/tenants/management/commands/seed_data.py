"""
Management command to seed the database with comprehensive test data.

Creates: tenant, users, doctors, patients, appointments, visits, prescriptions,
lab orders, invoices, pharmacy inventory, insurance, notifications.

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush  (wipe and re-seed)
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Seed the database with comprehensive test data for all modules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing seed data before re-seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Seeding MedFlow Pro Database ==="))

        # Step 1: Create tenant (organization)
        tenant = self._ensure_tenant()

        # Step 2: Create platform users (public schema)
        users = self._create_users()

        # Step 3: Seed tenant-scoped data
        with schema_context(tenant.schema_name):
            roles = self._create_roles()
            tenant_users = self._create_tenant_users(users, roles)
            doctors = self._create_doctor_profiles(users)
            patients = self._create_patients()
            appointments = self._create_appointments(patients, doctors)
            visits = self._create_visits(patients, doctors, appointments)
            medications = self._create_medications()
            self._create_prescriptions(patients, doctors, visits, medications)
            self._create_lab_orders(patients, doctors, visits)
            self._create_invoices(patients)
            self._create_pharmacy_inventory(medications)
            self._create_insurance(patients)
            self._create_notifications(tenant_users)

        self.stdout.write(self.style.SUCCESS("\n✅ All seed data created successfully!"))
        self.stdout.write(self.style.SUCCESS("   Login: admin@clinic.com / SecurePass123!"))

    def _ensure_tenant(self):
        from apps.tenants.models import Domain, Organization

        self.stdout.write("  Creating tenant...")
        tenant, created = Organization.objects.get_or_create(
            slug="demo-clinic",
            defaults={
                "name": "Demo Medical Clinic",
                "schema_name": "demo_clinic",
                "type": "clinic",
                "license_number": "MC-2024-001",
                "address": "123 Healthcare Ave, Medical City, MC 12345",
                "phone": "+1-555-0100",
                "email": "info@democlinic.com",
                "is_active": True,
                "subscription_plan": "pro",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"    ✓ Tenant '{tenant.name}' created"))
        else:
            self.stdout.write(f"    • Tenant '{tenant.name}' already exists")

        # Ensure domain mapping exists
        Domain.objects.get_or_create(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
        return tenant

    def _create_users(self):
        from apps.accounts.models import User, UserTenantMapping
        from apps.tenants.models import Organization

        self.stdout.write("  Creating users...")
        tenant = Organization.objects.get(slug="demo-clinic")

        user_data = [
            {
                "email": "admin@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Admin",
                "last_name": "User",
                "display_name": "Admin User",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "dr.ahmed@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Ahmed",
                "last_name": "Hassan",
                "display_name": "Dr. Ahmed Hassan",
            },
            {
                "email": "dr.sarah@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "display_name": "Dr. Sarah Johnson",
            },
            {
                "email": "dr.omar@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Omar",
                "last_name": "Ali",
                "display_name": "Dr. Omar Ali",
            },
            {
                "email": "dr.fatima@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Fatima",
                "last_name": "Khalil",
                "display_name": "Dr. Fatima Khalil",
            },
            {
                "email": "nurse.mary@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Mary",
                "last_name": "Williams",
                "display_name": "Mary Williams",
            },
            {
                "email": "nurse.john@clinic.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Smith",
                "display_name": "John Smith",
            },
            {
                "email": "reception@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Lisa",
                "last_name": "Brown",
                "display_name": "Lisa Brown",
            },
            {
                "email": "lab.tech@clinic.com",
                "password": "SecurePass123!",
                "first_name": "David",
                "last_name": "Chen",
                "display_name": "David Chen",
            },
            {
                "email": "pharmacist@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Aisha",
                "last_name": "Mohamed",
                "display_name": "Aisha Mohamed",
            },
            {
                "email": "billing@clinic.com",
                "password": "SecurePass123!",
                "first_name": "Robert",
                "last_name": "Taylor",
                "display_name": "Robert Taylor",
            },
        ]

        users = {}
        for data in user_data:
            password = data.pop("password")
            email = data["email"]
            user, created = User.objects.get_or_create(
                email=email,
                defaults=data,
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"    ✓ User: {email}"))
            else:
                self.stdout.write(f"    • User: {email} (exists)")
            users[email] = user

            # Ensure tenant mapping
            UserTenantMapping.objects.get_or_create(
                user=user,
                tenant=tenant,
                defaults={"email": email, "username": email.split("@")[0]},
            )

        return users

    def _create_roles(self):
        from apps.rbac.models import Permission, Role, RolePermission

        self.stdout.write("  Creating roles & permissions...")

        # Create permissions
        resources = [
            "patients", "appointments", "visits", "prescriptions",
            "lab_orders", "billing", "pharmacy", "insurance",
            "users", "roles", "notifications", "audit", "ai",
            "settings", "reports",
        ]
        actions = ["read", "write", "delete", "export"]

        permissions = {}
        for resource in resources:
            for action in actions:
                name = f"{resource}:{action}"
                perm, _ = Permission.objects.get_or_create(
                    name=name,
                    defaults={"resource": resource, "description": f"{action.title()} {resource}"},
                )
                permissions[name] = perm

        # Create roles
        role_configs = [
            {
                "name": "Admin",
                "description": "Full system access",
                "is_system": True,
                "permissions": [f"{r}:{a}" for r in resources for a in actions],
            },
            {
                "name": "Doctor",
                "description": "Clinical access - patients, visits, prescriptions, labs",
                "is_system": True,
                "permissions": [
                    f"{r}:{a}" for r in ["patients", "appointments", "visits", "prescriptions", "lab_orders", "notifications"]
                    for a in ["read", "write"]
                ] + ["billing:read", "pharmacy:read", "insurance:read", "ai:read", "ai:write"],
            },
            {
                "name": "Nurse",
                "description": "Clinical support - vitals, patient care",
                "is_system": True,
                "permissions": [
                    "patients:read", "patients:write", "appointments:read", "appointments:write",
                    "visits:read", "visits:write", "prescriptions:read", "lab_orders:read",
                    "notifications:read", "notifications:write",
                ],
            },
            {
                "name": "Receptionist",
                "description": "Front desk - appointments, basic patient info",
                "is_system": True,
                "permissions": [
                    "patients:read", "patients:write", "appointments:read", "appointments:write",
                    "billing:read", "notifications:read",
                ],
            },
            {
                "name": "Lab Technician",
                "description": "Lab operations - orders, results",
                "is_system": True,
                "permissions": [
                    "patients:read", "lab_orders:read", "lab_orders:write",
                    "notifications:read", "notifications:write",
                ],
            },
            {
                "name": "Pharmacist",
                "description": "Pharmacy operations - inventory, dispensing",
                "is_system": True,
                "permissions": [
                    "patients:read", "prescriptions:read", "pharmacy:read", "pharmacy:write",
                    "notifications:read",
                ],
            },
            {
                "name": "Billing Staff",
                "description": "Financial operations - invoices, payments, insurance",
                "is_system": True,
                "permissions": [
                    "patients:read", "billing:read", "billing:write", "billing:export",
                    "insurance:read", "insurance:write", "notifications:read",
                ],
            },
        ]

        roles = {}
        for config in role_configs:
            perms = config.pop("permissions")
            role, created = Role.objects.get_or_create(
                name=config["name"],
                defaults=config,
            )
            roles[config["name"]] = role

            if created:
                for perm_name in perms:
                    if perm_name in permissions:
                        RolePermission.objects.get_or_create(
                            role=role, permission=permissions[perm_name]
                        )
                self.stdout.write(self.style.SUCCESS(f"    ✓ Role: {role.name} ({len(perms)} permissions)"))
            else:
                self.stdout.write(f"    • Role: {role.name} (exists)")

        return roles

    def _create_tenant_users(self, users, roles):
        from apps.rbac.models import TenantUser

        self.stdout.write("  Creating tenant users...")

        mappings = [
            ("admin@clinic.com", "Admin", "General Practice", "ADM-001", "MD"),
            ("dr.ahmed@clinic.com", "Doctor", "Cardiology", "DOC-001", "MD, FACC"),
            ("dr.sarah@clinic.com", "Doctor", "Pediatrics", "DOC-002", "MD, FAAP"),
            ("dr.omar@clinic.com", "Doctor", "Orthopedics", "DOC-003", "MD, FAAOS"),
            ("dr.fatima@clinic.com", "Doctor", "Dermatology", "DOC-004", "MD, FAAD"),
            ("nurse.mary@clinic.com", "Nurse", "Emergency Care", "NRS-001", "RN, BSN"),
            ("nurse.john@clinic.com", "Nurse", "Surgical", "NRS-002", "RN"),
            ("reception@clinic.com", "Receptionist", "", "REC-001", ""),
            ("lab.tech@clinic.com", "Lab Technician", "Clinical Chemistry", "LAB-001", "MLT"),
            ("pharmacist@clinic.com", "Pharmacist", "Clinical Pharmacy", "PHR-001", "PharmD"),
            ("billing@clinic.com", "Billing Staff", "", "BIL-001", ""),
        ]

        tenant_users = {}
        for email, role_name, specialty, license_num, qualification in mappings:
            user = users[email]
            tu, created = TenantUser.objects.get_or_create(
                user_id=user.id,
                defaults={
                    "email": email,
                    "username": email.split("@")[0],
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "display_name": user.display_name,
                    "role": roles[role_name],
                    "specialty": specialty,
                    "license_number": license_num,
                    "qualification": qualification,
                    "status": "ACTIVE",
                },
            )
            tenant_users[email] = tu
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ TenantUser: {user.display_name} [{role_name}]"))

        return tenant_users

    def _create_doctor_profiles(self, users):
        from apps.appointments.models import DoctorProfile

        self.stdout.write("  Creating doctor profiles...")

        doctor_data = [
            {
                "user": users["dr.ahmed@clinic.com"],
                "specialization": "Cardiology",
                "license_number": "DOC-001",
                "qualification": "MD, FACC - Fellowship in Interventional Cardiology",
                "years_of_experience": 15,
                "consultation_fee": Decimal("200.00"),
                "bio": "Board-certified cardiologist with 15 years of experience in interventional cardiology and heart failure management.",
                "is_available": True,
            },
            {
                "user": users["dr.sarah@clinic.com"],
                "specialization": "Pediatrics",
                "license_number": "DOC-002",
                "qualification": "MD, FAAP - Pediatric Emergency Medicine",
                "years_of_experience": 10,
                "consultation_fee": Decimal("150.00"),
                "bio": "Pediatrician specializing in emergency medicine and developmental pediatrics.",
                "is_available": True,
            },
            {
                "user": users["dr.omar@clinic.com"],
                "specialization": "Orthopedics",
                "license_number": "DOC-003",
                "qualification": "MD, FAAOS - Sports Medicine",
                "years_of_experience": 12,
                "consultation_fee": Decimal("250.00"),
                "bio": "Orthopedic surgeon specializing in sports injuries, joint replacements, and minimally invasive procedures.",
                "is_available": True,
            },
            {
                "user": users["dr.fatima@clinic.com"],
                "specialization": "Dermatology",
                "license_number": "DOC-004",
                "qualification": "MD, FAAD - Cosmetic Dermatology",
                "years_of_experience": 8,
                "consultation_fee": Decimal("180.00"),
                "bio": "Dermatologist with expertise in medical and cosmetic dermatology, laser treatments, and skin cancer screening.",
                "is_available": True,
            },
        ]

        doctors = {}
        for data in doctor_data:
            user = data.pop("user")
            doc, created = DoctorProfile.objects.get_or_create(
                user_id=user.id,
                defaults=data,
            )
            doctors[user.email] = doc
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ Dr. {user.first_name} {user.last_name} - {data['specialization']}"))

        return doctors

    def _create_patients(self):
        from apps.patients.models import Patient
        from common.utils import generate_mrn

        self.stdout.write("  Creating patients...")

        patient_data = [
            {
                "first_name": "Mohamed",
                "last_name": "Ibrahim",
                "date_of_birth": date(1985, 3, 15),
                "gender": "male",
                "phone": "+1-555-0201",
                "email": "mohamed.i@email.com",
                "blood_type": "A+",
                "address": "45 Palm Street, Medical City, MC 12345",
                "emergency_contact_name": "Hana Ibrahim",
                "emergency_contact_phone": "+1-555-0202",
                "allergies": ["Penicillin", "Sulfa drugs"],
                "chronic_conditions": ["Hypertension", "Type 2 Diabetes"],
                "insurance_provider": "BlueCross",
                "insurance_number": "BC-123456",
            },
            {
                "first_name": "Layla",
                "last_name": "Ahmed",
                "date_of_birth": date(1990, 7, 22),
                "gender": "female",
                "phone": "+1-555-0203",
                "email": "layla.ahmed@email.com",
                "blood_type": "O+",
                "address": "78 Oak Lane, Medical City, MC 12346",
                "emergency_contact_name": "Khaled Ahmed",
                "emergency_contact_phone": "+1-555-0204",
                "allergies": ["Latex"],
                "chronic_conditions": ["Asthma"],
                "insurance_provider": "Aetna",
                "insurance_number": "AE-789012",
            },
            {
                "first_name": "James",
                "last_name": "Wilson",
                "date_of_birth": date(1978, 11, 3),
                "gender": "male",
                "phone": "+1-555-0205",
                "email": "james.wilson@email.com",
                "blood_type": "B+",
                "address": "234 Elm Drive, Medical City, MC 12347",
                "emergency_contact_name": "Patricia Wilson",
                "emergency_contact_phone": "+1-555-0206",
                "allergies": [],
                "chronic_conditions": ["Chronic Back Pain", "Osteoarthritis"],
                "insurance_provider": "UnitedHealth",
                "insurance_number": "UH-345678",
            },
            {
                "first_name": "Amira",
                "last_name": "Said",
                "date_of_birth": date(1995, 5, 18),
                "gender": "female",
                "phone": "+1-555-0207",
                "email": "amira.said@email.com",
                "blood_type": "AB+",
                "address": "56 Maple Court, Medical City, MC 12348",
                "emergency_contact_name": "Youssef Said",
                "emergency_contact_phone": "+1-555-0208",
                "allergies": ["Aspirin", "Ibuprofen"],
                "chronic_conditions": [],
                "insurance_provider": "Cigna",
                "insurance_number": "CG-901234",
            },
            {
                "first_name": "William",
                "last_name": "Anderson",
                "date_of_birth": date(1962, 9, 30),
                "gender": "male",
                "phone": "+1-555-0209",
                "email": "w.anderson@email.com",
                "blood_type": "O-",
                "address": "890 Cedar Blvd, Medical City, MC 12349",
                "emergency_contact_name": "Margaret Anderson",
                "emergency_contact_phone": "+1-555-0210",
                "allergies": ["Codeine"],
                "chronic_conditions": ["Coronary Artery Disease", "Hyperlipidemia", "Hypertension"],
                "insurance_provider": "Medicare",
                "insurance_number": "MC-567890",
            },
            {
                "first_name": "Nour",
                "last_name": "Hassan",
                "date_of_birth": date(2018, 1, 10),
                "gender": "female",
                "phone": "+1-555-0211",
                "email": "nour.parent@email.com",
                "blood_type": "A-",
                "address": "12 Rose Street, Medical City, MC 12350",
                "emergency_contact_name": "Hassan Family",
                "emergency_contact_phone": "+1-555-0212",
                "allergies": ["Eggs"],
                "chronic_conditions": [],
                "insurance_provider": "BlueCross",
                "insurance_number": "BC-111222",
            },
            {
                "first_name": "Catherine",
                "last_name": "Lee",
                "date_of_birth": date(1988, 4, 25),
                "gender": "female",
                "phone": "+1-555-0213",
                "email": "catherine.lee@email.com",
                "blood_type": "B-",
                "address": "67 Birch Avenue, Medical City, MC 12351",
                "emergency_contact_name": "David Lee",
                "emergency_contact_phone": "+1-555-0214",
                "allergies": [],
                "chronic_conditions": ["Eczema", "Seasonal Allergies"],
                "insurance_provider": "Aetna",
                "insurance_number": "AE-333444",
            },
            {
                "first_name": "Ali",
                "last_name": "Mahmoud",
                "date_of_birth": date(1972, 8, 14),
                "gender": "male",
                "phone": "+1-555-0215",
                "email": "ali.mahmoud@email.com",
                "blood_type": "A+",
                "address": "345 Pine Road, Medical City, MC 12352",
                "emergency_contact_name": "Fatima Mahmoud",
                "emergency_contact_phone": "+1-555-0216",
                "allergies": ["Shellfish"],
                "chronic_conditions": ["GERD", "Anxiety"],
                "insurance_provider": "UnitedHealth",
                "insurance_number": "UH-555666",
            },
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "date_of_birth": date(2000, 12, 5),
                "gender": "female",
                "phone": "+1-555-0217",
                "email": "emily.davis@email.com",
                "blood_type": "O+",
                "address": "89 Willow Lane, Medical City, MC 12353",
                "emergency_contact_name": "Richard Davis",
                "emergency_contact_phone": "+1-555-0218",
                "allergies": [],
                "chronic_conditions": [],
                "insurance_provider": "Cigna",
                "insurance_number": "CG-777888",
            },
            {
                "first_name": "Youssef",
                "last_name": "Bakr",
                "date_of_birth": date(1955, 6, 20),
                "gender": "male",
                "phone": "+1-555-0219",
                "email": "youssef.bakr@email.com",
                "blood_type": "AB-",
                "address": "123 Walnut Drive, Medical City, MC 12354",
                "emergency_contact_name": "Mariam Bakr",
                "emergency_contact_phone": "+1-555-0220",
                "allergies": ["Metformin"],
                "chronic_conditions": ["Type 2 Diabetes", "Peripheral Neuropathy", "CKD Stage 3"],
                "insurance_provider": "Medicare",
                "insurance_number": "MC-999000",
            },
        ]

        patients = []
        for data in patient_data:
            patient, created = Patient.objects.get_or_create(
                email=data["email"],
                defaults={**data, "medical_record_number": generate_mrn()},
            )
            patients.append(patient)
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ Patient: {patient.full_name}"))

        return patients

    def _create_appointments(self, patients, doctors):
        from apps.appointments.models import Appointment

        self.stdout.write("  Creating appointments...")

        now = timezone.now()
        doctor_list = list(doctors.values())
        appointments = []

        appt_data = [
            # Past completed appointments
            (patients[0], doctor_list[0], now - timedelta(days=30), "completed", "Follow-up for hypertension"),
            (patients[1], doctor_list[1], now - timedelta(days=25), "completed", "Annual checkup for child"),
            (patients[2], doctor_list[2], now - timedelta(days=20), "completed", "Knee pain evaluation"),
            (patients[3], doctor_list[3], now - timedelta(days=15), "completed", "Skin rash evaluation"),
            (patients[4], doctor_list[0], now - timedelta(days=10), "completed", "Cardiac follow-up"),
            (patients[5], doctor_list[1], now - timedelta(days=7), "completed", "Vaccination appointment"),
            # Today's appointments
            (patients[0], doctor_list[0], now.replace(hour=9, minute=0), "confirmed", "Blood pressure review"),
            (patients[6], doctor_list[3], now.replace(hour=9, minute=30), "confirmed", "Eczema follow-up"),
            (patients[7], doctor_list[0], now.replace(hour=10, minute=0), "in_progress", "Anxiety management"),
            (patients[8], doctor_list[1], now.replace(hour=10, minute=30), "scheduled", "General checkup"),
            (patients[9], doctor_list[0], now.replace(hour=11, minute=0), "scheduled", "Diabetes management"),
            # Future appointments
            (patients[1], doctor_list[1], now + timedelta(days=3), "scheduled", "Follow-up visit"),
            (patients[2], doctor_list[2], now + timedelta(days=5), "scheduled", "Post-surgery check"),
            (patients[3], doctor_list[3], now + timedelta(days=7), "confirmed", "Dermatology review"),
            (patients[4], doctor_list[0], now + timedelta(days=10), "scheduled", "Stress test"),
            (patients[0], doctor_list[0], now + timedelta(days=14), "scheduled", "Monthly BP check"),
        ]

        for patient, doctor, scheduled, status, reason in appt_data:
            appt, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                scheduled_at=scheduled,
                defaults={
                    "status": status,
                    "type": "in_person",
                    "reason": reason,
                    "duration_minutes": 30,
                },
            )
            appointments.append(appt)
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ Appt: {patient.first_name} → Dr.{doctor.specialization} ({status})"))

        return appointments

    def _create_visits(self, patients, doctors, appointments):
        from apps.medical_records.models import Diagnosis, Visit, Vitals

        self.stdout.write("  Creating visits & medical records...")

        now = timezone.now()
        doctor_list = list(doctors.values())
        visits = []

        visit_data = [
            {
                "patient": patients[0],
                "doctor": doctor_list[0],
                "appointment": appointments[0],
                "visit_date": now - timedelta(days=30),
                "chief_complaint": "Elevated blood pressure readings at home",
                "history_of_present_illness": "Patient reports BP readings of 150/95 mmHg over the past week. Taking Lisinopril 10mg daily. No chest pain, headaches, or visual changes.",
                "examination_notes": "Alert, oriented. Heart: RRR, no murmurs. Lungs: Clear bilateral. Extremities: No edema.",
                "assessment": "Uncontrolled essential hypertension despite current medication regimen.",
                "plan": "Increase Lisinopril to 20mg daily. Add Amlodipine 5mg daily. Recheck in 2 weeks. Low sodium diet counseling.",
                "is_signed": True,
                "vitals": {"bp_sys": 152, "bp_dia": 96, "hr": 78, "temp": 36.8, "rr": 16, "o2": 98, "weight": 85.5, "height": 175},
                "diagnoses": [("I10", "Essential hypertension", "primary")],
            },
            {
                "patient": patients[1],
                "doctor": doctor_list[1],
                "appointment": appointments[1],
                "visit_date": now - timedelta(days=25),
                "chief_complaint": "Annual wellness exam for 6-year-old",
                "history_of_present_illness": "Routine checkup. No concerns from parents. Developmentally appropriate. Immunizations up to date.",
                "examination_notes": "Well-nourished child. HEENT: Normal. Heart: RRR. Lungs: Clear. Abdomen: Soft, non-tender. Growth parameters: 50th percentile height and weight.",
                "assessment": "Healthy child, normal development for age.",
                "plan": "Continue routine care. Next wellness check in 1 year. Flu vaccine administered today.",
                "is_signed": True,
                "vitals": {"bp_sys": 95, "bp_dia": 60, "hr": 90, "temp": 36.6, "rr": 20, "o2": 99, "weight": 22, "height": 118},
                "diagnoses": [("Z00.129", "Well child visit", "primary")],
            },
            {
                "patient": patients[2],
                "doctor": doctor_list[2],
                "appointment": appointments[2],
                "visit_date": now - timedelta(days=20),
                "chief_complaint": "Right knee pain and swelling for 2 weeks",
                "history_of_present_illness": "Patient reports increasing right knee pain worse with stairs and prolonged standing. History of meniscus tear 5 years ago. No locking or giving way.",
                "examination_notes": "Right knee: Mild effusion, tenderness along medial joint line. ROM: 0-120 degrees. Negative McMurray test. Stable ligaments. No warmth or erythema.",
                "assessment": "Right knee osteoarthritis, mild-moderate. Possible medial meniscus degeneration.",
                "plan": "X-ray right knee. Physical therapy 2x/week for 6 weeks. Naproxen 500mg BID with food. Ice and elevation. Consider MRI if no improvement in 4 weeks.",
                "is_signed": True,
                "vitals": {"bp_sys": 128, "bp_dia": 82, "hr": 72, "temp": 36.7, "rr": 14, "o2": 98, "weight": 92, "height": 180},
                "diagnoses": [("M17.11", "Primary osteoarthritis, right knee", "primary"), ("M23.21", "Derangement of medial meniscus", "secondary")],
            },
            {
                "patient": patients[4],
                "doctor": doctor_list[0],
                "appointment": appointments[4],
                "visit_date": now - timedelta(days=10),
                "chief_complaint": "Cardiac follow-up, shortness of breath on exertion",
                "history_of_present_illness": "Patient with known CAD status post stent placement 6 months ago. Reports mild DOE when climbing stairs. No chest pain, palpitations, or orthopnea. Compliant with medications.",
                "examination_notes": "Heart: RRR, Grade I/VI systolic murmur at apex. JVP not elevated. Lungs: Clear. Peripheral pulses intact. No peripheral edema.",
                "assessment": "Stable CAD post-PCI. Mild deconditioning contributing to DOE. LDL at target.",
                "plan": "Continue current medications (Aspirin, Clopidogrel, Atorvastatin, Metoprolol). Cardiac rehabilitation referral. Echocardiogram in 3 months. Continue low-fat diet.",
                "is_signed": True,
                "vitals": {"bp_sys": 135, "bp_dia": 80, "hr": 68, "temp": 36.6, "rr": 16, "o2": 96, "weight": 88, "height": 172},
                "diagnoses": [("I25.10", "Atherosclerotic heart disease", "primary"), ("R06.00", "Dyspnea on exertion", "secondary")],
            },
            {
                "patient": patients[3],
                "doctor": doctor_list[3],
                "appointment": appointments[3],
                "visit_date": now - timedelta(days=15),
                "chief_complaint": "Itchy red rash on arms and torso for 1 week",
                "history_of_present_illness": "Patient developed pruritic erythematous papular rash on bilateral forearms and trunk 7 days ago. No new medications, detergents, or known exposures. History of seasonal allergies.",
                "examination_notes": "Multiple erythematous, raised papules on bilateral forearms, trunk. No vesicles, no facial involvement. No lymphadenopathy.",
                "assessment": "Contact dermatitis vs allergic reaction. No signs of systemic involvement.",
                "plan": "Triamcinolone 0.1% cream BID x 2 weeks. Cetirizine 10mg daily for pruritus. Avoid known irritants. Return if worsening or no improvement in 1 week.",
                "is_signed": True,
                "vitals": {"bp_sys": 118, "bp_dia": 72, "hr": 76, "temp": 36.9, "rr": 14, "o2": 99, "weight": 62, "height": 165},
                "diagnoses": [("L23.9", "Allergic contact dermatitis, unspecified", "primary")],
            },
        ]

        for data in visit_data:
            visit, created = Visit.objects.get_or_create(
                patient=data["patient"],
                doctor=data["doctor"],
                visit_date=data["visit_date"],
                defaults={
                    "appointment": data.get("appointment"),
                    "chief_complaint": data["chief_complaint"],
                    "history_of_present_illness": data["history_of_present_illness"],
                    "examination_notes": data["examination_notes"],
                    "assessment": data["assessment"],
                    "plan": data["plan"],
                    "is_signed": data["is_signed"],
                    "signed_at": data["visit_date"] + timedelta(hours=1) if data["is_signed"] else None,
                },
            )
            visits.append(visit)

            if created:
                # Create vitals
                v = data["vitals"]
                Vitals.objects.create(
                    visit=visit,
                    blood_pressure_systolic=v["bp_sys"],
                    blood_pressure_diastolic=v["bp_dia"],
                    heart_rate=v["hr"],
                    temperature=Decimal(str(v["temp"])),
                    respiratory_rate=v["rr"],
                    oxygen_saturation=Decimal(str(v["o2"])),
                    weight_kg=Decimal(str(v["weight"])),
                    height_cm=Decimal(str(v["height"])),
                    recorded_by_id=data["doctor"].user_id,
                )

                # Create diagnoses
                for icd, desc, dtype in data["diagnoses"]:
                    Diagnosis.objects.create(
                        visit=visit,
                        icd_code=icd,
                        description=desc,
                        type=dtype,
                    )

                self.stdout.write(self.style.SUCCESS(f"    ✓ Visit: {data['patient'].first_name} - {data['chief_complaint'][:40]}"))

        return visits

    def _create_medications(self):
        from apps.prescriptions.models import Medication

        self.stdout.write("  Creating medications...")

        med_data = [
            ("Lisinopril", "Lisinopril", "tablet", "10mg", "Pfizer"),
            ("Lisinopril 20mg", "Lisinopril", "tablet", "20mg", "Pfizer"),
            ("Amlodipine", "Amlodipine", "tablet", "5mg", "Novartis"),
            ("Metformin", "Metformin HCl", "tablet", "500mg", "Merck"),
            ("Metformin 1000mg", "Metformin HCl", "tablet", "1000mg", "Merck"),
            ("Atorvastatin", "Atorvastatin", "tablet", "20mg", "Pfizer"),
            ("Aspirin", "Acetylsalicylic Acid", "tablet", "81mg", "Bayer"),
            ("Metoprolol", "Metoprolol Tartrate", "tablet", "50mg", "AstraZeneca"),
            ("Naproxen", "Naproxen Sodium", "tablet", "500mg", "Roche"),
            ("Cetirizine", "Cetirizine HCl", "tablet", "10mg", "Johnson & Johnson"),
            ("Triamcinolone Cream", "Triamcinolone Acetonide", "cream", "0.1%", "Perrigo"),
            ("Amoxicillin", "Amoxicillin", "capsule", "500mg", "GSK"),
            ("Azithromycin", "Azithromycin", "tablet", "250mg", "Pfizer"),
            ("Omeprazole", "Omeprazole", "capsule", "20mg", "AstraZeneca"),
            ("Salbutamol Inhaler", "Salbutamol", "inhaler", "100mcg", "GSK"),
            ("Insulin Glargine", "Insulin Glargine", "injection", "100U/mL", "Sanofi"),
            ("Clopidogrel", "Clopidogrel", "tablet", "75mg", "Sanofi"),
            ("Ibuprofen", "Ibuprofen", "tablet", "400mg", "Advil"),
            ("Paracetamol", "Acetaminophen", "tablet", "500mg", "Johnson & Johnson"),
            ("Ciprofloxacin", "Ciprofloxacin HCl", "tablet", "500mg", "Bayer"),
        ]

        medications = []
        for name, generic, form, strength, mfr in med_data:
            med, created = Medication.objects.get_or_create(
                name=name,
                defaults={
                    "generic_name": generic,
                    "form": form,
                    "strength": strength,
                    "manufacturer": mfr,
                    "is_active": True,
                },
            )
            medications.append(med)
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ Med: {name} {strength}"))

        return medications

    def _create_prescriptions(self, patients, doctors, visits, medications):
        from apps.prescriptions.models import Prescription, PrescriptionItem

        self.stdout.write("  Creating prescriptions...")

        doctor_list = list(doctors.values())

        rx_data = [
            {
                "patient": patients[0],
                "doctor": doctor_list[0],
                "visit": visits[0] if visits else None,
                "notes": "Hypertension management - dose adjustment",
                "items": [
                    (medications[1], "20mg", "Once daily", "Ongoing", "oral", 30, "Take in the morning"),
                    (medications[2], "5mg", "Once daily", "Ongoing", "oral", 30, "Take in the evening"),
                ],
            },
            {
                "patient": patients[2],
                "doctor": doctor_list[2],
                "visit": visits[2] if len(visits) > 2 else None,
                "notes": "Knee osteoarthritis pain management",
                "items": [
                    (medications[8], "500mg", "Twice daily", "14 days", "oral", 28, "Take with food"),
                ],
            },
            {
                "patient": patients[3],
                "doctor": doctor_list[3],
                "visit": visits[4] if len(visits) > 4 else None,
                "notes": "Contact dermatitis treatment",
                "items": [
                    (medications[10], "Apply thin layer", "Twice daily", "14 days", "topical", 1, "Apply to affected areas only"),
                    (medications[9], "10mg", "Once daily", "14 days", "oral", 14, "For itching relief"),
                ],
            },
            {
                "patient": patients[4],
                "doctor": doctor_list[0],
                "visit": visits[3] if len(visits) > 3 else None,
                "notes": "Post-PCI maintenance therapy",
                "items": [
                    (medications[6], "81mg", "Once daily", "Indefinite", "oral", 90, "Do not stop without consulting doctor"),
                    (medications[16], "75mg", "Once daily", "12 months", "oral", 30, "Take with food"),
                    (medications[5], "20mg", "Once daily", "Indefinite", "oral", 30, "Take at bedtime"),
                    (medications[7], "50mg", "Twice daily", "Indefinite", "oral", 60, "Do not stop abruptly"),
                ],
            },
            {
                "patient": patients[9],
                "doctor": doctor_list[0],
                "visit": None,
                "notes": "Diabetes management",
                "items": [
                    (medications[3], "500mg", "Twice daily", "Ongoing", "oral", 60, "Take with meals"),
                    (medications[15], "100U/mL", "10 units at bedtime", "Ongoing", "subcutaneous", 1, "Inject subcutaneously, rotate sites"),
                ],
            },
        ]

        for data in rx_data:
            rx, created = Prescription.objects.get_or_create(
                patient=data["patient"],
                doctor=data["doctor"],
                visit=data["visit"],
                defaults={"notes": data["notes"]},
            )
            if created:
                for med, dosage, freq, duration, route, qty, instr in data["items"]:
                    PrescriptionItem.objects.create(
                        prescription=rx,
                        medication=med,
                        dosage=dosage,
                        frequency=freq,
                        duration=duration,
                        route=route,
                        quantity=qty,
                        instructions=instr,
                    )
                self.stdout.write(self.style.SUCCESS(f"    ✓ Rx: {data['patient'].first_name} ({len(data['items'])} meds)"))

    def _create_lab_orders(self, patients, doctors, visits):
        from apps.lab_results.models import LabOrder, LabTest, TestResult
        from common.utils import generate_invoice_number

        self.stdout.write("  Creating lab orders & results...")

        now = timezone.now()
        doctor_list = list(doctors.values())

        order_data = [
            {
                "patient": patients[0],
                "doctor": doctor_list[0],
                "visit": visits[0] if visits else None,
                "status": "completed",
                "priority": "routine",
                "clinical_notes": "Monitor renal function and electrolytes on ACE inhibitor",
                "tests": [
                    ("Complete Blood Count", "CBC", "Blood", "14.2", "g/dL", 12, 17.5, "normal"),
                    ("Creatinine", "CHEM-CR", "Blood", "1.1", "mg/dL", 0.7, 1.3, "normal"),
                    ("Potassium", "CHEM-K", "Blood", "4.8", "mEq/L", 3.5, 5.0, "normal"),
                    ("HbA1c", "HBA1C", "Blood", "7.2", "%", 4.0, 5.7, "high"),
                    ("Fasting Glucose", "GLUC", "Blood", "142", "mg/dL", 70, 100, "high"),
                ],
            },
            {
                "patient": patients[4],
                "doctor": doctor_list[0],
                "visit": visits[3] if len(visits) > 3 else None,
                "status": "completed",
                "priority": "routine",
                "clinical_notes": "Cardiac panel and lipids post-PCI",
                "tests": [
                    ("Total Cholesterol", "CHOL", "Blood", "185", "mg/dL", 0, 200, "normal"),
                    ("LDL Cholesterol", "LDL", "Blood", "68", "mg/dL", 0, 100, "normal"),
                    ("HDL Cholesterol", "HDL", "Blood", "52", "mg/dL", 40, 60, "normal"),
                    ("Triglycerides", "TG", "Blood", "145", "mg/dL", 0, 150, "normal"),
                    ("Troponin I", "TROP", "Blood", "0.02", "ng/mL", 0, 0.04, "normal"),
                    ("BNP", "BNP", "Blood", "89", "pg/mL", 0, 100, "normal"),
                ],
            },
            {
                "patient": patients[9],
                "doctor": doctor_list[0],
                "visit": None,
                "status": "completed",
                "priority": "urgent",
                "clinical_notes": "Diabetes monitoring - suspected renal decline",
                "tests": [
                    ("HbA1c", "HBA1C", "Blood", "8.9", "%", 4.0, 5.7, "high"),
                    ("Creatinine", "CHEM-CR", "Blood", "1.8", "mg/dL", 0.7, 1.3, "high"),
                    ("eGFR", "EGFR", "Blood", "42", "mL/min", 60, 120, "low"),
                    ("Urine Albumin/Creatinine", "UACR", "Urine", "85", "mg/g", 0, 30, "high"),
                    ("Potassium", "CHEM-K", "Blood", "5.4", "mEq/L", 3.5, 5.0, "high"),
                ],
            },
            {
                "patient": patients[1],
                "doctor": doctor_list[1],
                "visit": visits[1] if len(visits) > 1 else None,
                "status": "processing",
                "priority": "routine",
                "clinical_notes": "Routine blood work for well child visit",
                "tests": [
                    ("Complete Blood Count", "CBC", "Blood", None, None, None, None, None),
                    ("Iron Studies", "FE", "Blood", None, None, None, None, None),
                ],
            },
            {
                "patient": patients[7],
                "doctor": doctor_list[0],
                "visit": None,
                "status": "ordered",
                "priority": "routine",
                "clinical_notes": "Anxiety workup - thyroid function",
                "tests": [
                    ("TSH", "TSH", "Blood", None, None, None, None, None),
                    ("Free T4", "FT4", "Blood", None, None, None, None, None),
                    ("Cortisol (AM)", "CORT", "Blood", None, None, None, None, None),
                ],
            },
        ]

        for data in order_data:
            order_num = f"LAB-{uuid.uuid4().hex[:8].upper()}"
            order, created = LabOrder.objects.get_or_create(
                patient=data["patient"],
                doctor=data["doctor"],
                clinical_notes=data["clinical_notes"],
                defaults={
                    "visit": data["visit"],
                    "order_number": order_num,
                    "status": data["status"],
                    "priority": data["priority"],
                    "completed_at": now - timedelta(days=2) if data["status"] == "completed" else None,
                },
            )

            if created:
                for test_name, code, specimen, value, unit, ref_low, ref_high, flag in data["tests"]:
                    test = LabTest.objects.create(
                        order=order,
                        test_name=test_name,
                        test_code=code,
                        specimen_type=specimen,
                    )
                    if value is not None:
                        TestResult.objects.create(
                            test=test,
                            value=value,
                            unit=unit or "",
                            reference_range_low=Decimal(str(ref_low)) if ref_low is not None else None,
                            reference_range_high=Decimal(str(ref_high)) if ref_high is not None else None,
                            flag=flag,
                            resulted_by_id=uuid.uuid4(),
                        )
                self.stdout.write(self.style.SUCCESS(f"    ✓ Lab: {data['patient'].first_name} - {data['status']} ({len(data['tests'])} tests)"))

    def _create_invoices(self, patients):
        from apps.billing.models import Invoice, InvoiceItem, Payment
        from common.utils import generate_invoice_number

        self.stdout.write("  Creating invoices & payments...")

        now = timezone.now()

        invoice_data = [
            {
                "patient": patients[0],
                "status": "paid",
                "items": [
                    ("consultation", "Cardiology Consultation", 1, Decimal("200.00")),
                    ("lab_test", "Comprehensive Metabolic Panel", 1, Decimal("85.00")),
                    ("lab_test", "HbA1c Test", 1, Decimal("45.00")),
                ],
                "payment": Decimal("330.00"),
            },
            {
                "patient": patients[2],
                "status": "paid",
                "items": [
                    ("consultation", "Orthopedic Consultation", 1, Decimal("250.00")),
                    ("procedure", "Right Knee X-Ray (3 views)", 1, Decimal("120.00")),
                    ("medication", "Naproxen 500mg x28", 1, Decimal("25.00")),
                ],
                "payment": Decimal("395.00"),
            },
            {
                "patient": patients[4],
                "status": "partially_paid",
                "items": [
                    ("consultation", "Cardiac Follow-up", 1, Decimal("200.00")),
                    ("lab_test", "Cardiac Panel (Troponin, BNP)", 1, Decimal("150.00")),
                    ("lab_test", "Lipid Panel", 1, Decimal("65.00")),
                    ("procedure", "ECG", 1, Decimal("50.00")),
                ],
                "payment": Decimal("300.00"),
            },
            {
                "patient": patients[3],
                "status": "issued",
                "items": [
                    ("consultation", "Dermatology Consultation", 1, Decimal("180.00")),
                    ("medication", "Triamcinolone Cream 0.1%", 1, Decimal("35.00")),
                    ("medication", "Cetirizine 10mg x14", 1, Decimal("12.00")),
                ],
                "payment": None,
            },
            {
                "patient": patients[9],
                "status": "overdue",
                "items": [
                    ("consultation", "Diabetes Management", 1, Decimal("200.00")),
                    ("lab_test", "HbA1c", 1, Decimal("45.00")),
                    ("lab_test", "Renal Panel", 1, Decimal("95.00")),
                    ("lab_test", "Urine Albumin/Creatinine Ratio", 1, Decimal("55.00")),
                    ("medication", "Insulin Glargine", 1, Decimal("180.00")),
                ],
                "payment": None,
            },
            {
                "patient": patients[1],
                "status": "draft",
                "items": [
                    ("consultation", "Pediatric Wellness Visit", 1, Decimal("150.00")),
                    ("procedure", "Flu Vaccination", 1, Decimal("35.00")),
                ],
                "payment": None,
            },
        ]

        for data in invoice_data:
            subtotal = sum(item[3] * item[2] for item in data["items"])
            tax = subtotal * Decimal("0.05")
            total = subtotal + tax

            inv, created = Invoice.objects.get_or_create(
                patient=data["patient"],
                status=data["status"],
                total=total,
                defaults={
                    "invoice_number": generate_invoice_number(),
                    "subtotal": subtotal,
                    "tax_amount": tax,
                    "discount_amount": Decimal("0.00"),
                    "amount_paid": data["payment"] or Decimal("0.00"),
                    "due_date": (now - timedelta(days=5)).date() if data["status"] == "overdue" else (now + timedelta(days=30)).date(),
                    "notes": "",
                },
            )

            if created:
                for item_type, desc, qty, price in data["items"]:
                    InvoiceItem.objects.create(
                        invoice=inv,
                        item_type=item_type,
                        description=desc,
                        quantity=qty,
                        unit_price=price,
                        total_price=price * qty,
                    )

                if data["payment"]:
                    Payment.objects.create(
                        invoice=inv,
                        amount=data["payment"],
                        method="card",
                        reference_number=f"PAY-{uuid.uuid4().hex[:8].upper()}",
                        received_by_id=uuid.uuid4(),
                    )

                self.stdout.write(self.style.SUCCESS(f"    ✓ Invoice: {data['patient'].first_name} - ${total:.2f} ({data['status']})"))

    def _create_pharmacy_inventory(self, medications):
        from apps.pharmacy.models import PharmacyInventory

        self.stdout.write("  Creating pharmacy inventory...")

        inventory_data = [
            (medications[0], "BTH-2024-001", date(2026, 12, 31), 500, 50, 200, Decimal("0.15")),
            (medications[1], "BTH-2024-002", date(2026, 12, 31), 300, 50, 200, Decimal("0.20")),
            (medications[2], "BTH-2024-003", date(2027, 3, 15), 400, 40, 150, Decimal("0.25")),
            (medications[3], "BTH-2024-004", date(2027, 6, 30), 800, 100, 500, Decimal("0.08")),
            (medications[5], "BTH-2024-005", date(2027, 1, 15), 250, 30, 100, Decimal("0.45")),
            (medications[6], "BTH-2024-006", date(2027, 9, 30), 1000, 100, 500, Decimal("0.03")),
            (medications[7], "BTH-2024-007", date(2027, 4, 30), 350, 40, 150, Decimal("0.18")),
            (medications[8], "BTH-2024-008", date(2026, 11, 30), 200, 30, 100, Decimal("0.12")),
            (medications[9], "BTH-2024-009", date(2027, 8, 15), 600, 50, 200, Decimal("0.05")),
            (medications[10], "BTH-2024-010", date(2027, 2, 28), 80, 20, 50, Decimal("4.50")),
            (medications[11], "BTH-2024-011", date(2026, 9, 30), 15, 50, 200, Decimal("0.22")),  # Low stock!
            (medications[12], "BTH-2024-012", date(2027, 5, 31), 180, 30, 100, Decimal("0.85")),
            (medications[13], "BTH-2024-013", date(2027, 7, 31), 450, 50, 200, Decimal("0.15")),
            (medications[14], "BTH-2024-014", date(2027, 3, 31), 120, 20, 80, Decimal("8.50")),
            (medications[15], "BTH-2024-015", date(2026, 8, 31), 25, 10, 30, Decimal("35.00")),
            (medications[16], "BTH-2024-016", date(2027, 10, 31), 300, 30, 100, Decimal("0.90")),
            (medications[18], "BTH-2024-017", date(2027, 12, 31), 2000, 200, 1000, Decimal("0.02")),
            (medications[19], "BTH-2024-018", date(2027, 4, 15), 200, 30, 100, Decimal("0.35")),
        ]

        for med, batch, expiry, qty, reorder_lvl, reorder_qty, cost in inventory_data:
            inv, created = PharmacyInventory.objects.get_or_create(
                medication=med,
                batch_number=batch,
                defaults={
                    "expiry_date": expiry,
                    "quantity_on_hand": qty,
                    "reorder_level": reorder_lvl,
                    "reorder_quantity": reorder_qty,
                    "unit_cost": cost,
                    "location": "Shelf A" if cost < 1 else "Controlled Cabinet B",
                    "is_active": True,
                },
            )
            if created:
                status = "⚠️ LOW" if qty <= reorder_lvl else "✓"
                self.stdout.write(self.style.SUCCESS(f"    {status} {med.name}: {qty} units (batch {batch})"))

    def _create_insurance(self, patients):
        from apps.insurance.models import InsuranceProvider, PatientInsurance

        self.stdout.write("  Creating insurance data...")

        providers_data = [
            ("BlueCross BlueShield", "BCBS-001", "claims@bcbs.com", "+1-800-555-0001"),
            ("Aetna Health", "AETNA-001", "provider@aetna.com", "+1-800-555-0002"),
            ("UnitedHealthcare", "UHC-001", "claims@uhc.com", "+1-800-555-0003"),
            ("Cigna", "CIGNA-001", "provider@cigna.com", "+1-800-555-0004"),
            ("Medicare", "MDCR-001", "claims@medicare.gov", "+1-800-555-0005"),
            ("Humana", "HUM-001", "claims@humana.com", "+1-800-555-0006"),
        ]

        providers = {}
        for name, code, email, phone in providers_data:
            prov, created = InsuranceProvider.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "contact_email": email,
                    "contact_phone": phone,
                    "is_active": True,
                },
            )
            providers[name] = prov
            if created:
                self.stdout.write(self.style.SUCCESS(f"    ✓ Provider: {name}"))

        # Patient insurance policies
        policy_data = [
            (patients[0], "BlueCross BlueShield", "BCBS-P-123456", "GRP-100", date(2025, 1, 1), None),
            (patients[1], "Aetna Health", "AET-P-789012", "GRP-200", date(2025, 3, 1), None),
            (patients[2], "UnitedHealthcare", "UHC-P-345678", "GRP-300", date(2024, 6, 1), None),
            (patients[3], "Cigna", "CIG-P-901234", "GRP-400", date(2025, 1, 1), None),
            (patients[4], "Medicare", "MCR-P-567890", "", date(2020, 1, 1), None),
            (patients[5], "BlueCross BlueShield", "BCBS-P-111222", "GRP-100", date(2025, 1, 1), None),
            (patients[6], "Aetna Health", "AET-P-333444", "GRP-200", date(2025, 1, 1), None),
            (patients[7], "UnitedHealthcare", "UHC-P-555666", "GRP-500", date(2024, 9, 1), None),
            (patients[8], "Cigna", "CIG-P-777888", "GRP-400", date(2025, 6, 1), None),
            (patients[9], "Medicare", "MCR-P-999000", "", date(2019, 1, 1), None),
        ]

        for patient, prov_name, policy, group, eff_date, exp_date in policy_data:
            PatientInsurance.objects.get_or_create(
                patient=patient,
                provider=providers[prov_name],
                defaults={
                    "policy_number": policy,
                    "group_number": group,
                    "subscriber_name": patient.full_name,
                    "subscriber_relationship": "self",
                    "effective_date": eff_date,
                    "expiration_date": exp_date,
                    "is_primary": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(policy_data)} insurance policies created"))

    def _create_notifications(self, tenant_users):
        from apps.notifications.models import Notification

        self.stdout.write("  Creating notifications...")

        now = timezone.now()
        admin_tu = tenant_users.get("admin@clinic.com")
        if not admin_tu:
            return

        notifs = [
            ("appointment_reminder", "Upcoming Appointment", "Patient Mohamed Ibrahim has an appointment at 9:00 AM today.", False),
            ("lab_result", "Lab Results Ready", "Lab results for patient William Anderson (Cardiac Panel) are ready for review.", False),
            ("lab_result", "Critical Value Alert", "Patient Youssef Bakr has critical lab value: eGFR 42 mL/min (below threshold).", False),
            ("billing", "Overdue Invoice", "Invoice for patient Youssef Bakr ($603.75) is overdue by 5 days.", False),
            ("prescription", "Prescription Filled", "Prescription for patient Mohamed Ibrahim has been dispensed by pharmacy.", True),
            ("system", "System Update", "MedFlow Pro has been updated to version 2.1. Check release notes for new features.", True),
            ("appointment_reminder", "Tomorrow's Schedule", "You have 5 appointments scheduled for tomorrow.", True),
            ("billing", "Payment Received", "Payment of $300.00 received for patient William Anderson.", True),
        ]

        for ntype, title, body, is_read in notifs:
            Notification.objects.get_or_create(
                recipient_id=admin_tu.user_id,
                title=title,
                defaults={
                    "notification_type": ntype,
                    "channel": "in_app",
                    "body": body,
                    "is_read": is_read,
                    "read_at": now - timedelta(hours=2) if is_read else None,
                    "is_sent": True,
                    "sent_at": now - timedelta(hours=6),
                },
            )

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(notifs)} notifications created"))
