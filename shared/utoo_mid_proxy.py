"""透明 HTTP 转发到各中台进程（utoo_biz 共用）。"""
from __future__ import annotations

import uuid

import httpx
from django.conf import settings
from django.http import HttpResponse
from rest_framework.response import Response

FORWARDED_HEADERS = (
    "Authorization",
    "token",
    "X-Channel",
    "X-Request-ID",
    "Idempotency-Key",
    "X-Utoo-List-Scope",
    "X-Utoo-Audit-Validated",
    "Content-Type",
)


def proxy_mid_path(
    request,
    path: str,
    *,
    base_url: str,
    channel: str | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: float | None = None,
    service_name: str = "上游服务",
):
    normalized = path if path.startswith("/") else f"/{path}"
    if not normalized.startswith("/api/"):
        normalized = f"/api/{normalized.lstrip('/')}"

    headers = {name: request.headers[name] for name in FORWARDED_HEADERS if name in request.headers}
    if channel:
        headers["X-Channel"] = channel
    headers.setdefault("X-Request-ID", uuid.uuid4().hex)
    if request.content_type and "Content-Type" not in headers:
        headers["Content-Type"] = request.content_type
    if extra_headers:
        headers.update(extra_headers)

    base = (base_url or "").rstrip("/")
    if not base:
        return Response(
            {"code": "mid_unconfigured", "message": f"{service_name}未配置"},
            status=503,
        )

    if timeout is None:
        timeout = float(getattr(settings, "UTOO_MID_PROXY_TIMEOUT_SECONDS", 15))
        path_l = normalized.lower()
        if any(k in path_l for k in ("upload", "download", "export", "notify", "pay.ajax")):
            timeout = max(timeout, 120.0)

    try:
        upstream = httpx.request(
            request.method,
            f"{base}{normalized}",
            params=request.query_params,
            content=request.body or None,
            headers=headers,
            timeout=timeout,
            trust_env=False,
        )
    except httpx.HTTPError:
        return Response(
            {"code": "mid_unavailable", "message": f"{service_name}不可用"},
            status=503,
        )

    content_type = upstream.headers.get("Content-Type", "application/json")
    response = HttpResponse(upstream.content, status=upstream.status_code, content_type=content_type)
    for h in ("Content-Disposition", "Cache-Control"):
        val = upstream.headers.get(h)
        if val:
            response[h] = val
    return response
