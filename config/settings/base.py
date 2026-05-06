"""
Django base settings — shared across all environments.

Reads sensitive values from environment variables via django-environ.
"""
import os
from pathlib import Path

import environ

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ──────────────────────────────────────────────
# Core
# ──────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ──────────────────────────────────────────────
# Tenants  (django-tenants)
# ──────────────────────────────────────────────
TENANT_MODEL = "tenants.Organization"
TENANT_DOMAIN_MODEL = "tenants.Domain"

SHARED_APPS = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Third-party (public-schema only)
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
    "django_prometheus",
    # Project apps in public schema
    "apps.tenants",
    "apps.accounts",
    "apps.audit",
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    # Project apps in tenant schemas
    "apps.patients",
    "apps.appointments",
    "apps.prescriptions",
    "apps.medical_records",
    "apps.lab_results",
    "apps.billing",
    "apps.notifications",
    "apps.ai_integration",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.KeycloakOIDCBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Keycloak / OIDC
KEYCLOAK_URL = env("KEYCLOAK_URL", default="http://localhost:8080")
KEYCLOAK_REALM = env("KEYCLOAK_REALM", default="healthcare-saas")
OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID", default="web-app")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET", default="")
OIDC_OP_JWKS_ENDPOINT = env(
    "OIDC_OP_JWKS_ENDPOINT",
    default=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs",
)
OIDC_OP_TOKEN_ENDPOINT = env(
    "OIDC_OP_TOKEN_ENDPOINT",
    default=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
)
OIDC_OP_USER_ENDPOINT = env(
    "OIDC_OP_USER_ENDPOINT",
    default=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo",
)

# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

# ──────────────────────────────────────────────
# Database  (schema-per-tenant)
# ──────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("DB_NAME", default="healthcare"),
        "USER": env("DB_USER", default="healthcare_user"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ──────────────────────────────────────────────
# REST Framework
# ──────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.KeycloakJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "apps.accounts.permissions.IsTenantMember",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "user": "100/min",
    },
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ──────────────────────────────────────────────
# drf-spectacular (OpenAPI)
# ──────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Healthcare SaaS API",
    "DESCRIPTION": "Production-ready Healthcare SaaS platform API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ──────────────────────────────────────────────
# Celery
# ──────────────────────────────────────────────
CELERY_BROKER_URL = env("RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 min hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 min soft limit
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ROUTES = {
    "apps.ai_integration.tasks.*": {"queue": "ai_tasks"},
    "apps.notifications.tasks.*": {"queue": "notifications"},
}

# ──────────────────────────────────────────────
# Cache (Redis)
# ──────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# ──────────────────────────────────────────────
# Storage (MinIO / S3)
# ──────────────────────────────────────────────
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY", default="minioadmin")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET_DOCUMENTS", default="medical-documents")
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT_URL", default="http://localhost:9000")
AWS_S3_REGION_NAME = env("MINIO_REGION", default="us-east-1")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"
AWS_QUERYSTRING_EXPIRE = 900  # 15 minutes for pre-signed URLs
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_USE_SSL = env.bool("MINIO_USE_SSL", default=False)
AWS_S3_VERIFY = env.bool("MINIO_VERIFY_SSL", default=False)

MINIO_BUCKET_AI_INPUTS = env("MINIO_BUCKET_AI_INPUTS", default="ai-inputs")

# ──────────────────────────────────────────────
# AI Service
# ──────────────────────────────────────────────
AI_SERVICE_BASE_URL = env("AI_SERVICE_BASE_URL", default="http://localhost:5000")
AI_SERVICE_TIMEOUT = env.int("AI_SERVICE_TIMEOUT", default=30)
AI_SERVICE_MAX_RETRIES = env.int("AI_SERVICE_MAX_RETRIES", default=3)

# ──────────────────────────────────────────────
# Encryption
# ──────────────────────────────────────────────
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default="")

# ──────────────────────────────────────────────
# Sentry
# ──────────────────────────────────────────────
SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_RATE", default=0.1),
        send_default_pii=False,
        environment=env("SENTRY_ENVIRONMENT", default="development"),
    )

# ──────────────────────────────────────────────
# Structured Logging (structlog)
# ──────────────────────────────────────────────
import structlog  # noqa: E402

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# ──────────────────────────────────────────────
# Templates (admin only)
# ──────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ──────────────────────────────────────────────
# Security defaults
# ──────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True

# ──────────────────────────────────────────────
# Static files
# ──────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ──────────────────────────────────────────────
# Password validation
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ──────────────────────────────────────────────
# i18n
# ──────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# URL conf
# ──────────────────────────────────────────────
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ──────────────────────────────────────────────
# Upload limits
# ──────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
