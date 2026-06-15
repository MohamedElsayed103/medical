# 03 — Appointments & Doctor Availability

Covers **#4** (availability schedule), **#5** (search by specialization → choose doctor),
**#6** (calendar view with doctor name + filters), **#7** (completed appointment → record visit notice).

Depends on: `02-rbac-and-permissions.md` (uses `doctor_availability:*`).

---

## Current state (verified)
- `DoctorProfile` (tenant): `user_id` (UUID, cross-schema), `specialization` (free-text CharField),
  `consultation_fee`, `is_available` (bool, currently unused in logic).
- `Appointment`: `patient`, `doctor`, `scheduled_at`, `duration_minutes` (default 30), `status`
  (6-state FSM), `type`.
- `AppointmentService.get_available_slots(doctor, date, ...)` exists but uses **hardcoded
  `work_start_hour=9, work_end_hour=17`** — no real availability. `_check_conflict()` prevents
  double-booking. `transition_status()` enforces the FSM.
- Frontend: `AppointmentsPage.tsx` (list), `BookAppointmentModal.tsx`. `appointmentsService` has
  `getDoctors`, `getAvailableSlots`, `book`, status transitions.

---

## #4 — Doctor availability (weekly recurring + date exceptions)

### New models — `apps/appointments/models.py`

```python
class DoctorAvailability(BaseModel):
    """Recurring weekly availability window for a doctor (e.g. Mon 14:00–17:00)."""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="availabilities")
    day_of_week = models.PositiveSmallIntegerField(help_text="0=Monday … 6=Sunday")  # match Python date.weekday()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "appointments_doctor_availability"
        ordering = ["doctor", "day_of_week", "start_time"]
        indexes = [models.Index(fields=["doctor", "day_of_week"])]
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F("start_time")),
                                   name="availability_end_after_start"),
        ]
    AUDITED = True


class DoctorTimeOff(BaseModel):
    """Date-specific exception: doctor unavailable for a range (vacation, one-off block)."""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="time_off")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "appointments_doctor_time_off"
        ordering = ["-start_at"]
        indexes = [models.Index(fields=["doctor", "start_at"])]
        constraints = [
            models.CheckConstraint(check=models.Q(end_at__gt=models.F("start_at")),
                                   name="timeoff_end_after_start"),
        ]
    AUDITED = True
```

> `day_of_week` uses Python's `date.weekday()` convention (Mon=0). Document this in the field help_text
> and use it consistently in the service and the frontend day picker.

### Service changes — `apps/appointments/services.py`

Rewrite `get_available_slots` to read availability instead of hardcoded hours:
```python
@staticmethod
def get_available_slots(*, doctor, date, duration_minutes=30):
    windows = DoctorAvailability.objects.filter(
        doctor=doctor, day_of_week=date.weekday(), is_active=True
    ).order_by("start_time")
    if not windows.exists():
        return []   # doctor not in on that weekday

    # existing booked appts that day (exclude CANCELLED / NO_SHOW)
    day_start = make_aware(datetime.combine(date, time.min))
    day_end = day_start + timedelta(days=1)
    booked = Appointment.objects.filter(
        doctor=doctor, scheduled_at__gte=day_start, scheduled_at__lt=day_end,
    ).exclude(status__in=[AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW])

    time_off = DoctorTimeOff.objects.filter(doctor=doctor, start_at__lt=day_end, end_at__gt=day_start)

    slots = []
    for w in windows:
        cursor = make_aware(datetime.combine(date, w.start_time))
        window_end = make_aware(datetime.combine(date, w.end_time))
        while cursor + timedelta(minutes=duration_minutes) <= window_end:
            slot_end = cursor + timedelta(minutes=duration_minutes)
            overlaps_booked = any(a.scheduled_at < slot_end and a.end_time > cursor for a in booked)
            overlaps_off = any(t.start_at < slot_end and t.end_at > cursor for t in time_off)
            if not overlaps_booked and not overlaps_off:
                slots.append(cursor)
            cursor = slot_end
    return slots
```
Add CRUD service methods: `set_availability(doctor, windows: list[dict])` (replace-all for a doctor),
`add_time_off(...)`, `remove_time_off(...)`. Enforce the "doctor edits own only" rule in the view
by comparing `DoctorProfile.user_id == request.user.id` unless the user has `doctor_availability:write`
at admin/receptionist level — simplest: allow `doctor_availability:write` holders to edit anyone;
additionally allow a doctor to edit their own even if they only hold the read perm. Pick one and
document; default: **`doctor_availability:write` required to edit anyone; doctors get `:write` for
their own rows via service-side `user_id` check.**

Also make `book()` reject a slot the doctor isn't available for (call a
`_within_availability(doctor, scheduled_at, duration)` check that mirrors the slot logic) and respect
`DoctorTimeOff`. Raise `ServiceError("Doctor not available at this time.", code="OUTSIDE_AVAILABILITY")`.

### API — `apps/appointments/views.py` + `urls.py`
Add a `DoctorAvailabilityViewSet` (or actions on `DoctorProfileViewSet`):
- `GET /api/v1/appointments/doctors/{id}/availability/` → list weekly windows → `doctor_availability:read`.
- `PUT /api/v1/appointments/doctors/{id}/availability/` → replace weekly windows (body: list of
  `{day_of_week, start_time, end_time}`) → `doctor_availability:write`.
- `GET/POST/DELETE /api/v1/appointments/doctors/{id}/time-off/` → manage exceptions.
Serializers in `apps/appointments/serializers.py` for both models.

### Migration
`makemigrations appointments` → `migrate_schemas` (tenant app).

### Frontend
- `appointmentsService`: add `getAvailability(doctorId)`, `setAvailability(doctorId, windows)`,
  `getTimeOff(doctorId)`, `addTimeOff(doctorId, data)`, `removeTimeOff(doctorId, id)`.
- New UI in doctor management (e.g. a "Schedule" tab/modal on the doctor profile): a weekly grid
  (Mon–Sun rows) where the user adds start/end time windows, plus a time-off list with date-range
  picker. Day labels map 0→Mon … 6→Sun.
- `BookAppointmentModal`: after picking a doctor + date, call `getAvailableSlots` and render only
  real slots (it already calls `getAvailableSlots`; now it returns availability-driven results).

### Acceptance
- Set "Omar: Mon & Wed 14:00–17:00" → booking on Monday offers only 14:00–17:00 slots in
  `duration_minutes` increments; Tuesday offers none.
- Adding a time-off range removes overlapping slots and blocks `book()` with `OUTSIDE_AVAILABILITY`.

---

## #5 — Search by specialization, then choose a doctor

### Backend
`DoctorProfile.specialization` is free text today. To make filtering reliable:
- Add a `Specialization` `TextChoices` to `common/enums.py` with common values (General Practice,
  Cardiology, Dermatology/Dental, Pediatrics, Orthopedics, Gynecology, ENT, Ophthalmology,
  Neurology, Psychiatry, Radiology, …). Keep `specialization` a CharField but document that the UI
  selects from these choices (don't hard-restrict at DB level to avoid breaking existing free-text rows).
- Add filtering to `DoctorProfileViewSet`: support `?specialization=<value>` and
  `?search=<text>` (django-filter / SearchFilter). Add
  `GET /api/v1/appointments/specializations/` returning the distinct specializations present
  (`DoctorProfile.objects.values_list('specialization', flat=True).distinct()`), so the UI can
  populate a dropdown from real data.

### Frontend
- `appointmentsService.getSpecializations()` → `GET /appointments/specializations/`.
- `appointmentsService.getDoctors({ specialization })` (extend existing `getDoctors` params).
- In `BookAppointmentModal` (and a doctor search UI): **two-step select** — first a Specialization
  dropdown (from `getSpecializations`), then the Doctor dropdown filtered to that specialization.
  Selecting a specialization refetches doctors with `{ specialization }`.

### Acceptance
- Choosing "Dental" lists only dental doctors; the doctor select is disabled/empty until a
  specialization is chosen (or shows "all" if none selected).

---

## #6 — Calendar view with doctor name + filters

This is primarily frontend on `AppointmentsPage.tsx`.

### Backend (small)
- Ensure the appointment serializer returns `doctor_name` and `doctor_specialization` and
  `patient_name` (it likely returns `doctor_name`/`patient_name` already — verify in
  `apps/appointments/serializers.py`; add `doctor_specialization` via a `SerializerMethodField`
  reading `obj.doctor.specialization`).
- Ensure list filtering supports `?doctor_id=`, `?specialization=` (filter by
  `doctor__specialization`), and `?date_from=&date_to=` (already supports date range).

### Frontend — `AppointmentsPage.tsx`
- Add a view toggle: **List | Calendar**. For Calendar, render a week/day grid (you can build a
  lightweight month/week grid with `date-fns` — no new dependency required) placing each appointment
  in its day/time cell.
- Each calendar entry shows **patient name + doctor name** (and a small specialization tag /
  color-by-specialization).
- Filter bar above the calendar: **Doctor** dropdown (from `getDoctors`) and **Specialization**
  dropdown (from `getSpecializations`); selecting either refetches the appointment list with
  `{ doctor_id }` / `{ specialization }` and the date window of the visible period.
- Keep the existing list view intact; the toggle just swaps the render.

### Acceptance
- Calendar shows appointments in their time slots with patient + doctor names.
- Filtering by a doctor shows only that doctor's appointments; filtering by "Dental" shows only
  dental appointments.

---

## #7 — Completed appointment → prompt doctor to record the visit

### Backend — hook the status transition
In `AppointmentService.transition_status(...)` (`apps/appointments/services.py`), when
`new_status == AppointmentStatus.COMPLETED`:
1. Notify the doctor to record a visit (unless a `Visit` linked to this appointment already exists):
   ```python
   from apps.notifications.services import NotificationService
   already = Visit.objects.filter(appointment=appointment).exists()
   if not already:
       NotificationService.create_and_send(
           recipient_id=str(appointment.doctor.user_id),
           notification_type=NotificationType.SYSTEM,   # or a new APPOINTMENT type
           title="Record visit",
           body=f"Appointment with {appointment.patient.full_name} is completed. Please record the visit.",
           channel=NotificationChannel.IN_APP,
           data={"action": "create_visit", "appointment_id": str(appointment.id),
                 "patient_id": str(appointment.patient_id)},
       )
   ```
   Wrap in try/except so a notification failure never blocks the status change (log a warning).
2. (Optional but recommended) return a flag in the API response (`"prompt_visit": true`) so the UI
   can immediately open the Create-Visit modal for the doctor who clicked "Complete".

### Frontend
- In `AppointmentsPage` (and detail), after a successful `complete(id)` mutation, if the current user
  is the appointment's doctor, open `CreateVisitModal` pre-filled with `patient_id` and
  `appointment_id` (so `visit.appointment` links automatically — `VisitService.create_visit` already
  accepts `appointment=`). Pass `appointment_id` through `visitsService.create`.
- The notification (bell) deep-links: clicking the "Record visit" notification navigates to the
  patient and opens the Create-Visit modal using `data.appointment_id` / `data.patient_id`.

### Backend note for linkage
`visitsService.create` / `VisitService.create_visit` must accept and persist `appointment` — confirm
the visit create serializer exposes an `appointment_id` write field; add it if missing so the
prompted visit links back to the appointment (prevents duplicate prompts via the `already` check).

### Acceptance
- Marking an appointment Completed creates an in-app notification to that doctor (visible in the bell).
- The doctor is offered the Create-Visit form pre-linked to the appointment; once a visit exists for
  that appointment, completing again does not re-notify.
