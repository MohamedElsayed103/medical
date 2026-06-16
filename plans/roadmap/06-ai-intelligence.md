# Plan 06 — AI & Intelligence  (Tier P1→P2)

Make the existing `apps/ai_integration/` app deliver visible value. **Everything is human-in-the-loop**
(matches the platform's "never auto-finalize" rule). Use the latest Claude models via the Anthropic API.

> Provider note: build against the Anthropic API (model ids like `claude-fable-5` / latest). Keep the
> AI provider behind an adapter so it's swappable and so the core flows work even if AI is disabled
> (AI is "not functional out-of-box" per `CLAUDE.md` — keep that graceful).

Track status in [`PROGRESS.md`](./PROGRESS.md).

---

## 6.1 — Ambient scribe: audio → transcript → drafted SOAP note  ·  P1 (flagship)

**Why:** The single hottest EMR feature right now; massive time savings; strong differentiator.

**Backend (`apps/ai_integration/`)**
- Audio capture upload (presigned, Plan 02.5) → `AIRequest(type=SCRIBE, status, input_object_key)`.
- Celery pipeline: transcribe (speech-to-text provider) → summarize into a structured SOAP draft via
  Claude with a strict JSON schema (chief complaint, HPI, exam, assessment, plan, suggested diagnoses).
- `AIService.draft_note(visit, transcript)` returns the draft; persist as a **suggestion** linked to
  the visit (never auto-write the signed note).
- Endpoints: start scribe, poll status, fetch draft.

**Frontend:** on `VisitDetailPage`/`CreateVisitModal`, a "Record / Dictate" control; when the draft is
ready, show it side-by-side with editable SOAP fields ("Accept", "Edit", per-section insert). Doctor
edits then signs.

**Acceptance:** a recorded encounter produces an editable SOAP draft the doctor reviews and signs;
nothing is written to the chart without explicit acceptance.

---

## 6.2 — Result summarization & plain-language explanations  ·  P1

**Backend:** `AIService.summarize_results(lab_or_radiology_order)` → patient-friendly explanation +
clinician-facing highlights/anomalies; store as a suggestion field on the order/report. Trigger
optionally on result finalization (Celery), gated by a per-tenant setting.

**Frontend:** "AI summary" panel on lab/radiology detail (clinician) and a simplified version in the
patient portal (Plan 04.2), clearly labeled as AI-generated and not a diagnosis.

**Acceptance:** finalized results can show an AI summary for staff and a plain-language version for patients.

---

## 6.3 — Coding suggestions (ICD/CPT) from the note  ·  P2

**Backend:** `AIService.suggest_codes(visit)` → candidate ICD-10/CPT codes with rationale, validated
against the terminology tables (Plan 03.5/3.6). Returns suggestions only.

**Frontend:** on the superbill / diagnosis entry, show suggested codes with one-click accept; the human
confirms. Feeds Plan 05.5.

**Acceptance:** the encounter yields code suggestions that a coder/clinician accepts or rejects.

---

## 6.4 — Smart inbox / triage  ·  P2

**Backend:** classify + prioritize incoming items (abnormal/critical results, refill requests,
patient messages, unsigned visits) into a ranked worklist; `AIService.triage(items)` scores urgency.
Expose `GET /inbox/`.

**Frontend:** a unified inbox page with priority lanes and deep links to the underlying record.

**Acceptance:** staff sees a prioritized worklist instead of scattered queues.

---

## 6.5 — No-show prediction  ·  P2

**Backend:** a model (start with a simple logistic/heuristic on history: prior no-shows, lead time,
day/time, distance) → `no_show_risk` on upcoming appointments; recompute via Celery. No PHI leaves the
system; keep it explainable.

**Frontend:** risk badge on appointments + a setting to auto-intensify reminders / suggest overbooking
for high-risk slots.

**Acceptance:** appointments carry a risk score that drives reminder/overbooking strategy.

---

## 6.6 — AI safety scaffolding  ·  P1 (do alongside 6.1)

**Backend/Frontend cross-cutting**
- Every AI output: stored with model id + timestamp, labeled "AI-generated, requires review", never
  auto-applied; audit each generation and each human acceptance.
- Confidence/uncertainty surfaced; a global per-tenant AI on/off switch; PII handling documented
  (what is sent to the provider, retention) for the compliance docs (Plan 07.1).
- Graceful degradation: if `AI_SERVICE_BASE_URL`/keys are unset, AI features hide cleanly and core
  flows are unaffected.

**Acceptance:** AI is auditable, clearly labeled, always confirmed by a human, and safely disableable.
