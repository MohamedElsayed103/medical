"""
Celery application for Healthcare SaaS.

Auto-discovers tasks from all installed apps.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("healthcare")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
