"""网关 → 入驻服务转发（已并入 qd_svc_admin_platform）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import forward_entry, svc_entry_enabled


def forward_entry_first(view_func):
    """DRF 视图最外层：启用 SVC_ENTRY_URL 时透明转发 request.path。"""

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_entry_enabled():
            return as_django_response(
                forward_entry(as_drf_request(request), request.path)
            )
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_entry_request(request: Request, subpath: str = "") -> Response:
    return forward_entry(request, request.path)
