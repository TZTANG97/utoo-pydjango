"""网关 → qd_svc_payment 转发（MS-3）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.svc_proxy import forward_payment, svc_payment_enabled


def forward_payment_first(view_func):
    """DRF 视图最外层：启用 SVC_PAYMENT_URL 时透明转发 request.path。"""

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_payment_enabled():
            return forward_payment(request, request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_payment_request(request: Request, subpath: str = "") -> Response:
    return forward_payment(request, request.path)
