from django.contrib import admin

from .models import Device, DeviceType


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "metric_name", "metric_unit", "metric_min", "metric_max", "created_at")
    list_filter = ("metric_name",)
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("id", "created_at")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "serial_number", "device_type", "status", "last_seen", "created_at")
    list_filter = ("status", "device_type")
    search_fields = ("name", "serial_number", "location")
    ordering = ("-created_at",)
    readonly_fields = ("id", "auth_token", "token_generated_at", "created_at", "updated_at")
    raw_id_fields = ("device_type",)
