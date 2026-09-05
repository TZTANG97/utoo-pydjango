"""网关 → qd_svc_admin_asset 转发"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import (
    forward_admin_asset,
    mid_svc_unconfigured_response,
    svc_admin_asset_enabled,
)


def _upstream_missing(upstream: Response) -> bool:
    data = upstream.data if isinstance(upstream, Response) else None
    msg = ""
    if isinstance(data, dict):
        msg = str(data.get("message") or data.get("msg") or "")
    return upstream.status_code in (404, 502) and (
        "非 JSON" in msg
        or "Not Found" in msg
        or "不可用" in msg
        or upstream.status_code == 404
    )


def _local_asset_fallback(request: Request):
    """仅故意 GW-LOCAL 白名单（lab expOrderList）；禁止一般 silent twin。"""
    path = (getattr(request, "path", "") or "").split("?")[0].rstrip("/")
    if path in (
        "/api/labPerformanceSaleuser/expOrderList.ajax",
        "/api/adminLabSale/expOrderList.ajax",
    ):
        # 该 view 不挂 forward_*，可直接调用，避免循环转发
        from apps.admin_digital.views.digital import lab_sale_order_list

        return lab_sale_order_list(request)
    return None


def forward_admin_asset_first(view_func):
    """已挂 asset：配了 SVC_ADMIN_ASSET_URL 只转发；未配 → 503（禁止 silent twin）。

    lab expOrderList 不经本装饰器（urls 精确挂 GW-LOCAL）。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if not svc_admin_asset_enabled():
            return as_django_response(
                mid_svc_unconfigured_response(
                    "后台Asset中台",
                    "SVC_ADMIN_ASSET_URL",
                )
            )
        return as_django_response(
            forward_admin_asset(as_drf_request(request), request.path)
        )

    return wrapper


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_admin_asset_request(request: Request, subpath: str = "") -> Response:
    """Prefix 代理；仅 lab expOrderList 白名单可本地回落。"""
    del subpath
    if not svc_admin_asset_enabled():
        return mid_svc_unconfigured_response(
            "后台Asset中台",
            "SVC_ADMIN_ASSET_URL",
        )
    upstream = forward_admin_asset(request, request.path)
    if _upstream_missing(upstream):
        local = _local_asset_fallback(as_drf_request(request))
        if local is not None:
            return local
    return upstream
