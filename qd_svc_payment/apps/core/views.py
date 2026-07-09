from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from qd_common.responses import api_ok


def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "qd_svc_payment",
            "framework": "django",
            "port": settings.SERVER_PORT_HTTP,
        }
    )


def root(request):
    return JsonResponse(
        {
            "message": "QD 支付微服务",
            "service": "qd_svc_payment",
            "health": "/health",
        }
    )


@api_view(["GET"])
def api_health(request):
    return Response(api_ok({"status": "ok", "service": "qd_svc_payment"}))
