"""网关 → qd_svc_admin_platform 转发"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_admin_platform,
    mid_svc_unconfigured_response,
    svc_admin_platform_enabled,
)


def forward_admin_platform_first(view_func):
    """已挂 platform：配了 SVC_ADMIN_PLATFORM_URL 只转发；未配 → 503（禁止 silent twin）。"""

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_admin_platform_enabled():
            return as_django_response(
                mid_svc_unconfigured_response(
                    "后台Platform中台",
                    "SVC_ADMIN_PLATFORM_URL",
                )
            )
        return as_django_response(
            forward_admin_platform(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_admin_platform_request(request: Request, subpath: str = "") -> Response:
    if not svc_admin_platform_enabled():
        return mid_svc_unconfigured_response(
            "后台Platform中台",
            "SVC_ADMIN_PLATFORM_URL",
        )
    return forward_admin_platform(request, request.path)
