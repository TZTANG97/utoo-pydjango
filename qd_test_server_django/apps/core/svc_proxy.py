"""网关 → 微服务 HTTP 转发（MS-1+）"""
from __future__ import annotations

import json
import logging

import httpx
from django.conf import settings
from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.drf_request import as_drf_request

logger = logging.getLogger(__name__)

_FORWARD_HEADERS = (
    "Authorization",
    "Content-Type",
    "Accept",
    "token",
    "X-Channel",  # 中台渠道：admin / pc / wx，透传给上游，不据此拆服务
    # IOT → UTOO HMAC 回调（缺任一都会被验签判为「缺少签名头」）
    "X-IOT-App-Id",
    "X-IOT-Timestamp",
    "X-IOT-Nonce",
    "X-IOT-Signature",
)

_BINARY_CT_HINTS = (
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/msword",
    "application/vnd.",
    "image/",
    "audio/",
    "video/",
    "text/csv",
    "text/plain",
)


def _is_binary_upstream(upstream: httpx.Response) -> bool:
    """附件下载 / 导出等非 JSON 响应用于透传，避免误报 502。"""
    ct = (upstream.headers.get("content-type") or "").lower()
    cd = (upstream.headers.get("content-disposition") or "").lower()
    if "attachment" in cd or "filename=" in cd or "filename*" in cd:
        return True
    return any(h in ct for h in _BINARY_CT_HINTS)


def _passthrough_binary(upstream: httpx.Response) -> HttpResponse:
    ct = upstream.headers.get("content-type") or "application/octet-stream"
    resp = HttpResponse(upstream.content, status=upstream.status_code, content_type=ct)
    for header in ("Content-Disposition", "Content-Length", "Cache-Control", "Content-Type"):
        val = upstream.headers.get(header)
        if not val:
            continue
        try:
            resp[header] = val
        except (UnicodeEncodeError, ValueError):
            # 跳过非法头，仍返回文件体
            logger.warning("skip upstream header %s", header)
    return resp


def svc_auth_url() -> str:
    return (getattr(settings, "SVC_AUTH_URL", "") or "").strip().rstrip("/")


def svc_auth_enabled() -> bool:
    return bool(svc_auth_url())


def _plain_form_dict(data) -> dict:
    """QueryDict/dict → 单值 dict，避免 json 序列化成 list。"""
    if data is None:
        return {}
    keys = getattr(data, "keys", None)
    if not callable(keys):
        return {}
    out: dict = {}
    for k in data.keys():
        v = data.get(k) if hasattr(data, "get") else data[k]
        if isinstance(v, list) and len(v) == 1:
            v = v[0]
        out[k] = v
    return out


def forward_request(
    request: Request,
    *,
    base_url: str,
    path: str,
    service_name: str = "上游服务",
) -> Response | HttpResponse:
    # forward_*_first 在 @api_view 外侧时拿到的是 WSGIRequest；统一提升为 DRF Request
    request = as_drf_request(request)
    url = f"{base_url.rstrip('/')}{path}"
    headers = {}
    for key in _FORWARD_HEADERS:
        meta = f"HTTP_{key.upper().replace('-', '_')}"
        val = request.META.get(meta)
        if val:
            headers[key] = val
    if "Content-Type" not in headers and request.content_type:
        headers["Content-Type"] = request.content_type
    params = dict(request.query_params)
    path_l = (path or "").lower()
    is_download = "downloadfile" in path_l or "export" in path_l or "download" in path_l
    try:
        # 本机微服务转发禁止走系统 HTTP_PROXY，否则上游宕机会变成空 502 被误报为「非 JSON」
        # 大文件上传 / 附件下载需要更长超时
        timeout = 120.0 if (request.method.upper() == "POST" or is_download) else 30.0
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            if request.method.upper() == "GET":
                upstream = client.get(url, params=params, headers=headers)
            elif request.method.upper() == "POST":
                ct = (request.content_type or "").lower()
                # HMAC 回调依赖「原始 body + 签名头」；重编码会改字节串导致验签失败。
                preserve_raw_body = bool(
                    request.META.get("HTTP_X_IOT_SIGNATURE")
                    or ("/api/iot/callback/" in (path or "").lower())
                )
                # form/multipart 必须原样透传 body；勿用 json= 重编码，
                # 否则 headers 里残留的 form Content-Type 会导致上游解析不到参数。
                if preserve_raw_body:
                    upstream = client.post(
                        url, content=request.body, params=params, headers=headers
                    )
                elif "application/json" in ct:
                    fwd = {k: v for k, v in headers.items() if k.lower() != "content-type"}
                    # submitExpOrder 等接口 body 为 JSON 数组；_plain_form_dict 只认 dict，
                    # list 会被当成 {} 转发，上游报「订单没有数据」。
                    raw = request.data
                    if isinstance(raw, list):
                        json_payload = raw
                    else:
                        json_payload = _plain_form_dict(raw)
                    upstream = client.post(
                        url,
                        json=json_payload,
                        params=params,
                        headers={**fwd, "Content-Type": "application/json"},
                    )
                else:
                    upstream = client.post(
                        url, content=request.body, params=params, headers=headers
                    )
            else:
                upstream = client.request(
                    request.method,
                    url,
                    content=request.body,
                    params=params,
                    headers=headers,
                )
    except httpx.RequestError as exc:
        logger.exception("forward %s failed: %s", url, exc)
        return Response(
            {"code": 503, "message": f"{service_name}不可用：{exc}", "data": None},
            status=503,
        )
    # 附件/导出：直接透传二进制，勿当 JSON
    if _is_binary_upstream(upstream) and upstream.status_code < 400:
        return _passthrough_binary(upstream)
    try:
        data = upstream.json()
    except json.JSONDecodeError:
        if _is_binary_upstream(upstream) and upstream.status_code < 500:
            return _passthrough_binary(upstream)
        body = (upstream.content or b"").decode("utf-8", errors="replace").strip()
        host = base_url.rstrip("/")
        if upstream.status_code == 413:
            return Response(
                {
                    "code": 413,
                    "message": f"{service_name}拒绝：上传文件过大（HTTP 413），请压缩后重试或联系管理员提高上限",
                    "data": None,
                },
                status=413,
            )
        if upstream.status_code >= 500 or not body:
            return Response(
                {
                    "code": 502,
                    "message": (
                        f"{service_name}不可用（HTTP {upstream.status_code}，"
                        f"请确认已启动：{host}）"
                    ),
                    "data": None,
                },
                status=502,
            )
        return Response(
            {
                "code": 502,
                "message": f"{service_name}返回非 JSON（HTTP {upstream.status_code}）",
                "data": None,
            },
            status=502,
        )
    return Response(data, status=upstream.status_code)


def forward_auth(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_auth_url(),
        path=path,
        service_name="认证服务",
    )


def svc_order_url() -> str:
    return (getattr(settings, "SVC_ORDER_URL", "") or "").strip().rstrip("/")


def svc_order_enabled() -> bool:
    return bool(svc_order_url())


def forward_order(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_order_url(),
        path=path,
        service_name="订单服务",
    )


def svc_payment_url() -> str:
    return (getattr(settings, "SVC_PAYMENT_URL", "") or "").strip().rstrip("/")


def svc_payment_enabled() -> bool:
    return bool(svc_payment_url())


def forward_payment(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_payment_url(),
        path=path,
        service_name="支付服务",
    )


def svc_invoice_url() -> str:
    return (getattr(settings, "SVC_INVOICE_URL", "") or "").strip().rstrip("/")


def svc_invoice_enabled() -> bool:
    return bool(svc_invoice_url())


def forward_invoice(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_invoice_url(),
        path=path,
        service_name="发票服务",
    )


def svc_entry_url() -> str:
    return (getattr(settings, "SVC_ENTRY_URL", "") or "").strip().rstrip("/")


def svc_entry_enabled() -> bool:
    return bool(svc_entry_url())


def forward_entry(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_entry_url(),
        path=path,
        service_name="讨论区服务",
    )


def svc_wx_url() -> str:
    return (getattr(settings, "SVC_WX_URL", "") or "").strip().rstrip("/")


def svc_wx_enabled() -> bool:
    return bool(svc_wx_url())


def forward_wx(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_wx_url(),
        path=path,
        service_name="微信服务",
    )


def svc_admin_asset_url() -> str:
    return (getattr(settings, "SVC_ADMIN_ASSET_URL", "") or "").strip().rstrip("/")


def svc_admin_asset_enabled() -> bool:
    return bool(svc_admin_asset_url())


def forward_admin_asset(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_admin_asset_url(),
        path=path,
        service_name="后台Asset服务",
    )


def svc_admin_platform_url() -> str:
    return (getattr(settings, "SVC_ADMIN_PLATFORM_URL", "") or "").strip().rstrip("/")


def svc_admin_platform_enabled() -> bool:
    return bool(svc_admin_platform_url())


def forward_admin_platform(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_admin_platform_url(),
        path=path,
        service_name="后台Platform服务",
    )
