"""网关 → utoo_biz 转发（阶段 A：实验订单主链）。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_drf_request
from apps.core.svc_proxy import forward_request, svc_utoo_biz_enabled, svc_utoo_biz_url


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_utoo_biz_request(request: Request, subpath: str = "", **_kwargs) -> Response:
    if not svc_utoo_biz_enabled():
        return Response(
            {"code": 503, "message": "愉兔业务服务未配置（请设置 UTOO_BIZ_SERVICE_URL 并启动 utoo_biz）", "data": None},
            status=503,
        )
    drf = as_drf_request(request)
    return forward_request(
        drf,
        base_url=svc_utoo_biz_url(),
        path=drf.path,
        service_name="愉兔业务服务",
    )
