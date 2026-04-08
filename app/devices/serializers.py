from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.forms.models import model_to_dict

from .models import Device, DeviceType
from .exceptions import ApiValidationError


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


# ---------------------------------------------------------------------------
# DeviceType serializers
# ---------------------------------------------------------------------------


@dataclass
class DeviceTypeReadSerializer:
    instance: DeviceType

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.instance.id),
            "name": self.instance.name,
            "description": self.instance.description,
            "metric_name": self.instance.metric_name,
            "metric_unit": self.instance.metric_unit,
            "metric_min": (
                str(self.instance.metric_min)
                if self.instance.metric_min is not None
                else None
            ),
            "metric_max": (
                str(self.instance.metric_max)
                if self.instance.metric_max is not None
                else None
            ),
            "created_at": (
                self.instance.created_at.isoformat()
                if self.instance.created_at
                else None
            ),
        }


@dataclass
class DeviceTypeValidator:
    data: Optional[dict[str, Any]] = None
    partial: bool = False
    instance: Optional[DeviceType] = None

    write_fields = (
        "name",
        "description",
        "metric_name",
        "metric_unit",
        "metric_min",
        "metric_max",
    )

    errors: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> dict[str, Any]:
        self.errors = {}
        if self.data is None:
            raise ValueError("DeviceTypeValidator(data=...) is required for validate()")
        cleaned = self._parse_and_clean()
        self._validate_business_rules(cleaned)

        if self.errors:
            raise ApiValidationError(self.errors, status_code=400)

        return cleaned

    def _parse_and_clean(self) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        self._require_fields()
        self._copy_allowed_fields(cleaned)
        self._normalize_strings(cleaned)
        return cleaned

    def _validate_business_rules(self, cleaned: dict[str, Any]) -> None:
        self._validate_name(cleaned)
        self._validate_name_unique(cleaned)
        self._validate_metric_name(cleaned)
        self._validate_metric_unit(cleaned)

    def _require_fields(self) -> None:
        if self.partial:
            return
        required = ("name", "metric_name", "metric_unit")
        for f in required:
            if f not in self.data:
                self.errors[f] = "This field is required."

    def _copy_allowed_fields(self, cleaned: dict[str, Any]) -> None:
        for k in self.write_fields:
            if k in self.data:
                cleaned[k] = self.data.get(k)

    def _normalize_strings(self, cleaned: dict[str, Any]) -> None:
        for k in ("name", "description", "metric_unit"):
            if k in cleaned and isinstance(cleaned[k], str):
                cleaned[k] = cleaned[k].strip()

    def _validate_name(self, cleaned: dict[str, Any]) -> None:
        if "name" in cleaned and _is_blank(cleaned["name"]):
            self.errors["name"] = "Name cannot be blank."

    def _validate_name_unique(self, cleaned: dict[str, Any]) -> None:
        name = cleaned.get("name")
        if not _is_blank(name):
            qs = DeviceType.objects.filter(name=name)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.errors["name"] = "DeviceType with this name already exists."

    def _validate_metric_name(self, cleaned: dict[str, Any]) -> None:
        if "metric_name" in cleaned:
            allowed = DeviceType.MetricName.values
            if cleaned["metric_name"] not in allowed:
                self.errors["metric_name"] = (
                    f"Invalid metric_name. Allowed: {', '.join(allowed)}"
                )

    def _validate_metric_unit(self, cleaned: dict[str, Any]) -> None:
        if "metric_unit" in cleaned and _is_blank(cleaned["metric_unit"]):
            self.errors["metric_unit"] = "Metric unit cannot be blank."


class DeviceTypeRepository:
    @staticmethod
    @transaction.atomic
    def save(
        cleaned: dict[str, Any], instance: Optional[DeviceType] = None
    ) -> DeviceType:
        if instance is None:
            obj = DeviceType(**cleaned)
        else:
            obj = instance
            for k, v in cleaned.items():
                setattr(obj, k, v)

        obj.full_clean()
        obj.save()
        return obj

    @staticmethod
    @transaction.atomic
    def delete(instance: DeviceType) -> None:
        instance.delete()


# ---------------------------------------------------------------------------
# Device serializers
# ---------------------------------------------------------------------------


@dataclass
class DeviceTypeShortSerializer:
    instance: DeviceType

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.instance.id),
            "name": self.instance.name,
        }


@dataclass
class DeviceSerializer:
    instance: Optional[Device] = None

    read_fields = (
        "id",
        "name",
        "serial_number",
        "location",
        "status",
        "last_seen",
        "created_at",
        "updated_at",
    )

    def to_dict(self, include_token: bool = False) -> dict[str, Any]:
        if not self.instance:
            raise ValueError("DeviceSerializer(instance=...) is required for to_dict()")

        payload = model_to_dict(self.instance, fields=self.read_fields)
        payload["id"] = str(self.instance.id)

        payload["device_type"] = DeviceTypeShortSerializer(
            self.instance.device_type
        ).to_dict()

        # datetimes -> ISO
        for k in ("last_seen", "created_at", "updated_at"):
            dt = getattr(self.instance, k, None)
            payload[k] = dt.isoformat() if dt else None

        if include_token:
            payload["auth_token"] = self.instance.auth_token
            payload["token_generated_at"] = (
                self.instance.token_generated_at.isoformat()
                if self.instance.token_generated_at
                else None
            )

        return payload


@dataclass
class DeviceValidator:
    data: Optional[dict[str, Any]] = None
    partial: bool = False
    instance: Optional[Device] = None

    write_fields = (
        "name",
        "serial_number",
        "location",
        "status",
        "device_type_id",
    )

    errors: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> dict[str, Any]:
        self.errors = {}
        if self.data is None:
            raise ValueError("DeviceValidator(data=...) is required for validate()")
        cleaned = self._parse_and_clean()
        self._validate_business_rules(cleaned)

        if self.errors:
            raise ApiValidationError(self.errors, status_code=400)

        return cleaned

    def _parse_and_clean(self) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        self._require_fields()
        self._copy_allowed_fields(cleaned)
        self._normalize_strings(cleaned)
        return cleaned

    def _validate_business_rules(self, cleaned: dict[str, Any]) -> None:
        self._validate_name(cleaned)
        self._validate_serial(cleaned)
        self._validate_serial_unique(cleaned)
        self._validate_status(cleaned)
        self._resolve_device_type(cleaned)

    def _require_fields(self) -> None:
        required = set(self.write_fields) if not self.partial else set()
        for f in required:
            if f not in self.data:
                self.errors[f] = "This field is required."

    def _copy_allowed_fields(self, cleaned: dict[str, Any]) -> None:
        for k in self.write_fields:
            if k in self.data:
                cleaned[k] = self.data.get(k)

    def _normalize_strings(self, cleaned: dict[str, Any]) -> None:
        for k in ("name", "serial_number", "location"):
            if k in cleaned and isinstance(cleaned[k], str):
                cleaned[k] = cleaned[k].strip()

    def _validate_name(self, cleaned: dict[str, Any]) -> None:
        if "name" in cleaned and _is_blank(cleaned["name"]):
            self.errors["name"] = "Device name cannot be blank."

    def _validate_serial(self, cleaned: dict[str, Any]) -> None:
        if "serial_number" in cleaned and _is_blank(cleaned["serial_number"]):
            self.errors["serial_number"] = "Serial number cannot be blank."

    def _validate_serial_unique(self, cleaned: dict[str, Any]) -> None:
        serial = cleaned.get("serial_number")
        if not _is_blank(serial):
            qs = Device.objects.filter(serial_number=serial)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.errors["serial_number"] = (
                    "Device with this serial number already exists"
                )

    def _validate_status(self, cleaned: dict[str, Any]) -> None:
        if "status" in cleaned:
            allowed = Device.DeviceStatus.values
            if cleaned["status"] not in allowed:
                self.errors["status"] = (
                    f"Invalid status. Allowed: {', '.join(allowed)}"
                )

    def _resolve_device_type(self, cleaned: dict[str, Any]) -> None:
        if "device_type_id" in cleaned:
            dt_id = cleaned["device_type_id"]
            try:
                if isinstance(dt_id, str):
                    UUID(dt_id)
                device_type = DeviceType.objects.get(id=dt_id)
                cleaned["device_type"] = device_type
            except (ValueError, ObjectDoesNotExist):
                self.errors["device_type_id"] = "DeviceType not found or invalid id."
            else:
                cleaned.pop("device_type_id", None)


class DeviceRepository:
    @staticmethod
    @transaction.atomic
    def save(cleaned: dict[str, Any], instance: Optional[Device] = None) -> Device:
        if instance is None:
            obj = Device(**cleaned)
        else:
            obj = instance
            for k, v in cleaned.items():
                setattr(obj, k, v)

        obj.full_clean()
        obj.save()
        return obj

    @staticmethod
    @transaction.atomic
    def delete(instance: Device) -> None:
        instance.delete()
