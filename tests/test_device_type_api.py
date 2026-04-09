import json

import pytest

from devices.models import DeviceType


@pytest.mark.django_db
class TestDeviceTypeListAPI:
    def test_list_device_types_returns_pagination(self, client):
        resp = client.get("/v1/device-types/")
        assert resp.status_code == 200

        body = resp.json()
        assert "data" in body
        assert "pagination" in body

    def test_create_device_type(self, client):
        payload = {
            "name": "Vibration Sensor",
            "metric_name": "vibration",
            "metric_unit": "mm/s",
            "description": "Industrial vibration sensor",
        }
        resp = client.post(
            "/v1/device-types/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["name"] == "Vibration Sensor"
        assert body["data"]["metric_name"] == "vibration"

    def test_create_device_type_validation_error_missing_fields(self, client):
        payload = {"description": "No name or metric"}
        resp = client.post(
            "/v1/device-types/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "name" in body["errors"]
        assert "metric_name" in body["errors"]
        assert "metric_unit" in body["errors"]

    def test_create_device_type_duplicate_name(self, client):
        DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )
        payload = {
            "name": "Temp Sensor",
            "metric_name": "temperature",
            "metric_unit": "C",
        }
        resp = client.post(
            "/v1/device-types/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "name" in body["errors"]

    def test_search_device_types(self, client):
        DeviceType.objects.create(
            name="Temp Sensor", metric_name="temperature", metric_unit="C",
        )
        DeviceType.objects.create(
            name="Vibration Sensor", metric_name="vibration", metric_unit="mm/s",
        )

        resp = client.get("/v1/device-types/", {"search": "Vibration"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Vibration Sensor"


@pytest.mark.django_db
class TestDeviceTypeDetailAPI:
    @pytest.fixture
    def device_type(self):
        return DeviceType.objects.create(
            name="Temp Sensor",
            metric_name=DeviceType.MetricName.TEMPERATURE,
            metric_unit="C",
        )

    def test_retrieve_device_type(self, client, device_type):
        resp = client.get(f"/v1/device-types/{device_type.id}/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == str(device_type.id)

    def test_patch_device_type(self, client, device_type):
        payload = {"description": "Updated description"}
        resp = client.patch(
            f"/v1/device-types/{device_type.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["description"] == "Updated description"

    def test_delete_device_type(self, client, device_type):
        resp = client.delete(f"/v1/device-types/{device_type.id}/")
        assert resp.status_code == 204
        assert not DeviceType.objects.filter(id=device_type.id).exists()

    def test_detail_not_found(self, client):
        resp = client.get("/v1/device-types/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404
