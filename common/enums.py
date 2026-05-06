"""
Shared enums (TextChoices) used across multiple apps.
"""
from django.db import models


class OrganizationType(models.TextChoices):
    CLINIC = "clinic", "Clinic"
    HOSPITAL = "hospital", "Hospital"
    LAB = "lab", "Laboratory"


class SubscriptionPlan(models.TextChoices):
    FREE = "free", "Free"
    PRO = "pro", "Professional"
    ENTERPRISE = "enterprise", "Enterprise"


class UserRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Administrator"
    DOCTOR = "doctor", "Doctor"
    NURSE = "nurse", "Nurse"
    RECEPTIONIST = "receptionist", "Receptionist"
    LAB_TECH = "lab_tech", "Lab Technician"
    BILLING_STAFF = "billing_staff", "Billing Staff"


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class AppointmentStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CONFIRMED = "confirmed", "Confirmed"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"


class AppointmentType(models.TextChoices):
    IN_PERSON = "in_person", "In Person"
    TELEHEALTH = "telehealth", "Telehealth"


class LabOrderStatus(models.TextChoices):
    ORDERED = "ordered", "Ordered"
    SAMPLE_COLLECTED = "sample_collected", "Sample Collected"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class LabPriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "Stat"


class ResultFlag(models.TextChoices):
    NORMAL = "normal", "Normal"
    LOW = "low", "Low"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    INSURANCE = "insurance", "Insurance"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    ONLINE = "online", "Online"


class MedicationForm(models.TextChoices):
    TABLET = "tablet", "Tablet"
    CAPSULE = "capsule", "Capsule"
    SYRUP = "syrup", "Syrup"
    INJECTION = "injection", "Injection"
    CREAM = "cream", "Cream"
    DROPS = "drops", "Drops"
    INHALER = "inhaler", "Inhaler"


class MedicationRoute(models.TextChoices):
    ORAL = "oral", "Oral"
    IV = "iv", "Intravenous"
    IM = "im", "Intramuscular"
    TOPICAL = "topical", "Topical"
    SUBLINGUAL = "sublingual", "Sublingual"
    INHALATION = "inhalation", "Inhalation"


class DiagnosisType(models.TextChoices):
    PRIMARY = "primary", "Primary"
    SECONDARY = "secondary", "Secondary"
    RULE_OUT = "rule_out", "Rule Out"


class AIRequestType(models.TextChoices):
    PRESCRIPTION_OCR = "prescription_ocr", "Prescription OCR"
    LAB_ANALYSIS = "lab_analysis", "Lab Analysis"
    RADIOLOGY = "radiology", "Radiology"


class AIRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    READ = "read", "Read"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    EXPORT = "export", "Export"


class NotificationType(models.TextChoices):
    APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
    LAB_RESULT = "lab_result", "Lab Result Ready"
    PRESCRIPTION = "prescription", "Prescription"
    BILLING = "billing", "Billing"
    SYSTEM = "system", "System"


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-App"
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    PUSH = "push", "Push Notification"


class InvoiceItemType(models.TextChoices):
    CONSULTATION = "consultation", "Consultation"
    PROCEDURE = "procedure", "Procedure"
    LAB_TEST = "lab_test", "Lab Test"
    MEDICATION = "medication", "Medication"
    OTHER = "other", "Other"
