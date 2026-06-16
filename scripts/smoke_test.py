#!/usr/bin/env python3
"""
API smoke test — exercises the request path of every clinical viewset against a
RUNNING dev server. This is the regression catcher for the class of bugs that
unit tests miss (read-only serializer fields, wrong filter params, property vs
DB-field filters, etc.).

Run:
    # backend must be running on :8000 with the demo tenant seeded
    venv_new/bin/python scripts/smoke_test.py
    # or point at another host:
    BASE=http://localhost:8000 EMAIL=admin@clinic.com PASSWORD=SecurePass123! \\
      venv_new/bin/python scripts/smoke_test.py

Exit code 0 = all passed, 1 = at least one failure.
"""
import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.environ.get("BASE", "http://localhost:8000").rstrip("/")
EMAIL = os.environ.get("EMAIL", "admin@clinic.com")
PASSWORD = os.environ.get("PASSWORD", "SecurePass123!")
API = f"{BASE}/api/v1"

_token = None
passed = 0
failed = 0


def _req(method, path, body=None, token=None):
    url = path if path.startswith("http") else f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  \033[32mPASS\033[0m {name}")
    else:
        failed += 1
        print(f"  \033[31mFAIL\033[0m {name} {detail}")


def login():
    global _token
    status, data = _req("POST", "/auth/login/", {"email": EMAIL, "password": PASSWORD})
    _token = (data or {}).get("access") or (data or {}).get("tokens", {}).get("access")
    check("auth/login", status == 200 and bool(_token), f"(status {status})")
    return _token


def get_first_id(path):
    status, data = _req("GET", path, token=_token)
    results = (data or {}).get("results", data) if isinstance(data, dict) else data
    if isinstance(results, list) and results:
        return results[0].get("id")
    return None


def list_ok(name, path, *, expect_results=True):
    status, data = _req("GET", path, token=_token)
    ok = status == 200 and (not expect_results or isinstance((data or {}).get("results", data), (list,)))
    check(f"GET {name}", ok, f"(status {status})")
    return data


def main():
    print(f"Smoke testing {API} as {EMAIL}\n")
    if not login():
        print("\nCannot continue without a token.")
        sys.exit(1)

    print("\n— List endpoints —")
    for name, path in [
        ("patients", "/patients/?page_size=1"),
        ("appointments", "/appointments/?page_size=1"),
        ("visits", "/visits/?page_size=1"),
        ("prescriptions", "/prescriptions/?page_size=1"),
        ("medications", "/prescriptions/medications/?page_size=1"),
        ("lab-orders", "/lab-orders/?page_size=1"),
        ("invoices", "/invoices/?page_size=1"),
        ("radiology", "/radiology/orders/"),
        ("doctors", "/appointments/doctors/?page_size=1"),
        ("availability", "/appointments/availability/"),
    ]:
        list_ok(name, path)

    print("\n— Appointment doctor filter (regression: doctor_id param) —")
    did = get_first_id("/appointments/doctors/?page_size=1")
    if did:
        status, data = _req("GET", f"/appointments/?doctor_id={did}", token=_token)
        check("appointments?doctor_id=", status == 200, f"(status {status})")
        status, _ = _req("GET", f"/appointments/available-slots/?doctor_id={did}&date=2026-06-22&duration_minutes=30", token=_token)
        check("available-slots", status == 200, f"(status {status})")

    print("\n— Patient 360 (timeline + summary) —")
    pid = get_first_id("/patients/?page_size=1")
    if pid:
        status, tl = _req("GET", f"/patients/{pid}/timeline/", token=_token)
        check("patient timeline", status == 200 and isinstance(tl, list), f"(status {status})")
        status, sm = _req("GET", f"/patients/{pid}/summary/", token=_token)
        check("patient summary", status == 200 and "outstanding_balance" in (sm or {}), f"(status {status})")

    print("\n— Global search —")
    status, sr = _req("GET", "/search/?q=INV", token=_token)
    check("search returns groups", status == 200 and "patients" in (sr or {}), f"(status {status})")

    print("\n— Visit related —")
    vid = get_first_id("/visits/?page_size=1")
    if vid:
        status, rel = _req("GET", f"/visits/{vid}/related/", token=_token)
        check("visit related", status == 200 and "prescriptions" in (rel or {}), f"(status {status})")

    print("\n— Detail retrieves (regression: nested fields) —")
    if pid:
        status, p = _req("GET", f"/patients/{pid}/", token=_token)
        check("patient retrieve", status == 200 and p.get("id") == pid, f"(status {status})")
    lid = get_first_id("/lab-orders/?page_size=1")
    if lid:
        status, lo = _req("GET", f"/lab-orders/{lid}/", token=_token)
        check("lab-order retrieve has doctor_name", status == 200 and "doctor_name" in (lo or {}), f"(status {status})")

    print("\n— Radiology create → transition (regression: is_deleted filter) —")
    if pid:
        status, order = _req("POST", "/radiology/orders/", {
            "patient_id": pid, "priority": "routine", "clinical_notes": "smoke",
            "studies": [{"modality": "xray", "body_part": "Chest"}],
        }, token=_token)
        check("radiology create", status == 201 and order.get("id"), f"(status {status})")
        if status == 201:
            oid = order["id"]
            s2, _ = _req("POST", f"/radiology/orders/{oid}/transition/", {"status": "scheduled"}, token=_token)
            check("radiology transition", s2 == 200, f"(status {s2})")

    print("\n— Notifications (preferences + device registration) —")
    status, _ = _req("GET", "/notifications/preferences/", token=_token)
    check("notification preferences", status == 200, f"(status {status})")
    status, dev = _req("POST", "/notifications/register-device/", {"token": "smoke-tok", "platform": "web"}, token=_token)
    check("register push device", status == 201, f"(status {status})")
    status, _ = _req("POST", "/notifications/unregister-device/", {"token": "smoke-tok"}, token=_token)
    check("unregister push device", status == 204, f"(status {status})")

    print("\n— Documents (list endpoint) —")
    if pid:
        status, _ = _req("GET", f"/patients/{pid}/documents/", token=_token)
        check("patient documents list", status == 200, f"(status {status})")

    print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
