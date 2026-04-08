from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from devices.models import DeviceType, Device


@pytest.mark.django_db
class TestDeviceTypeModel:
    def test_metric_min_must_be_less_than_metric_max(self):
        dt = DeviceType(
            name="DT-Temp",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
            metric_min=Decimal("10"),
            metric_max=Decimal("5"),
        )
        with pytest.raises(ValidationError) as exc_info:
            dt.full_clean()

        err = exc_info.value.message_dict
        assert "metric_min" in err
        assert "metric_max" in err

    def test_valid_device_type_creation(self):
        dt = DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )
        assert dt.pk is not None
        assert str(dt) == "Temp Sensor (temperature)"


@pytest.mark.django_db
class TestDeviceModel:
    @pytest.fixture
    def device_type(self):
        return DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )

    def test_device_status_must_be_in_choices(self, device_type):
        d = Device(
            device_type=device_type,
            name="Sensor 1",
            serial_number="SN-001",
            status="not-valid",
        )
        with pytest.raises(ValidationError) as exc_info:
            d.full_clean()
        assert "status" in exc_info.value.message_dict

    def test_serial_number_must_be_unique(self, device_type):
        Device.objects.create(
            device_type=device_type,
            name="Sensor 1",
            serial_number="SN-UNIQ",
        )

        d2 = Device(
            device_type=device_type,
            name="Sensor 2",
            serial_number="SN-UNIQ",
        )
        with pytest.raises(ValidationError) as exc_info:
            d2.full_clean()
        assert "serial_number" in exc_info.value.message_dict

    def test_generate_token(self, device_type):
        d = Device.objects.create(
            device_type=device_type,
            name="Sensor Token",
            serial_number="SN-TOK-001",
        )
        token = d.generate_token()
        assert token is not None
        assert len(token) == 64
        assert d.token_generated_at is not None

    def test_extended_statuses(self, device_type):
        for status in ("active", "inactive", "online", "offline", "error"):
            d = Device(
                device_type=device_type,
                name=f"Sensor {status}",
                serial_number=f"SN-{status}",
                status=status,
            )
            d.full_clean()
