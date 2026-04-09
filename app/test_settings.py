import os
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-testing-purposes-only")

from device_service.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
