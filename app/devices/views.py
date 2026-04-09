from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from iot_auth.django import CheckPermissionsMixin

from .models import Device
from .serializers import DeviceSerializer, DeviceValidator, DeviceRepository
from .exceptions import ApiValidationError, NotFoundError
from .views_common import json_body, parse_uuid, handle_api_errors, InternalServiceMixin


ALLOWED_ORDERING = {"created_at", "-created_at", "name", "-name", "last_seen", "-last_seen"}


@method_decorator(csrf_exempt, name="dispatch")
class DeviceListView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["devices.view"],
        "post": ["devices.add"],
    }
    default_page_size = 10

    @handle_api_errors
    def get(self, request):
        qs = Device.objects.select_related("device_type").order_by("-created_at")

        # --- Search (AC#5) ---
        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(location__icontains=search)
            )

        # --- Filtering (AC#5) ---
        serial_number = request.GET.get("serial_number", "").strip()
        if serial_number:
            qs = qs.filter(serial_number=serial_number)

        status = request.GET.get("status", "").strip()
        if status:
            qs = qs.filter(status=status)

        is_active = request.GET.get("is_active", "").strip().lower()
        if is_active == "true":
            qs = qs.exclude(status=Device.DeviceStatus.INACTIVE)
        elif is_active == "false":
            qs = qs.filter(status=Device.DeviceStatus.INACTIVE)

        device_type_id = request.GET.get("device_type_id", "").strip()
        if device_type_id:
            qs = qs.filter(device_type_id=device_type_id)

        # --- Ordering ---
        ordering = request.GET.get("ordering", "").strip()
        if ordering and ordering in ALLOWED_ORDERING:
            qs = qs.order_by(ordering)

        # --- Pagination ---
        page_number = request.GET.get("page", 1)
        page_size = int(request.GET.get("page_size", self.default_page_size))
        paginator = Paginator(qs, page_size)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            return JsonResponse({"errors": {"page": "Invalid page"}}, status=400)

        data = [
            DeviceSerializer(instance=obj).to_dict() for obj in page_obj.object_list
        ]

        return JsonResponse(
            {
                "data": data,
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total": paginator.count,
                    "total_pages": paginator.num_pages,
                    "next_page": (
                        page_obj.next_page_number() if page_obj.has_next() else None
                    ),
                    "prev_page": (
                        page_obj.previous_page_number()
                        if page_obj.has_previous()
                        else None
                    ),
                },
            },
            status=200,
        )

    @handle_api_errors
    def post(self, request: HttpRequest):
        payload = json_body(request)
        cleaned = DeviceValidator(data=payload, partial=False).validate()
        device = DeviceRepository.save(cleaned)
        device = Device.objects.select_related("device_type").get(id=device.id)
        return JsonResponse(
            {"data": DeviceSerializer(instance=device).to_dict()}, status=201
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceDetailView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["devices.view"],
        "patch": ["devices.change"],
        "put": ["devices.change"],
        "delete": ["devices.delete"],
    }

    def _get_device_or_404(self, device_id):
        try:
            uuid_obj = parse_uuid(device_id)
            return Device.objects.select_related("device_type").get(id=uuid_obj)
        except Device.DoesNotExist:
            raise NotFoundError("Device not found.")

    @handle_api_errors
    def get(self, request: HttpRequest, device_id):
        obj = self._get_device_or_404(device_id)
        return JsonResponse(
            {"data": DeviceSerializer(instance=obj).to_dict()}, status=200
        )

    def patch(self, request: HttpRequest, device_id):
        return self._update(request, device_id, partial=True)

    def put(self, request: HttpRequest, device_id):
        return self._update(request, device_id, partial=False)

    @handle_api_errors
    def delete(self, request: HttpRequest, device_id):
        obj = self._get_device_or_404(device_id)
        with transaction.atomic():
            obj.delete()
        return HttpResponse(status=204)

    @transaction.atomic
    @handle_api_errors
    def _update(self, request: HttpRequest, device_id, partial: bool):
        obj = self._get_device_or_404(device_id)

        payload = json_body(request)
        cleaned = DeviceValidator(
            data=payload, partial=partial, instance=obj
        ).validate()
        updated = DeviceRepository.save(cleaned, instance=obj)
        return JsonResponse(
            {"data": DeviceSerializer(instance=updated).to_dict()}, status=200
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceRegisterView(CheckPermissionsMixin, View):
    """POST /api/v1/devices/register/ — create device + generate auth token."""
    required_permissions = ["devices.add"]

    @handle_api_errors
    def post(self, request: HttpRequest):
        payload = json_body(request)
        cleaned = DeviceValidator(data=payload, partial=False).validate()

        with transaction.atomic():
            device = Device(**cleaned)
            device.generate_token()
            device.full_clean()
            device.save()

        device = Device.objects.select_related("device_type").get(id=device.id)
        return JsonResponse(
            {"data": DeviceSerializer(instance=device).to_dict(include_token=True)},
            status=201,
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceRegenerateTokenView(CheckPermissionsMixin, View):
    """POST /api/v1/devices/<uuid>/regenerate-token/ — regenerate auth token."""
    required_permissions = ["devices.change"]

    @handle_api_errors
    def post(self, request: HttpRequest, device_id):
        try:
            uuid_obj = parse_uuid(device_id)
            device = Device.objects.select_related("device_type").get(id=uuid_obj)
        except Device.DoesNotExist:
            raise NotFoundError("Device not found.")

        with transaction.atomic():
            device.generate_token()
            device.save(update_fields=["auth_token", "token_generated_at", "updated_at"])

        return JsonResponse(
            {"data": DeviceSerializer(instance=device).to_dict(include_token=True)},
            status=200,
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceStatusView(CheckPermissionsMixin, View):
    """PATCH /api/v1/devices/<uuid>/status/ — update device status."""
    required_permissions = ["devices.change"]

    @handle_api_errors
    def patch(self, request: HttpRequest, device_id):
        try:
            uuid_obj = parse_uuid(device_id)
            device = Device.objects.select_related("device_type").get(id=uuid_obj)
        except Device.DoesNotExist:
            raise NotFoundError("Device not found.")

        payload = json_body(request)
        new_status = payload.get("status", "").strip()

        if not new_status:
            raise ApiValidationError({"status": "This field is required."})

        allowed = Device.DeviceStatus.values
        if new_status not in allowed:
            raise ApiValidationError(
                {"status": f"Invalid status. Allowed: {', '.join(allowed)}"}
            )

        with transaction.atomic():
            device.status = new_status
            update_fields = ["status", "updated_at"]

            if new_status == Device.DeviceStatus.ONLINE:
                device.last_seen = timezone.now()
                update_fields.append("last_seen")

            device.save(update_fields=update_fields)

        return JsonResponse(
            {"data": DeviceSerializer(instance=device).to_dict()}, status=200
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceVerifyTokenView(InternalServiceMixin):
    """GET /v1/devices/verify-token/ — internal endpoint for service-to-service token check."""

    @handle_api_errors
    def get(self, request: HttpRequest):
        serial_number = request.GET.get("serial_number", "").strip()
        token = request.GET.get("token", "").strip()

        if not serial_number or not token:
            raise ApiValidationError(
                {"detail": "Both 'serial_number' and 'token' query params are required."},
                status_code=400,
            )

        try:
            device = Device.objects.select_related("device_type").get(
                serial_number=serial_number
            )
        except Device.DoesNotExist:
            return JsonResponse({"detail": "Device not found."}, status=404)

        if device.auth_token != token:
            return JsonResponse({"detail": "Invalid token."}, status=401)

        return JsonResponse(
            {"data": DeviceSerializer(instance=device).to_dict()}, status=200
        )
