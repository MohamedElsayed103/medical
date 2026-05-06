"""
Test settings — fast, isolated.
"""
from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

# In-memory SQLite is not compatible with django-tenants, so use a test PG database.
DATABASES["default"]["NAME"] = "healthcare_test"  # noqa: F405

# Faster hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# Celery: eager execution (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable Sentry in tests
SENTRY_DSN = ""

# Encryption key for tests
FIELD_ENCRYPTION_KEY = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw=="

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
