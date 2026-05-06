"""
Staging settings — mirrors production with relaxed secrets.
"""
from .base import *  # noqa: F401,F403

DEBUG = False

# Force JSON logging in staging
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
