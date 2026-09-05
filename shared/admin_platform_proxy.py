"""青岛电商中台 admin_platform HTTP 转发（mall catalog / 网关共用）。"""

from __future__ import annotations

import uuid

import httpx
from django.conf import settings
from django.http import HttpResponse


FORWARDED_HEADERS = ("Authorization", "token", "X-Channel", "X-Request-ID", "X-Caller-Context")


def admin_platform_base() -> str:
    return (
        getattr(settings, "UTOO_ADMIN_PLATFORM_SERVICE_URL", None)
        or getattr(settings, "ADMIN_PLATFORM_SERVICE_URL", None)
        or "http://127.0.0.1:18091"
    ).rstrip("/")


def proxy_admin_platform(request, *, upstream_path: str) -> HttpResponse:
    """转发到 platform/admin_platform，upstream_path 形如 /api/goods/goods_list.ajax。"""
    path = upstream_path if upstream_path.startswith("/") else f"/{upstream_path}"
    if not path.startswith("/api/"):
        path = f"/api/{path.lstrip('/')}"
    # 允许调用方已组好 headers（含桥接 token）；否则从 request.headers 取
    if isinstance(getattr(request, "headers", None), dict):
        headers = dict(request.headers)
    else:
        headers = {name: request.headers[name] for name in FORWARDED_HEADERS if name in request.headers}
    headers.setdefault("X-Request-ID", uuid.uuid4().hex)
    headers.setdefault("X-Channel", "mall_qd")
    token = getattr(settings, "UPSTREAM_INTERNAL_SERVICE_TOKEN", "") or ""
    if token:
        headers["X-Internal-Service-Token"] = token
    ct = getattr(request, "content_type", None)
    if ct and "Content-Type" not in headers:
        headers["Content-Type"] = ct
    timeout = float(getattr(settings, "SERVICE_PROXY_TIMEOUT_SECONDS", 30) or 30)
    try:
        upstream = httpx.request(
            request.method,
            f"{admin_platform_base()}{path}",
            params=getattr(request, "query_params", None) or getattr(request, "GET", None),
            content=getattr(request, "body", None) or None,
            headers=headers,
            timeout=timeout,
            trust_env=False,
        )
    except httpx.HTTPError:
        return HttpResponse(
            b'{"res":1,"resMsg":"admin_platform \xe4\xb8\xad\xe5\x8f\xb0\xe4\xb8\x8d\xe5\x8f\xaf\xe7\x94\xa8"}',
            status=503,
            content_type="application/json",
        )
    content_type = upstream.headers.get("Content-Type", "application/json")
    return HttpResponse(upstream.content, status=upstream.status_code, content_type=content_type)
