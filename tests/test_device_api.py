import json

import pytest

from devices.models import DeviceType, Device


@pytest.mark.django_db
class TestDeviceListAPI:
    @pytest.fixture
    def device_type(self):
        return DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )

    def test_list_devices_returns_pagination(self, client):
        resp = client.get("/v1/devices/")
        assert resp.status_code == 200

        body = resp.json()
        assert "data" in body
        assert "pagination" in body
        assert isinstance(body["data"], list)

        for key in ("page", "page_size", "total", "total_pages", "next_page", "prev_page"):
            assert key in body["pagination"]

    def test_list_devices_invalid_page_returns_400(self, client):
        resp = client.get("/v1/devices/", {"page": 0, "page_size": 10})
        assert resp.status_code == 400
        body = resp.json()
        assert "errors" in body
        assert body["errors"]["page"] == "Invalid page"

    def test_create_device(self, client, device_type):
        payload = {
            "name": "Sensor 1",
            "serial_number": "SN-001",
            "device_type_id": str(device_type.id),
            "status": "active",
            "location": "Lab",
        }
        resp = client.post(
            "/v1/devices/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 201

        body = resp.json()
        assert "data" in body
        assert body["data"]["name"] == "Sensor 1"
        assert Device.objects.filter(id=body["data"]["id"]).exists()

    def test_create_device_validation_error(self, client, device_type):
        payload = {
            "name": "",
            "serial_number": "",
            "device_type_id": str(device_type.id),
        }
        resp = client.post(
            "/v1/devices/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "errors" in body

    def test_search_devices(self, client, device_type):
        Device.objects.create(
            name="Alpha Sensor", serial_number="SN-A1",
            device_type=device_type, location="Lab A",
        )
        Device.objects.create(
            name="Beta Sensor", serial_number="SN-B1",
            device_type=device_type, location="Lab B",
        )

        resp = client.get("/v1/devices/", {"search": "Alpha"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Alpha Sensor"

    def test_filter_by_status(self, client, device_type):
        Device.objects.create(
            name="Active Dev", serial_number="SN-ACT",
            device_type=device_type, status="active",
        )
        Device.objects.create(
            name="Offline Dev", serial_number="SN-OFF",
            device_type=device_type, status="offline",
        )

        resp = client.get("/v1/devices/", {"status": "offline"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["status"] == "offline"

    def test_filter_by_device_type_id(self, client, device_type):
        dt2 = DeviceType.objects.create(
            name="Pressure Sensor",
            metric_name=DeviceType.MetricName.PRESSURE,
            metric_unit="Pa",
        )
        Device.objects.create(
            name="Temp Dev", serial_number="SN-T1", device_type=device_type,
        )
        Device.objects.create(
            name="Press Dev", serial_number="SN-P1", device_type=dt2,
        )

        resp = client.get("/v1/devices/", {"device_type_id": str(dt2.id)})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Press Dev"


@pytest.mark.django_db
class TestDeviceDetailAPI:
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
            name="Sensor X",
            serial_number="SN-XYZ",
            device_type=device_type,
            status=Device.DeviceStatus.ACTIVE,
            location="Lab",
        )

    def test_retrieve_device(self, client, device):
        resp = client.get(f"/v1/devices/{device.id}/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == str(device.id)

    def test_patch_device(self, client, device):
        payload = {"status": Device.DeviceStatus.INACTIVE}
        resp = client.patch(
            f"/v1/devices/{device.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        device.refresh_from_db()
        assert device.status == Device.DeviceStatus.INACTIVE

    def test_delete_device(self, client, device):
        resp = client.delete(f"/v1/devices/{device.id}/")
        assert resp.status_code == 204
        assert not Device.objects.filter(id=device.id).exists()

    def test_detail_not_found(self, client):
        resp = client.get("/v1/devices/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404
