"""网关 → qd_svc_admin_asset 转发"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.svc_proxy import forward_admin_asset, svc_admin_asset_enabled


def forward_admin_asset_first(view_func):
    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_admin_asset_enabled():
            return forward_admin_asset(request, request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_admin_asset_request(request: Request, subpath: str = "") -> Response:
    return forward_admin_asset(request, request.path)
