from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from iot_auth.django import CheckPermissionsMixin

from .models import TelemetrySchema
from .exceptions import ApiValidationError, NotFoundError
from .views_common import json_body, parse_uuid, handle_api_errors


def _serialize(obj: TelemetrySchema) -> dict:
    return {
        "id": str(obj.id),
        "version": obj.version,
        "is_active": obj.is_active,
        "validation_schema": obj.validation_schema,
        "transformation_rules": obj.transformation_rules,
        "description": obj.description,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
    }


def _validate_payload(data: dict, partial: bool = False) -> dict:
    errors = {}
    if not partial:
        for field in ("version", "validation_schema"):
            if field not in data:
                errors[field] = "This field is required."
    if errors:
        raise ApiValidationError(errors)

    cleaned = {}
    for field in ("version", "is_active", "validation_schema", "transformation_rules", "description"):
        if field in data:
            cleaned[field] = data[field]

    if "version" in cleaned and (not isinstance(cleaned["version"], str) or not cleaned["version"].strip()):
        errors["version"] = "Version cannot be blank."
    if "validation_schema" in cleaned and not isinstance(cleaned["validation_schema"], dict):
        errors["validation_schema"] = "Must be a JSON object."
    if "transformation_rules" in cleaned and not isinstance(cleaned["transformation_rules"], dict):
        errors["transformation_rules"] = "Must be a JSON object."
    if errors:
        raise ApiValidationError(errors)

    return cleaned


@method_decorator(csrf_exempt, name="dispatch")
class TelemetrySchemaListView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["devices.view"],
        "post": ["devices.add"],
    }
    default_page_size = 20

    @handle_api_errors
    def get(self, request: HttpRequest):
        qs = TelemetrySchema.objects.order_by("-created_at")

        version = request.GET.get("version", "").strip()
        if version:
            qs = qs.filter(version=version)

        is_active = request.GET.get("is_active", "").strip().lower()
        if is_active == "true":
            qs = qs.filter(is_active=True)
        elif is_active == "false":
            qs = qs.filter(is_active=False)

        page_number = request.GET.get("page", 1)
        page_size = int(request.GET.get("page_size", self.default_page_size))
        paginator = Paginator(qs, page_size)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            return JsonResponse({"errors": {"page": "Invalid page"}}, status=400)

        return JsonResponse(
            {
                "data": [_serialize(obj) for obj in page_obj.object_list],
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
        cleaned = _validate_payload(payload, partial=False)

        version = cleaned.get("version", "").strip()
        if TelemetrySchema.objects.filter(version=version).exists():
            raise ApiValidationError({"version": "TelemetrySchema with this version already exists."})

        with transaction.atomic():
            obj = TelemetrySchema(**cleaned)
            obj.save()

        return JsonResponse({"data": _serialize(obj)}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class TelemetrySchemaDetailView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["devices.view"],
        "patch": ["devices.change"],
        "put": ["devices.change"],
        "delete": ["devices.delete"],
    }

    def _get_or_404(self, schema_id):
        try:
            uuid_obj = parse_uuid(schema_id)
            return TelemetrySchema.objects.get(id=uuid_obj)
        except TelemetrySchema.DoesNotExist:
            raise NotFoundError("TelemetrySchema not found.")

    @handle_api_errors
    def get(self, request: HttpRequest, schema_id):
        obj = self._get_or_404(schema_id)
        return JsonResponse({"data": _serialize(obj)}, status=200)

    def patch(self, request: HttpRequest, schema_id):
        return self._update(request, schema_id, partial=True)

    def put(self, request: HttpRequest, schema_id):
        return self._update(request, schema_id, partial=False)

    @handle_api_errors
    def delete(self, request: HttpRequest, schema_id):
        obj = self._get_or_404(schema_id)
        with transaction.atomic():
            obj.delete()
        return HttpResponse(status=204)

    @transaction.atomic
    @handle_api_errors
    def _update(self, request: HttpRequest, schema_id, partial: bool):
        obj = self._get_or_404(schema_id)
        payload = json_body(request)
        cleaned = _validate_payload(payload, partial=partial)

        version = cleaned.get("version")
        if version and TelemetrySchema.objects.filter(version=version).exclude(pk=obj.pk).exists():
            raise ApiValidationError({"version": "TelemetrySchema with this version already exists."})

        for k, v in cleaned.items():
            setattr(obj, k, v)
        obj.save()

        return JsonResponse({"data": _serialize(obj)}, status=200)
