from django.urls import path

from .views_device_type import DeviceTypeListView, DeviceTypeDetailView

urlpatterns = [
    # LIST + CREATE
    path("", DeviceTypeListView.as_view(), name="device-type-list"),
    # RETRIEVE + UPDATE + DELETE
    path(
        "<uuid:device_type_id>/",
        DeviceTypeDetailView.as_view(),
        name="device-type-detail",
    ),
]
