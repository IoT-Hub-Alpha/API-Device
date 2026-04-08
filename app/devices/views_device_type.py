from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from iot_auth.django import CheckPermissionsMixin

from .models import DeviceType
from .serializers import (
    DeviceTypeReadSerializer,
    DeviceTypeValidator,
    DeviceTypeRepository,
)
from .exceptions import NotFoundError
from .views_common import json_body, parse_uuid, handle_api_errors


@method_decorator(csrf_exempt, name="dispatch")
class DeviceTypeListView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["device_types.view"],
        "post": ["device_types.add"],
    }
    default_page_size = 10

    @handle_api_errors
    def get(self, request):
        qs = DeviceType.objects.order_by("name")

        # --- Search ---
        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        # --- Filter by metric_name ---
        metric_name = request.GET.get("metric_name", "").strip()
        if metric_name:
            qs = qs.filter(metric_name=metric_name)

        # --- Pagination ---
        page_number = request.GET.get("page", 1)
        page_size = int(request.GET.get("page_size", self.default_page_size))
        paginator = Paginator(qs, page_size)

        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            return JsonResponse({"errors": {"page": "Invalid page"}}, status=400)

        data = [
            DeviceTypeReadSerializer(instance=obj).to_dict()
            for obj in page_obj.object_list
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
        cleaned = DeviceTypeValidator(data=payload, partial=False).validate()
        device_type = DeviceTypeRepository.save(cleaned)
        return JsonResponse(
            {"data": DeviceTypeReadSerializer(instance=device_type).to_dict()},
            status=201,
        )


@method_decorator(csrf_exempt, name="dispatch")
class DeviceTypeDetailView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["device_types.view"],
        "patch": ["device_types.change"],
        "put": ["device_types.change"],
        "delete": ["device_types.delete"],
    }

    def _get_or_404(self, pk):
        try:
            uuid_obj = parse_uuid(pk)
            return DeviceType.objects.get(id=uuid_obj)
        except DeviceType.DoesNotExist:
            raise NotFoundError("DeviceType not found.")

    @handle_api_errors
    def get(self, request: HttpRequest, device_type_id):
        obj = self._get_or_404(device_type_id)
        return JsonResponse(
            {"data": DeviceTypeReadSerializer(instance=obj).to_dict()}, status=200
        )

    def patch(self, request: HttpRequest, device_type_id):
        return self._update(request, device_type_id, partial=True)

    def put(self, request: HttpRequest, device_type_id):
        return self._update(request, device_type_id, partial=False)

    @handle_api_errors
    def delete(self, request: HttpRequest, device_type_id):
        obj = self._get_or_404(device_type_id)
        with transaction.atomic():
            obj.delete()
        return HttpResponse(status=204)

    @transaction.atomic
    @handle_api_errors
    def _update(self, request: HttpRequest, device_type_id, partial: bool):
        obj = self._get_or_404(device_type_id)

        payload = json_body(request)
        cleaned = DeviceTypeValidator(
            data=payload, partial=partial, instance=obj
        ).validate()
        updated = DeviceTypeRepository.save(cleaned, instance=obj)
        return JsonResponse(
            {"data": DeviceTypeReadSerializer(instance=updated).to_dict()}, status=200
        )
