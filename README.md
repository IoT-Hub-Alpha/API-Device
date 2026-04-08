# API-Device

Device API microservice for IoT Hub Alpha — dedicated service for device management.

## Overview

| Item | Value |
|------|-------|
| **Framework** | Django 5.2.10 |
| **Port** | 8010 |
| **Database** | Shared PostgreSQL (`iot_hub_alpha_db`) |
| **Python** | 3.13 |

## API Endpoints

### Devices (`/api/v1/devices/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/devices/` | List devices (paginated, search, filter) |
| POST | `/api/v1/devices/` | Create device |
| GET | `/api/v1/devices/<uuid>/` | Retrieve device |
| PATCH | `/api/v1/devices/<uuid>/` | Partial update |
| PUT | `/api/v1/devices/<uuid>/` | Full update |
| DELETE | `/api/v1/devices/<uuid>/` | Delete device |
| POST | `/api/v1/devices/register/` | Register device (with token) |
| POST | `/api/v1/devices/<uuid>/regenerate-token/` | Regenerate auth token |
| PATCH | `/api/v1/devices/<uuid>/status/` | Update device status |

**Query parameters** for `GET /api/v1/devices/`:
- `search` — search by name, serial_number, location
- `status` — filter by status (active, inactive, online, offline, error)
- `device_type_id` — filter by device type UUID
- `ordering` — sort by created_at, name, last_seen (prefix `-` for desc)
- `page`, `page_size` — pagination

### Device Types (`/api/v1/device-types/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/device-types/` | List device types |
| POST | `/api/v1/device-types/` | Create device type |
| GET | `/api/v1/device-types/<uuid>/` | Retrieve device type |
| PATCH | `/api/v1/device-types/<uuid>/` | Partial update |
| PUT | `/api/v1/device-types/<uuid>/` | Full update |
| DELETE | `/api/v1/device-types/<uuid>/` | Delete device type |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health/` | Liveness probe |
| GET | `/ready/` | Readiness probe (DB check) |

## Local Development

```bash
cp .env.example .env
# edit .env with your DB credentials

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cd app
python manage.py runserver 0.0.0.0:8010
```

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t api-device .
docker run -p 8010:8010 --env-file .env api-device
```