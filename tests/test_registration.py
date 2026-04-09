import json

import pytest

from devices.models import DeviceType, Device


@pytest.mark.django_db
class TestDeviceRegistration:
    @pytest.fixture
    def device_type(self):
        return DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )

    def test_register_device_creates_with_token(self, client, device_type):
        payload = {
            "name": "Registered Sensor",
            "serial_number": "SN-REG-001",
            "device_type_id": str(device_type.id),
            "status": "active",
            "location": "Factory Floor",
        }
        resp = client.post(
            "/v1/devices/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 201
        body = resp.json()

        assert "auth_token" in body["data"]
        assert body["data"]["auth_token"] is not None
        assert len(body["data"]["auth_token"]) == 64
        assert body["data"]["token_generated_at"] is not None

        device = Device.objects.get(id=body["data"]["id"])
        assert device.auth_token == body["data"]["auth_token"]

    def test_register_device_validation_error(self, client, device_type):
        payload = {
            "name": "",
            "serial_number": "",
            "device_type_id": str(device_type.id),
        }
        resp = client.post(
            "/v1/devices/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_regenerate_token(self, client, device_type):
        device = Device.objects.create(
            name="Sensor Regen",
            serial_number="SN-REGEN",
            device_type=device_type,
            status="active",
        )
        device.generate_token()
        device.save()
        old_token = device.auth_token

        resp = client.post(
            f"/v1/devices/{device.id}/regenerate-token/",
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["data"]["auth_token"] != old_token
        assert len(body["data"]["auth_token"]) == 64

    def test_regenerate_token_not_found(self, client):
        resp = client.post(
            "/v1/devices/00000000-0000-0000-0000-000000000000/regenerate-token/",
            content_type="application/json",
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDeviceStatusTracking:
    @pytest.fixture
    def device_type(self):
        return DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )

    @pytest.fixture
    def device(self, device_type):
        return Device.objects.create(
            name="Status Sensor",
            serial_number="SN-STATUS",
            device_type=device_type,
            status="active",
        )

    def test_update_status_to_online_sets_last_seen(self, client, device):
        assert device.last_seen is None

        resp = client.patch(
            f"/v1/devices/{device.id}/status/",
            data=json.dumps({"status": "online"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["status"] == "online"
        assert body["data"]["last_seen"] is not None

    def test_update_status_to_offline(self, client, device):
        resp = client.patch(
            f"/v1/devices/{device.id}/status/",
            data=json.dumps({"status": "offline"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "offline"

    def test_update_status_to_error(self, client, device):
        resp = client.patch(
            f"/v1/devices/{device.id}/status/",
            data=json.dumps({"status": "error"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "error"

    def test_update_status_invalid(self, client, device):
        resp = client.patch(
            f"/v1/devices/{device.id}/status/",
            data=json.dumps({"status": "broken"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_status_missing(self, client, device):
        resp = client.patch(
            f"/v1/devices/{device.id}/status/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_status_not_found(self, client):
        resp = client.patch(
            "/v1/devices/00000000-0000-0000-0000-000000000000/status/",
            data=json.dumps({"status": "online"}),
            content_type="application/json",
        )
        assert resp.status_code == 404
