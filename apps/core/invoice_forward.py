"""网关 → qd_svc_invoice 转发（MS-3）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.svc_proxy import forward_invoice, svc_invoice_enabled


def forward_invoice_first(view_func):
    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_invoice_enabled():
            return forward_invoice(request, request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_invoice_request(request: Request, subpath: str = "") -> Response:
    return forward_invoice(request, request.path)
