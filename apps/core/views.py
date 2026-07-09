from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.core.responses import api_ok


def health(request):
    body = {"status": "ok", "service": "qd_test_server_django", "framework": "django"}
    if settings.PAY_DEBUG_ENABLED:
        body["payDebug"] = "/dev/pay-debug"
    return JsonResponse(body)


def root(request):
    body = {
        "message": "青岛检测平台 API",
        "version": "0.1.0-d0",
        "framework": "django",
        "health": "/health",
    }
    if settings.PAY_DEBUG_ENABLED:
        body["payDebug"] = "/dev/pay-debug"
    return JsonResponse(body)


@api_view(["GET"])
def api_health(request):
    return Response(
        api_ok(
            {
                "status": "ok",
                "service": "qd_test_server_django",
                "app_env": settings.APP_ENV,
            }
        )
    )
