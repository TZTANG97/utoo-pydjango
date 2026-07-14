from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from qd_common.responses import api_ok


def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "qd_svc_admin_asset",
            "framework": "django",
            "port": settings.SERVER_PORT_HTTP,
        }
    )


def root(request):
    return JsonResponse(
        {
            "service": "qd_svc_admin_asset",
            "message": "数字化/库存/资金后台微服务",
            "health": "/health",
        }
    )


@api_view(["GET"])
def api_health(request):
    return Response(
        api_ok(
            {
                "status": "ok",
                "service": "qd_svc_admin_asset",
                "port": settings.SERVER_PORT_HTTP,
            }
        )
    )
