from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from django.db import transaction
from django.conf import settings
from devices.models import TelemetrySchema, Device, DeviceType
import json

class Command(BaseCommand):
    help = "Seed demo data (idempotent) from seed_data.json"
    
    def handle(self, *args, **kwargs):
        seed_data = self._get_json()
        self._start_seed(seed_data)
        
    @transaction.atomic
    def _start_seed(self, data):
        try:
            self._seed_device_type(data['device_types'])
            self._seed_devices(data['devices'])
            self._seed_schema(data['telemetry_schemas'])
            self.stdout.write(self.style.SUCCESS("Data seeded!"))
        except Exception as e:
            self.stdout.write(self.style.SUCCESS(str(e)))
        
        
        
        
    def _seed_devices(self, devices):
        for device in devices:
            Device.objects.update_or_create(
                id=device['id'],
                defaults={
                    **device
                }
            )
            self.stdout.write(self.style.SUCCESS("Data seeded!"))
            
    def _seed_schema(self, schemas):
        for schema in schemas:
            TelemetrySchema.objects.update_or_create(
                id=schema['id'],
                defaults={
                    **schema
                }
            )
            
    def _seed_device_type(self, types):
        for devices_type in types:
            DeviceType.objects.update_or_create(
                id=devices_type['id'],
                defaults={
                    **devices_type
                }
            )
        
        
    def _get_json(self):
        path: Path = Path(settings.BASE_DIR) / "seed_data.json"
        with open(path) as f:
            data = json.load(f)
    
        return data