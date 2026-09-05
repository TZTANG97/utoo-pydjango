"""网关 → 入驻服务转发（已并入 qd_svc_admin_platform）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_entry,
    mid_svc_unconfigured_response,
    svc_entry_enabled,
)


def forward_entry_first(view_func):
    """已挂 entry/platform：配了 URL 只转发；未配 → 503（禁止 silent twin）。"""

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_entry_enabled():
            return as_django_response(
                mid_svc_unconfigured_response(
                    "入驻/讨论区中台",
                    "SVC_ENTRY_URL 或 SVC_ADMIN_PLATFORM_URL",
                )
            )
        return as_django_response(
            forward_entry(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_entry_request(request: Request, subpath: str = "") -> Response:
    if not svc_entry_enabled():
        return mid_svc_unconfigured_response(
            "入驻/讨论区中台",
            "SVC_ENTRY_URL 或 SVC_ADMIN_PLATFORM_URL",
        )
    return forward_entry(request, request.path)
