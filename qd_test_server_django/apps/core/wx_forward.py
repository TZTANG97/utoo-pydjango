"""网关 → 微信接口转发（现指向 qd_svc_payment:/api/wx，原 qd_svc_wx 已废弃）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.svc_proxy import forward_wx, svc_wx_enabled


def forward_wx_first(view_func):
    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_wx_enabled():
            return forward_wx(request, request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_wx_request(request: Request, subpath: str = "") -> Response:
    del subpath
    return forward_wx(request, request.path)
