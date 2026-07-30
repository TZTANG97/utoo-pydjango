"""网关 → qd_svc_payment 转发（MS-3）"""
from __future__ import annotations

from functools import wraps

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_django_response, as_drf_request
from apps.core.svc_proxy import forward_payment, svc_payment_enabled


def forward_payment_first(view_func):
    """DRF 视图最外层：启用 SVC_PAYMENT_URL 时透明转发 request.path。

    上游 404 / 非 JSON（常见于支付服务尚未同步某接口）时回退到网关本地实现，
    避免「我的资产」等页整页弹 502 提示。
    """

    @wraps(view_func)
    def wrapper(request: Request, *args, **kwargs):
        if svc_payment_enabled():
            upstream = forward_payment(as_drf_request(request), request.path)
            data = upstream.data if isinstance(upstream, Response) else None
            msg = ""
            if isinstance(data, dict):
                msg = str(data.get("message") or data.get("msg") or "")
            # 上游路由缺失或返回 HTML 404/非 JSON 时，走本地兜底
            if upstream.status_code in (404, 502) and (
                "非 JSON" in msg or "Not Found" in msg or upstream.status_code == 404
            ):
                return view_func(request, *args, **kwargs)
            return as_django_response(upstream)
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def proxy_payment_request(request: Request, subpath: str = "") -> Response:
    return forward_payment(request, request.path)
