import json
from functools import wraps
from uuid import UUID

from django.http import JsonResponse, HttpRequest
from django.core.exceptions import ValidationError as DjangoValidationError

from .exceptions import ApiValidationError, BadRequestError, NotFoundError


def json_body(request: HttpRequest) -> dict:
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise BadRequestError("Invalid JSON body.")


def parse_uuid(value: str):
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        raise BadRequestError("Invalid UUID format.")


def handle_api_errors(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except ApiValidationError as e:
            return JsonResponse({"errors": e.errors}, status=e.status_code)
        except BadRequestError as e:
            return JsonResponse({"detail": e.message}, status=e.status_code)
        except NotFoundError as e:
            return JsonResponse({"detail": e.message}, status=e.status_code)
        except DjangoValidationError as e:
            return JsonResponse({"errors": e.message_dict}, status=400)

    return wrapper
