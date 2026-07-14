from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from qd_common.responses import api_ok


def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "qd_svc_admin_platform",
            "framework": "django",
            "port": settings.SERVER_PORT_HTTP,
        }
    )


def root(request):
    return JsonResponse(
        {
            "service": "qd_svc_admin_platform",
            "message": "平台后台微服务（系统/会员/运营/服务/订单设置 + 入驻/发票）",
            "health": "/health",
        }
    )


@api_view(["GET"])
def api_health(request):
    return Response(
        api_ok(
            {
                "status": "ok",
                "service": "qd_svc_admin_platform",
                "port": settings.SERVER_PORT_HTTP,
            }
        )
    )
