"""网关 → qd_svc_order 转发（MS-2）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_order,
    mid_svc_unconfigured_response,
    svc_order_enabled,
)


def forward_order_first(view_func):
    """已挂 order：配了 SVC_ORDER_URL 只转发；未配 → 503（禁止 silent twin）。"""

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_order_enabled():
            return as_django_response(
                mid_svc_unconfigured_response("订单中台", "SVC_ORDER_URL")
            )
        return as_django_response(
            forward_order(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_order_request(request: Request, subpath: str = "") -> Response:
    if not svc_order_enabled():
        return mid_svc_unconfigured_response("订单中台", "SVC_ORDER_URL")
    return forward_order(request, request.path)
