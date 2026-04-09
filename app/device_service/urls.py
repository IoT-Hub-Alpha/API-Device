from django.contrib import admin
from django.urls import path, include

from devices.views_health import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),
    path("v1/devices/", include("devices.urls_devices")),
    path("v1/device-types/", include("devices.urls_device_types")),
    path("v1/telemetry-schemas/", include("devices.urls_telemetry_schemas")),
]
