# Plan 02 — Notifications & File Pipeline  (Tier P0→P1)

Two infrastructure gaps called out in `CLAUDE.md`: SMS/push are stubs, notifications poll instead of
push, and file uploads aren't wired (MinIO configured but unused; we enabled local storage in dev).
Closing these unblocks reminders (Plan 04), documents, and DICOM (Plan 03/06).

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 2.1 — SMS provider (Twilio)  ·  P1

**Backend (`apps/notifications/`)**
- Add a channel backend interface `notifications/channels/base.py::Channel.send(notification)`.
- `channels/sms_twilio.py` using `twilio` SDK; config in settings (`TWILIO_SID/TOKEN/FROM`) read via
  `django-environ`. No-op + warn if unconfigured (keeps dev working).
- Wire into `NotificationService.create_and_send(...)` so `NotificationChannel.SMS` dispatches via the
  backend, async through Celery (`tasks.py::send_notification.delay(id)`), with retry/backoff.
- Recipient phone resolution: patients via `Patient.phone`; staff via user profile.

**Acceptance:** an SMS notification enqueues a Celery task and sends via Twilio in staging; failures
are logged and retried, never block the triggering action.

---

## 2.2 — Push provider  ·  P1

**Backend**
- `channels/push_fcm.py` (FCM for mobile/web) — store device tokens in a `PushDevice(user_id, token,
  platform)` model (tenant or public schema as appropriate). Web-push (VAPID) acceptable as a first target.
- Dispatch `NotificationChannel.PUSH` via Celery like SMS.

**Frontend:** register the service worker + request permission; POST the token to
`/notifications/devices/`. Show toast on foreground push.

**Acceptance:** a push notification reaches a registered browser/device.

---

## 2.3 — Real-time bell via WebSocket  ·  P0 (Channels is installed but unconnected)

**Backend**
- Configure Django Channels: `config/asgi.py` routing, `channels_redis` layer (Redis already in stack).
- `apps/notifications/consumers.py::NotificationConsumer` — authenticates via JWT in the query string
  / subprotocol, joins group `notifications.<user_id>`.
- In `NotificationService.create_and_send`, after persisting the in-app notification,
  `group_send` the payload to the recipient's group.

**Frontend**
- `src/lib/ws.ts` — open a WS to `/ws/notifications/` with the access token; on message, push into the
  React Query cache for the bell and bump the unread count; reconnect with backoff.
- Replace the polling in the notifications hook with cache updates from the socket (keep a slow poll as fallback).

**Acceptance:** creating a notification updates the recipient's bell within ~1s without a refresh.

---

## 2.4 — Notification preferences UI  ·  P1

**Backend:** a `NotificationPreference(user_id, type, channel, enabled)` model (or JSON on profile);
`GET/PUT /notifications/preferences/`. `create_and_send` consults it before dispatching each channel.

**Frontend:** a Preferences section (in `pages/settings/` or `pages/profile/`): matrix of
notification-type × channel toggles.

**Acceptance:** disabling "Appointment reminder · SMS" stops that channel for that user.

---

## 2.5 — Production file storage (presigned uploads)  ·  P0 for any upload feature

**Why:** Dev uses filesystem (we set that). Production should use MinIO/S3 without proxying bytes
through Django.

**Backend**
- Keep `S3Boto3Storage` in prod (already configured). Add endpoints to mint **presigned PUT URLs**:
  `POST /files/presign/` → `{upload_url, object_key, headers}` (validates content-type + max size,
  scopes the key by tenant). Front end PUTs directly to storage; then confirms with the owning record.
- For dev, the existing `FileSystemStorage` + direct multipart upload (already working for medication
  images) is the fallback path.

**Acceptance:** a large file uploads directly to object storage via a presigned URL in staging.

---

## 2.6 — Document model + categories + patient Documents tab  ·  P1

**Backend (`apps/patients/` or new `apps/documents/` tenant app)**
- `Document(BaseModel)`: `patient` (nullable) / `customer` (nullable), `category`
  (`lab|imaging|id|insurance|consent|other` TextChoices), `object_key`, `filename`, `content_type`,
  `size`, `uploaded_by_id`, optional links (`visit`, `lab_order`, `radiology_order`). `AUDITED = True`.
- `DocumentService.create_from_upload(...)`, `presigned_view_url(doc)` (short-lived GET). Endpoints:
  `GET/POST /patients/{id}/documents/`, `GET /documents/{id}/url/`.

**Frontend:** a **Documents** tab on `PatientDetailPage` — upload (presigned), categorized list,
preview/download via short-lived URL.

**Acceptance:** files can be attached to a patient, categorized, listed, and viewed via expiring URLs.

---

## 2.7 — Upload validation + virus scanning  ·  P1

**Backend:** validate content-type allowlist + max size on presign and on confirm. Add a Celery task
hook to scan via ClamAV (`clamd`) or a cloud scanner; quarantine flag on `Document` until clean.

**Acceptance:** disallowed types/oversize are rejected; unscanned docs are flagged until cleared.

---

## 2.8 — DICOM / imaging handling for radiology  ·  P2 (feeds Plan 06 AI)

**Backend:** allow attaching imaging objects to `RadiologyReport.image_object_key` (field exists).
Store the original; generate a web-friendly thumbnail/preview (pydicom + Pillow for DICOM → PNG) via a
Celery task. Expose presigned view URL.

**Frontend:** show the thumbnail on `RadiologyOrderDetailPage`; "view full image" opens the object.
(A full DICOM viewer like Cornerstone.js is a later enhancement.)

**Acceptance:** a radiologist can attach an image to a report and see a preview on the detail page.
