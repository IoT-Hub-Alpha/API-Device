"""
Django settings for device_service (API-Device microservice).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY or "insecure" in SECRET_KEY.lower():
    raise ValueError("DJANGO_SECRET_KEY must be set to a secure value")

DEBUG = str(os.getenv("DEVICE_SERVICE_DEBUG", "false")).lower() in ("true", "yes", "1")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# --- Application definition ---

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "devices",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "iot_auth.django.JWTAuthMiddleware",
]

ROOT_URLCONF = "device_service.urls"

WSGI_APPLICATION = "device_service.wsgi.application"

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

# --- Database (shared DB via ghcr.io/iot-hub-alpha/postgresql:0.1) ---

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "iot_hub_alpha_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        },
    }
}

# --- Internationalization ---

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- JWT Auth (jwt-auth-lib) ---

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
INTERNAL_SERVICE_HEADER = os.getenv("INTERNAL_SERVICE_HEADER", "X-Internal-Service")

# --- Logging ---

try:
    import iot_logging  # noqa: F401

    _log_formatter = {"()": "iot_logging.StructuredJsonFormatter"}
except ImportError:
    _log_formatter = {
        "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": _log_formatter,
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
}
