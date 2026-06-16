# MedFlow Pro — Product & Engineering Recommendations

*How to turn the current platform into a complete, competitive healthcare SaaS.*

Last updated: 2026-06-15

---

## How to read this document

This is a roadmap, not a backlog dump. It is organized by **theme**, and within each
theme items are ordered roughly by **impact-to-effort**. Each recommendation states *why*
it matters competitively (vs. products like Epic, Athenahealth, DrChrono, Practice Fusion,
SimplePractice, Tebra) and *what* it concretely means in this codebase.

A direct answer to the question you asked — *"should we add more detail pages like the
medication page?"* — is in **Section 2**. Short version: **yes**, and it's one of the
highest-leverage, lowest-risk things you can do right now.

---

## 1. Where the product stands today

**Strong foundation already in place:**
- Multi-tenant (schema-per-tenant) architecture with RBAC — this is the hard part, and it's done.
- Core clinical modules: patients, appointments + doctor availability, visits (SOAP), prescriptions,
  lab orders, **radiology (now with full create/report UI)**, pharmacy/inventory, billing, insurance.
- Service-layer discipline (business logic in `services.py`), soft-delete + audit log, immutable
  signed visits, encrypted PII.
- Auto-billing hook (`BillingService.create_from_source`) wiring clinical events → draft invoices.
- A clean, modern React UI with consistent list/detail patterns.

**The competitive gaps** are mostly in *depth, polish, and the "last mile" of each workflow* —
not in missing modules. That's good news: you're closing gaps, not rebuilding.

---

## 2. Add richer detail pages and "entity 360" views  ← your direct question

You asked whether to keep adding detail pages like the new **Medication detail page** (which now
has an image, description, side effects, contraindications, and storage instructions). **Yes — this
is exactly the right instinct.** In clinical software, the perceived quality of the product is
largely a function of how much useful context each screen surfaces without a click. Thin list rows
that aren't clickable (the bugs we just fixed) read as "unfinished"; rich, navigable detail pages
read as "enterprise-grade."

### Detail pages worth building next (highest value first)

| Entity | What the detail page should show | Why it matters |
|--------|----------------------------------|----------------|
| **Patient 360** (extend existing) | Timeline merging visits, prescriptions, lab + radiology results, invoices, allergies, problem list, active meds, insurance status — one scrollable chart | This is *the* screen clinicians live in. It's the single biggest differentiator. |
| **Doctor / Provider profile** | Bio, specialization, availability calendar, today's schedule, patient panel, productivity stats | Already have `DoctorProfile`; surface it as a real page. |
| **Visit detail** (enrich) | SOAP + vitals trend sparklines, linked prescriptions/labs/rays/invoice, "sign & lock" affordance, amendment history | Ties the whole encounter together. |
| **Invoice detail** (done) / **Payment receipt** | Printable/PDF receipt, insurance claim status, partial-payment ledger | Billing trust = printable artifacts. |
| **Lab/Radiology result detail** (done) | Trend graphs for repeated tests, reference-range visualization, critical-value banner, attached images/DICOM | Result interpretation is where labs/imaging products win. |
| **Insurance policy / claim detail** | Coverage breakdown, claim lifecycle timeline, EOB, denial reasons | Revenue-cycle depth. |

### A reusable "rich detail" recipe
You already have the pattern (back link → header with status chips → summary card → related
sections). Standardize it:
- **Domain enrichment fields** on reference models (we just did this for `Medication`: image +
  clinical text). Do the same for diagnoses (ICD‑10 description + category), lab tests (LOINC +
  reference ranges by age/sex), and procedures (CPT + default price).
- **"Related to this" sections** that deep-link across modules (a prescription links to its
  medication and its visit; a lab order links to its patient and invoice). We added several of
  these links; keep extending them so nothing is a dead end.
- **Empty states that teach** ("No clinical details yet — click Edit to add…") instead of blank space.

---

## 3. Clinical depth (the features payers and clinicians expect)

These are the things that show up on competitor feature-comparison pages.

1. **Medication catalog → real drug database.** Today `Medication` is a free-text table.
   Integrate (or stub an interface for) an external drug DB (RxNorm/First Databank/OpenFDA) for:
   - **Drug–drug and drug–allergy interaction checking** at prescribe time (huge safety + sales point).
   - Autocomplete by NDC/RxNorm, standardized strengths/forms.
   - Dosage guidance and renal/hepatic adjustments.
2. **Problem list & allergy list** as first-class, structured patient records (not just visit notes).
3. **ICD‑10 / CPT / LOINC coded pickers** with search-as-you-type (replaces manual code entry —
   currently a known gap per `CLAUDE.md`).
4. **e-Prescribing (eRx) / EPCS.** Sending prescriptions electronically to pharmacies (Surescripts
   in the US) is table-stakes for ambulatory EMRs. Even a "print/fax Rx" PDF is a meaningful interim step.
5. **Clinical templates & order sets** — specialty-specific SOAP templates, favorite Rx/lab/imaging
   bundles. Massive time-saver that drives daily-active usage.
6. **Vitals & growth charts** — trend graphs, pediatric percentile curves.
7. **Care plans & care gaps / reminders** — overdue screenings, chronic-disease follow-ups.
8. **Referrals loop closure** — you have a `referrals` app; add status tracking + result return.

---

## 4. Patient experience & engagement (the revenue multiplier)

Competitors monetize the patient-facing side heavily. This is likely your biggest untapped surface.

1. **Patient portal** (separate auth scope): view records, results, upcoming appts, statements.
2. **Online self-scheduling** — patients book into the doctor-availability slots you now compute.
3. **Automated reminders** — appointment reminders via SMS/email/push (the SMS/push channels are
   currently stubs per `CLAUDE.md`; wiring a real provider like Twilio is high ROI).
4. **Telehealth / video visits** — `Appointment.type` already supports modalities; add a video room
   (Twilio Video / Daily / Zoom SDK) and a virtual waiting room.
5. **Digital intake & consent forms** — pre-visit questionnaires, e-signatures.
6. **Online bill pay** — Stripe/Adyen checkout against invoices; you already track balances.

---

## 5. Revenue cycle management (where clinics decide to buy)

1. **Insurance eligibility checks (real-time 270/271)** before the visit.
2. **Claims submission & ERA/EOB (837/835)** — clearinghouse integration; claim scrubbing.
3. **Superbills & coding assistance** — auto-suggest CPT/ICD from the encounter.
4. **Payment plans, statements, and dunning** — automated patient A/R follow-up.
5. **Financial dashboards** — A/R aging, denial rate, days-in-A/R, collection rate, payer mix.
   (The dashboard revenue chart is a good start; extend into a proper RCM analytics view.)

---

## 6. Intelligence & automation (your "AI platform" promise)

You already have an `ai_integration` app. Make it deliver visible value:
1. **Ambient scribe / note generation** — transcribe the visit, draft the SOAP note (this is the
   single hottest feature in the EMR market right now). Use the latest Claude models via the API.
2. **Lab/radiology result summarization & flagging** — plain-language explanations, anomaly highlights.
3. **Coding & billing suggestions** from the note.
4. **Smart inbox / triage** — prioritize messages, results, refill requests.
5. **Predictive no-show scoring** to drive overbooking/reminder strategy.
> Keep all AI suggestions **human-in-the-loop** (matches your existing auto-billing philosophy:
> never auto-finalize). This is also the safer regulatory posture.

---

## 7. Platform, trust & compliance (what unlocks enterprise deals)

1. **Compliance posture**: HIPAA (US) / GDPR (EU) readiness — BAAs, data-processing agreements,
   data residency. Document it; enterprises will ask.
2. **Audit log UI & exports** — you have an immutable `AuditLog`; give compliance officers a
   searchable, exportable view. Add "who viewed this patient" (break-the-glass) access logging.
3. **Real file storage pipeline** — MinIO/S3 is configured but uploads weren't wired end-to-end
   (we just enabled local-filesystem storage for dev + a working medication-image upload). Productionize:
   presigned uploads, virus scanning, DICOM handling, document categories (labs, IDs, consents).
4. **Notifications**: finish SMS + push (currently stubs) and add **WebSocket** real-time delivery
   (Channels is installed but not connected per `CLAUDE.md`) so the bell updates live instead of polling.
5. **Observability**: Sentry + Prometheus are installed — add dashboards, SLOs, and alerting.
   Add structured request tracing across the service layer.
6. **Background jobs hardening** — Celery is present; make reminders, claim submission, and
   AI calls all async with retries and dead-letter handling.
7. **Data import/export & interoperability** — **FHIR API** (R4) and HL7 v2 feeds. This is the key
   that opens integrations with hospitals, labs, and HIEs, and is increasingly a regulatory requirement.

---

## 8. Engineering quality & developer experience

These reduce the cost of everything above and prevent regressions like the clickability and
`doctor_id`/`is_deleted` bugs we just fixed.

1. **Automated tests for the request path, not just units.** Several bugs we fixed were latent
   because there were no end-to-end API tests:
   - The radiology create endpoint 500'd on `Patient.objects.get(..., is_deleted=False)` — `is_deleted`
     is a *property*, not a DB field. A single happy-path API test would have caught it.
   - The `DoctorAvailability` serializer silently dropped `doctor_id` (read-only by default in DRF).
   - The appointment doctor filter used a param name the backend didn't accept.
   Add a per-viewset smoke test (create → retrieve → transition) using the test admin token.
2. **Contract tests / typed client.** The frontend and backend disagreed on field names
   (`doctor_name` vs `doctor`, `visit_id` vs `visit`, `test.result_value` vs `test.result.value`).
   Generate the TS client from the OpenAPI schema (`drf-spectacular` is already installed) so the
   types are always in sync.
3. **Shared UI primitives.** Extract the repeated "detail page" scaffold, status-chip, and
   orderer-picker into reusable components (the lab/radiology/pharmacy order forms duplicate a lot).
4. **Consistent error surfacing.** The backend returns `{"error": {"code", "message"}}` but several
   frontend toasts read `error.detail`. Standardize an axios response interceptor that normalizes
   both shapes so users see real messages.
5. **Seed/demo data + a one-command dev bootstrap.** Make it trivial to spin up a populated tenant
   for demos and tests.
6. **Fix the broken `venv/`** and pin dependencies (we added `Pillow`); keep `requirements/*.txt`
   authoritative.

---

## 9. Suggested sequencing (next two quarters)

**Now (finish the "feels complete" pass):**
- Rich detail pages everywhere (Section 2) + cross-module deep links + empty states.
- Wire SMS/email reminders (turn the stubs on) and real file storage in production.
- API smoke tests + OpenAPI-generated TS client (stop the field-name drift).

**Next (clinical depth that closes deals):**
- Coded pickers (ICD‑10/CPT/LOINC), problem/allergy lists, drug-interaction checking.
- Patient portal + online scheduling + online bill pay.
- AI ambient scribe (note generation) as a flagship differentiator.

**Then (enterprise & scale):**
- FHIR/HL7 interoperability, eligibility + claims (RCM), telehealth.
- Compliance documentation, audit/access-log UI, observability/SLOs.

---

## 10. Quick wins you can ship this week

- [ ] Make **every** list row clickable to a detail page (done for invoices, lab orders,
      prescriptions, radiology — audit the rest: pharmacy, insurance, visits).
- [ ] Add **print/PDF** for invoices, prescriptions, and lab/radiology reports.
- [ ] Turn on **appointment reminders** (email is already working).
- [ ] Add a **global search** (patients, orders, invoices) in the top bar.
- [ ] Show **status timelines** on orders (ordered → … → completed) instead of a single chip.
- [ ] Add **bulk medication import** (CSV) to populate the formulary fast.
- [ ] Add **drug images + monographs** to the rest of the formulary now that the model supports it.
