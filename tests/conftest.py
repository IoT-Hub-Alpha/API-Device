import os
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-testing-purposes-only")


def _stub_iot_auth():
    """Create stub modules for iot_auth so tests run without the real package."""
    if "iot_auth" in sys.modules:
        return

    iot_auth = ModuleType("iot_auth")
    iot_auth_django = ModuleType("iot_auth.django")
    iot_auth_types = ModuleType("iot_auth.types")

    # CheckPermissionsMixin — passthrough (no permission enforcement in tests)
    class CheckPermissionsMixin:
        required_permissions = []
        permission_map = {}

    # JWTAuthMiddleware — passthrough
    class JWTAuthMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            request.auth = {
                "sub": "test-user-uuid",
                "username": "testuser",
                "permissions": [],
                "is_superuser": True,
            }
            return self.get_response(request)

    iot_auth_django.CheckPermissionsMixin = CheckPermissionsMixin
    iot_auth_django.JWTAuthMiddleware = JWTAuthMiddleware
    iot_auth_django.check_permissions = MagicMock(side_effect=lambda *p: lambda fn: fn)
    iot_auth_django.require_auth = MagicMock(side_effect=lambda fn: fn)

    iot_auth_types.JWTPayload = dict

    sys.modules["iot_auth"] = iot_auth
    sys.modules["iot_auth.django"] = iot_auth_django
    sys.modules["iot_auth.types"] = iot_auth_types


def _stub_iot_logging():
    """Stub iot_logging if not installed."""
    if "iot_logging" in sys.modules:
        return
    iot_logging = ModuleType("iot_logging")
    iot_logging.StructuredJsonFormatter = MagicMock()
    sys.modules["iot_logging"] = iot_logging


# Stub before Django setup so middleware/logging imports succeed
_stub_iot_auth()
_stub_iot_logging()



