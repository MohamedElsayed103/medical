"""
Development settings — local machine, debug on, verbose logging.
"""
from datetime import timedelta

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Dev-friendly renderers
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Use Simple JWT for development (no Keycloak needed)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "rest_framework_simplejwt.authentication.JWTAuthentication",
    "apps.accounts.authentication.KeycloakJWTAuthentication",
    "rest_framework.authentication.SessionAuthentication",
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# CORS — allow everything in dev
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar
INSTALLED_APPS += ["django_extensions", "rest_framework_simplejwt"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Throttling — relaxed in dev
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/min",
    "user": "5000/min",
}

# Store uploaded files (e.g. medication images) on the local filesystem in dev,
# since MinIO/S3 is not running. Served via MEDIA_URL (see config/urls.py).
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# In-memory channel layer for dev so the real-time WebSocket works under a
# single-process `runserver` (daphne) without a running Redis.
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

# Email — console backend for dev (emails printed directly in terminal)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@medflow.com"

# Also print invitation links to console to make it easy for dev 
INVITATION_BASE_URL = "http://localhost:5173/invitation"
