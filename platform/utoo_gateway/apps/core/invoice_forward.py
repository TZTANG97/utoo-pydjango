"""网关 → 发票服务转发（已并入 qd_svc_admin_platform）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_invoice,
    mid_svc_unconfigured_response,
    svc_invoice_enabled,
)


def forward_invoice_first(view_func):
    """已挂 invoice/platform：配了 URL 只转发；未配 → 503（禁止 silent twin）。

    须把原始 WSGIRequest 转为 DRF Request，否则访问 query_params 会 500。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_invoice_enabled():
            return as_django_response(
                mid_svc_unconfigured_response(
                    "发票中台",
                    "SVC_INVOICE_URL 或 SVC_ADMIN_PLATFORM_URL",
                )
            )
        return as_django_response(
            forward_invoice(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_invoice_request(request: Request, subpath: str = "") -> Response:
    if not svc_invoice_enabled():
        return mid_svc_unconfigured_response(
            "发票中台",
            "SVC_INVOICE_URL 或 SVC_ADMIN_PLATFORM_URL",
        )
    return forward_invoice(request, request.path)
