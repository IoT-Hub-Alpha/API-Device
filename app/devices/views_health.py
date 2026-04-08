from django.db import connection
from django.http import JsonResponse


def health(request):
    """Liveness probe."""
    return JsonResponse({"status": "ok"}, status=200)


def ready(request):
    """Readiness probe — checks database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ready"}, status=200)
    except Exception as e:
        return JsonResponse(
            {"status": "unavailable", "detail": str(e)}, status=503
        )
