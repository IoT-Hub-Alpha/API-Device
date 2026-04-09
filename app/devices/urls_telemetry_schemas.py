from django.urls import path

from .views_telemetry_schema import TelemetrySchemaListView, TelemetrySchemaDetailView

urlpatterns = [
    path("", TelemetrySchemaListView.as_view(), name="telemetry-schema-list"),
    path("<uuid:schema_id>/", TelemetrySchemaDetailView.as_view(), name="telemetry-schema-detail"),
]
