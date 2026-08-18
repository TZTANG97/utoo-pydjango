"""网关 → qd_svc_identity 公网前缀（青岛 IDENTITY_MID_SERVICE_URL 打同一 VIP）。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.svc_proxy import forward_identity, svc_identity_enabled

# 与青岛 gateway identity_mid_resource 对齐
IDENTITY_PUBLIC_EXACT = frozenset(
    {
        "auth/login",
        "auth/me",
        "auth/refresh",
        "auth/password",
        "auth/data-scope",
        "menus",
        "permissions",
    }
)
IDENTITY_PUBLIC_PREFIXES = frozenset({"departments", "roles", "users", "menus"})


def _allowed(normalized: str) -> bool:
    if normalized in IDENTITY_PUBLIC_EXACT:
        return True
    head = (normalized or "").split("/", 1)[0]
    return head in IDENTITY_PUBLIC_PREFIXES


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_identity_request(request: Request, subpath: str = "") -> Response:
    if not svc_identity_enabled():
        return Response(
            {"code": 503, "message": "身份中台未配置", "data": None},
            status=503,
        )
    normalized = (subpath or "").strip("/")
    if not _allowed(normalized):
        return Response(
            {"code": 404, "message": "不支持的身份中台路径", "data": None},
            status=404,
        )
    return forward_identity(request, request.path)
