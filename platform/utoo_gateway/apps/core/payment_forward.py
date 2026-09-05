"""网关 → qd_svc_payment 转发（MS-3）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_payment,
    mid_svc_unconfigured_response,
    svc_payment_enabled,
)


def forward_payment_first(view_func):
    """已挂 payment：配了 SVC_PAYMENT_URL 只转发；未配 → 503（禁止 silent twin）。

    上游 404/不可用不再回落本地视图（方案 B：禁止 silent twin）。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_payment_enabled():
            return as_django_response(
                mid_svc_unconfigured_response("支付中台", "SVC_PAYMENT_URL")
            )
        return as_django_response(
            forward_payment(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_payment_request(request: Request, subpath: str = "") -> Response:
    if not svc_payment_enabled():
        return mid_svc_unconfigured_response("支付中台", "SVC_PAYMENT_URL")
    return forward_payment(request, request.path)
