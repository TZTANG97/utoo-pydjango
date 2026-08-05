"""网关 → qd_svc_admin_asset 转发"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import forward_admin_asset, svc_admin_asset_enabled


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
    """Asset 缺路由时回退到网关本地实现。"""
    path = (getattr(request, "path", "") or "").split("?")[0].rstrip("/")
    if path in (
        "/api/labPerformanceSaleuser/expOrderList.ajax",
        "/api/adminLabSale/expOrderList.ajax",
    ):
        # 该 view 不挂 forward_*，可直接调用，避免循环转发
        from apps.admin_digital.views.digital import lab_sale_order_list

        return lab_sale_order_list(request)
    # 留存仓库下拉：Asset 旧版缺路由时回退网关本地
    if path.endswith("/sampleremainstoreHouse/queryStore.ajax"):
        from apps.admin_inventory.views import inventory as inv

        return inv.remain_sample_order_options(request)
    if path.endswith("/sampleremainstoreHouse/queryListByStoreId.ajax"):
        from apps.admin_inventory.views import inventory as inv

        return inv.sample_store_positions(request)
    return None


def forward_admin_asset_first(view_func):
    """DRF 视图最外层：启用 SVC_ADMIN_ASSET_URL 时透明转发 request.path。

    上游 404 / 非 JSON（常见于 Asset 尚未同步某接口）时回退到网关本地实现。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_admin_asset_enabled():
            upstream = forward_admin_asset(as_drf_request(request), request.path)
            if _upstream_missing(upstream):
                return view_func(request, *args, **kwargs)
            return as_django_response(upstream)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_admin_asset_request(request: Request, subpath: str = "") -> Response:
    """Prefix 代理；上游缺路由时回退网关本地白名单接口。"""
    del subpath
    upstream = forward_admin_asset(request, request.path)
    if _upstream_missing(upstream):
        local = _local_asset_fallback(as_drf_request(request))
        if local is not None:
            return local
    return upstream
