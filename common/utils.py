"""
Shared utility functions.
"""
import base64
import hashlib
import secrets
import uuid

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def generate_mrn(prefix: str = "MRN") -> str:
    """Generate a unique Medical Record Number.  Format: MRN-XXXXXXXX"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def generate_invoice_number(prefix: str = "INV") -> str:
    """Generate a unique invoice number.  Format: INV-XXXXXXXX"""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def generate_api_key() -> tuple[str, str]:
    """Generate a random API key and its SHA-256 hash.

    Returns:
        (raw_key, hashed_key) — display raw_key once, store hashed_key.
    """
    raw_key = secrets.token_urlsafe(48)
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed_key


def hash_pin(pin: str) -> str:
    """One-way SHA-256 hash of a PIN with a salt derived from SECRET_KEY."""
    salted = f"{settings.SECRET_KEY}:{pin}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_pin(pin: str, pin_hash: str) -> bool:
    return hash_pin(pin) == pin_hash


# ── Field-level encryption (Fernet) ──


def _get_fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise ValueError("FIELD_ENCRYPTION_KEY is not configured.")
    # Ensure the key is proper base64
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext. Returns plaintext string."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return ""


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxy headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first (client) IP — proxies append downstream
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
