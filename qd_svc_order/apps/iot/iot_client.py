"""IOT HTTP 客户端：login / devices / register / cancel / get_run。"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode

from django.conf import settings

logger = logging.getLogger(__name__)


class IotClientError(Exception):
    def __init__(self, message: str, *, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _base_url() -> str:
    return str(getattr(settings, "IOT_BASE_URL", "") or "").rstrip("/")


def _timeout() -> float:
    try:
        return float(getattr(settings, "IOT_HTTP_TIMEOUT", 15) or 15)
    except (TypeError, ValueError):
        return 15.0


def _assert_header_ascii(name: str, value: str) -> str:
    """HTTP 头必须是 ASCII；误把文档占位「<与 IOT 一致>」写进 token 时会在此明确报错。"""
    v = str(value or "")
    try:
        v.encode("ascii")
    except UnicodeEncodeError as exc:
        raise IotClientError(
            f"IOT 配置项含中文/非 ASCII（{name}），请检查 .env 是否误填了文档占位符"
            f"（如「<与 IOT 一致>」），应填写 IOT 侧真实密钥。详情: {exc}"
        ) from exc
    return v


def _service_auth_headers() -> dict[str, str]:
    token = str(getattr(settings, "IOT_SERVICE_TOKEN", "") or "").strip()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        token = _assert_header_ascii("IOT_SERVICE_TOKEN", token)
        headers["Authorization"] = f"Bearer {token}"
        headers["X-UTOO-Service-Token"] = token
    return headers


def _bearer_headers(access_token: str) -> dict[str, str]:
    token = _assert_header_ascii("IOT access_token", access_token.strip())
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _url(path: str) -> str:
    base = _base_url()
    if not base:
        raise IotClientError("IOT_BASE_URL 未配置")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _request(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    query: dict | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = _url(path)
    if query:
        url = url + ("&" if "?" in url else "?") + urlencode(
            {k: v for k, v in query.items() if v is not None}
        )
    # ensure_ascii=True：JSON 用 \\uXXXX，避免中间代理/旧客户端对 UTF-8 body 出问题
    payload = json.dumps(body, ensure_ascii=True).encode("utf-8") if body is not None else None
    hdrs = headers if headers is not None else _service_auth_headers()
    for hk, hv in list(hdrs.items()):
        hdrs[hk] = _assert_header_ascii(hk, hv)
    timeout = _timeout()

    try:
        import httpx

        with httpx.Client(timeout=timeout) as client:
            resp = client.request(method.upper(), url, content=payload, headers=hdrs)
            text = resp.text or ""
            try:
                data = resp.json() if text else {}
            except Exception:
                data = {"raw": text}
            if resp.status_code >= 400:
                raise IotClientError(
                    f"IOT HTTP {resp.status_code}: {text[:300]}",
                    status=resp.status_code,
                    body=data,
                )
            return data if isinstance(data, dict) else {"data": data}
    except ImportError:
        pass
    except IotClientError:
        raise
    except UnicodeEncodeError as exc:
        logger.exception("IOT httpx header/body encode failed %s %s", method, url)
        raise IotClientError(
            f"IOT 请求编码失败（多为 .env 中 IOT_SERVICE_TOKEN 含中文占位符）: {exc}"
        ) from exc
    except Exception as exc:
        logger.exception("IOT httpx request failed %s %s", method, url)
        raise IotClientError(f"IOT 请求失败: {exc}") from exc

    req = urllib.request.Request(
        url,
        data=payload,
        headers=hdrs,
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"raw": raw}
            return data if isinstance(data, dict) else {"data": data}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw}
        raise IotClientError(
            f"IOT HTTP {exc.code}: {raw[:300]}",
            status=exc.code,
            body=data,
        ) from exc
    except Exception as exc:
        logger.exception("IOT urllib request failed %s %s", method, url)
        raise IotClientError(f"IOT 请求失败: {exc}") from exc


def login_ops(*, username: str, password: str) -> dict[str, Any]:
    """POST /nss/api/auth/login — 运维端 loginType=0。"""
    return _request(
        "POST",
        "/nss/api/auth/login",
        body={"name": username, "password": password, "loginType": "0"},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )


def register_task(payload: dict[str, Any]) -> dict[str, Any]:
    """POST /nss/api/v1/tasks/register"""
    return _request("POST", "/nss/api/v1/tasks/register", body=payload)


def cancel_task(payload: dict[str, Any]) -> dict[str, Any]:
    """POST /nss/api/v1/tasks/cancel"""
    return _request("POST", "/nss/api/v1/tasks/cancel", body=payload)


def get_run(run_id: str, *, include_series: bool = False) -> dict[str, Any]:
    """GET /nss/api/v1/runs/{runId}"""
    rid = str(run_id or "").strip()
    if not rid:
        raise IotClientError("runId 为空")
    q = {"includeSeries": "1" if include_series else "0"}
    return _request("GET", f"/nss/api/v1/runs/{rid}", query=q)


def list_devices(*, q: str = "", limit: int = 200, access_token: str = "") -> dict[str, Any]:
    """GET /nss/api/v1/devices — 需 IOT 用户 JWT（按账号权限）。"""
    token = str(access_token or "").strip()
    if not token:
        raise IotClientError("缺少 IOT 用户令牌", status=401)
    query: dict[str, Any] = {"limit": int(limit or 200), "scope": "user"}
    if str(q or "").strip():
        query["q"] = str(q).strip()
    return _request(
        "GET",
        "/nss/api/v1/devices",
        query=query,
        headers=_bearer_headers(token),
    )


def create_sso_ticket(
    *,
    access_token: str,
    refresh_token: str = "",
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """POST /nss/api/v1/sso/ticket — Service Token 写入一次性 ticket。"""
    return _request(
        "POST",
        "/nss/api/v1/sso/ticket",
        body={
            "accessToken": access_token,
            "refreshToken": refresh_token or "",
            "user": user or {},
        },
    )
