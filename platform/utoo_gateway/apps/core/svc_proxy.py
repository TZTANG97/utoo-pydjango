"""网关 → 微服务 HTTP 转发（MS-1+）"""
from __future__ import annotations

import json
import logging

import httpx
from django.conf import settings
from django.core.exceptions import RequestDataTooBig
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
    """QueryDict/dict → 单值 dict，避免 json 序列化成 list。

    仅展开「单元素且元素为标量」的 list（QueryDict 常见形态）。
    禁止展开 children / checkChilds 等对象数组，否则
    children:[{...}] 会变成 {...}，上游 _parse_children_payload 丢弃产品行，
    表现为子单编辑保存成功但测试人员/平台/预计完成时间不回写。
    """
    if data is None:
        return {}
    keys = getattr(data, "keys", None)
    if not callable(keys):
        return {}
    out: dict = {}
    for k in data.keys():
        v = data.get(k) if hasattr(data, "get") else data[k]
        if (
            isinstance(v, list)
            and len(v) == 1
            and not isinstance(v[0], (dict, list))
        ):
            v = v[0]
        out[k] = v
    return out


def _upload_too_large_response(service_name: str) -> Response:
    return Response(
        {
            "code": 413,
            "message": f"{service_name}拒绝：上传文件过大（HTTP 413），请压缩后重试或联系管理员提高上限",
            "data": None,
            "res": False,
            "resMsg": "上传文件过大，请压缩后重试",
        },
        status=413,
    )


def _safe_request_body(request: Request, *, service_name: str) -> bytes | Response:
    """读取原始 body；超限时返回统一 JSON，避免 Django HTML 413。"""
    try:
        return request.body
    except RequestDataTooBig:
        return _upload_too_large_response(service_name)


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
                    body = _safe_request_body(request, service_name=service_name)
                    if isinstance(body, Response):
                        return body
                    upstream = client.post(
                        url, content=body, params=params, headers=headers
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
                    body = _safe_request_body(request, service_name=service_name)
                    if isinstance(body, Response):
                        return body
                    upstream = client.post(
                        url, content=body, params=params, headers=headers
                    )
            else:
                body = _safe_request_body(request, service_name=service_name)
                if isinstance(body, Response):
                    return body
                upstream = client.request(
                    request.method,
                    url,
                    content=body,
                    params=params,
                    headers=headers,
                )
    except RequestDataTooBig:
        return _upload_too_large_response(service_name)
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
            return _upload_too_large_response(service_name)
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


def public_api_path(path: str) -> str:
    """biz → `/api/_internal/...` 回落时剥掉 `_internal`，命中中台公开路径。"""
    prefix = "/api/_internal/"
    if path.startswith(prefix):
        return "/api/" + path[len(prefix) :]
    return path


def svc_identity_url() -> str:
    return (getattr(settings, "SVC_IDENTITY_URL", "") or "").strip().rstrip("/")


def svc_identity_enabled() -> bool:
    return bool(svc_identity_url())


def forward_identity(request: Request, path: str) -> Response | HttpResponse:
    return forward_request(
        request,
        base_url=svc_identity_url(),
        path=public_api_path(path),
        service_name="身份中台",
    )


def identity_get(path: str, *, token: str, channel: str = "admin") -> Response:
    """网关主动 GET 调 identity（避免把前端 POST 误转发到写接口）。"""
    import httpx
    from rest_framework.response import Response as DrfResponse

    url = f"{svc_identity_url()}{path if path.startswith('/') else '/' + path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "token": token,
        "X-Channel": channel,
        "Accept": "application/json",
    }
    try:
        upstream = httpx.get(url, headers=headers, timeout=15, trust_env=False)
    except httpx.HTTPError:
        return DrfResponse({"code": 503, "message": "身份中台不可用", "data": None}, status=503)
    try:
        body = upstream.json()
    except ValueError:
        body = {"code": 502, "message": "身份中台返回非 JSON", "data": None}
    return DrfResponse(body, status=upstream.status_code)


def identity_password_login(login_name: str, password: str, *, channel: str) -> dict:
    """网关适配层：用账号密码直调中台（小程序 query 登录等无法原样转发 body 时）。"""
    import httpx

    url = f"{svc_identity_url()}/api/v1/identity/auth/login"
    upstream = httpx.post(
        url,
        json={"loginName": login_name, "password": password},
        headers={"X-Channel": channel, "Content-Type": "application/json"},
        timeout=15,
    )
    try:
        return {"http_status": upstream.status_code, "body": upstream.json()}
    except ValueError:
        return {"http_status": upstream.status_code, "body": {"code": 502, "message": "身份中台返回非 JSON"}}


def svc_order_url() -> str:
    return (getattr(settings, "SVC_ORDER_URL", "") or "").strip().rstrip("/")


def svc_order_enabled() -> bool:
    return bool(svc_order_url())


def forward_order(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_order_url(),
        path=public_api_path(path),
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
        path=public_api_path(path),
        service_name="支付服务",
    )


def svc_invoice_url() -> str:
    """发票已并入 platform：显式 SVC_INVOICE_URL，否则回落 SVC_ADMIN_PLATFORM_URL。"""
    explicit = (getattr(settings, "SVC_INVOICE_URL", "") or "").strip().rstrip("/")
    if explicit:
        return explicit
    return svc_admin_platform_url()


def svc_invoice_enabled() -> bool:
    return bool(svc_invoice_url())


def forward_invoice(request: Request, path: str) -> Response:
    return forward_request(
        request,
        base_url=svc_invoice_url(),
        path=public_api_path(path),
        service_name="发票服务",
    )


def svc_entry_url() -> str:
    """入驻已并入 platform：显式 SVC_ENTRY_URL，否则回落 SVC_ADMIN_PLATFORM_URL。"""
    explicit = (getattr(settings, "SVC_ENTRY_URL", "") or "").strip().rstrip("/")
    if explicit:
        return explicit
    return svc_admin_platform_url()


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


def svc_utoo_biz_url() -> str:
    return (getattr(settings, "UTOO_BIZ_SERVICE_URL", "") or "").strip().rstrip("/")


def svc_utoo_biz_enabled() -> bool:
    return bool(svc_utoo_biz_url())


# --- 阶段 D / P3：网关 BFF-only + 生产启动门禁（禁止公开 twin 回退）---

BFF_REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "UTOO_BIZ_SERVICE_URL",
    "SVC_IDENTITY_URL",
    "SVC_ORDER_URL",
    "SVC_PAYMENT_URL",
    "SVC_WX_URL",
    "SVC_ADMIN_ASSET_URL",
    "SVC_ADMIN_PLATFORM_URL",
)

_TRUTHY = ("1", "true", "yes", "on")


def _as_bool(raw) -> bool:
    if isinstance(raw, str):
        return raw.strip().lower() in _TRUTHY
    return bool(raw)


def gateway_production_env() -> bool:
    """生产态：APP_ENV=production|prod（大小写不敏感）。"""
    from django.conf import settings

    env = (getattr(settings, "APP_ENV", "") or "").strip().lower()
    return env in ("production", "prod")


def gateway_bff_only_enabled() -> bool:
    """BFF-only：UTOO_GATEWAY_BFF_ONLY 或别名 GATEWAY_BFF_ONLY。"""
    from django.conf import settings

    if _as_bool(getattr(settings, "UTOO_GATEWAY_BFF_ONLY", False)):
        return True
    if _as_bool(getattr(settings, "GATEWAY_BFF_ONLY", False)):
        return True
    return False


def gateway_enforce_mid_config() -> bool:
    """须配齐关键 SVC_* 并拒绝公开 twin：生产 或 BFF-only。"""
    return gateway_production_env() or gateway_bff_only_enabled()


def gateway_twin_public_enabled() -> bool:
    """公开路径是否仍允许挂载本地 twin。

    生产 / BFF-only / 已配 utoo_biz → **一律 False**（禁止 silent 开 twin）。
    注意（方案 B / V3）：即便本开关为 True、本地 twin 视图仍被 urls 挂载，
    凡已挂中台归属的 `forward_*_first` 在未配对应 `SVC_*_URL` 时一律 **503**，
    不再 silent 执行本地落库。本开关只影响「未装饰 / 故意 GW-LOCAL」路径
    （如 wechatconfig、lab expOrderList、wx stubs）；Platform/invoice/entry
    路由组永不 twin（始终 proxy，缺配 503）。
    """
    if gateway_enforce_mid_config():
        return False
    if svc_utoo_biz_enabled():
        return False
    return True


def mid_svc_unconfigured_response(service_label: str, env_hint: str) -> Response:
    """已挂中台的路径：缺 SVC/mid URL → 503（禁止 silent twin）。"""
    return Response(
        {
            "code": 503,
            "message": f"{service_label}未配置（请设置 {env_hint}）",
            "data": None,
        },
        status=503,
    )


def _env_url(key: str) -> str:
    from django.conf import settings

    return (getattr(settings, key, "") or "").strip().rstrip("/")


def bff_services_configured() -> tuple[bool, list[str]]:
    """BFF-only / 生产所需上游是否齐全；invoice/entry 可并入 platform。"""
    missing: list[str] = []
    for key in BFF_REQUIRED_ENV_KEYS:
        if not _env_url(key):
            missing.append(key)
    platform = _env_url("SVC_ADMIN_PLATFORM_URL")
    if not _env_url("SVC_INVOICE_URL") and not platform:
        missing.append("SVC_INVOICE_URL(or SVC_ADMIN_PLATFORM_URL)")
    if not _env_url("SVC_ENTRY_URL") and not platform:
        missing.append("SVC_ENTRY_URL(or SVC_ADMIN_PLATFORM_URL)")
    return (len(missing) == 0, missing)


def validate_bff_gateway_config(*, raise_error: bool = True) -> list[str]:
    """启动 / CI：生产或 BFF-only 时校验关键 SVC_*；缺配拒绝启动（或返回 missing）。"""
    if not gateway_enforce_mid_config():
        return []
    ok, missing = bff_services_configured()
    if ok:
        return []
    mode = []
    if gateway_production_env():
        mode.append("APP_ENV=production")
    if gateway_bff_only_enabled():
        mode.append("UTOO_GATEWAY_BFF_ONLY/GATEWAY_BFF_ONLY")
    msg = (
        f"网关启动门禁（{'+'.join(mode)}）缺少上游配置："
        + ", ".join(missing)
        + "。请配置 SVC_*_URL 与 UTOO_BIZ_SERVICE_URL；生产禁止依赖公开 twin。"
    )
    if raise_error:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(msg)
    return missing
