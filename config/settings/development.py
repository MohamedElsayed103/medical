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

# Email — console backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
