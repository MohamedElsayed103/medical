"""
Production settings — hardened security, JSON logging, strict CORS.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# ── Security hardening ──
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── JSON logging in production ──
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405

# ── Ensure all origins are explicit ──
CORS_ALLOW_ALL_ORIGINS = False
