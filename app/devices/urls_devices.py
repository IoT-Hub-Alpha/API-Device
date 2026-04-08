from django.urls import path

from .views import (
    DeviceListView,
    DeviceDetailView,
    DeviceRegisterView,
    DeviceRegenerateTokenView,
    DeviceStatusView,
)

urlpatterns = [
    # LIST + CREATE
    path("", DeviceListView.as_view(), name="device-list"),
    # REGISTER (token generation)
    path("register/", DeviceRegisterView.as_view(), name="device-register"),
    # RETRIEVE + UPDATE + DELETE
    path("<uuid:device_id>/", DeviceDetailView.as_view(), name="device-detail"),
    # REGENERATE TOKEN
    path(
        "<uuid:device_id>/regenerate-token/",
        DeviceRegenerateTokenView.as_view(),
        name="device-regenerate-token",
    ),
    # STATUS UPDATE
    path(
        "<uuid:device_id>/status/",
        DeviceStatusView.as_view(),
        name="device-status",
    ),
]
