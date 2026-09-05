"""网关 → 微信接口转发（现指向 qd_svc_payment:/api/wx，原 qd_svc_wx 已废弃）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_wx,
    mid_svc_unconfigured_response,
    svc_wx_enabled,
)


def forward_wx_first(view_func):
    """已挂 wx/payment：配了 SVC_WX_URL 只转发；未配 → 503（禁止 silent twin）。

    wechatconfig 不挂本装饰器，始终 GW-LOCAL。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_wx_enabled():
            return as_django_response(
                mid_svc_unconfigured_response("微信/支付扫码服务", "SVC_WX_URL")
            )
        return as_django_response(forward_wx(as_drf_request(request), request.path))

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_wx_request(request: Request, subpath: str = "") -> Response:
    del subpath
    if not svc_wx_enabled():
        return mid_svc_unconfigured_response("微信/支付扫码服务", "SVC_WX_URL")
    return forward_wx(request, request.path)
