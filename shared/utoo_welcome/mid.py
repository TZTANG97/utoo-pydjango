"""welcome 中台原子读。

失败策略：
- identity helpers：返回 None → service 仅本人 + warning（禁直 SQL）。
- identity 用户 / asset 账户余额：返回 None → service **保留 JWT/入参或 0.00 + warning**（禁 SQL）。
- asset 汇率 / 公司账户 id：返回 None → service **默认 1 / 空列表 + warning**（禁直 SQL）。
- order 图表/待审/运营 count / syslog recent|page / 分包按币种 SUM：返回 None → service **空数据 + warning 日志**，
  **禁止**再 silent 直 SQL / 写库（方案 B）。
"""
from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


def _pick_url(*keys: str, default: str = "") -> str:
    for key in keys:
        val = (os.getenv(key) or "").strip().rstrip("/")
        if val:
            return val
    return default.rstrip("/")


def identity_base() -> str:
    return _pick_url(
        "UTOO_IDENTITY_MID_SERVICE_URL",
        "IDENTITY_MID_SERVICE_URL",
        "SVC_IDENTITY_URL",
        default="http://127.0.0.1:18110",
    )


def asset_base() -> str:
    return _pick_url(
        "UTOO_ASSET_MID_SERVICE_URL",
        "SVC_ADMIN_ASSET_URL",
        default="http://127.0.0.1:18090",
    )


def order_base() -> str:
    """未配显式 URL 时返回空串（调用方空数据+日志，禁止默认 localhost silent）。"""
    return _pick_url(
        "UTOO_ORDER_MID_SERVICE_URL",
        "UTOO_ORDER_SERVICE_URL",
        "SVC_ORDER_URL",
        default="",
    )


def _headers(token: str, *, channel: str = "admin") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "token": token,
        "X-Channel": channel,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _get_order_data(
    token: str,
    path: str,
    params: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any] | None:
    base = order_base()
    if not base:
        logger.warning("welcome order mid skipped (%s): order URL not configured", label)
        return None
    if not token:
        logger.warning("welcome order mid skipped (%s): no token", label)
        return None
    qs = urlencode({k: v for k, v in params.items() if v is not None and v != ""})
    url = f"{base}{path}"
    if qs:
        url = f"{url}?{qs}"
    try:
        r = httpx.get(url, headers=_headers(token), timeout=10, trust_env=False)
        if r.status_code >= 400:
            logger.warning(
                "welcome order mid %s HTTP %s: %s",
                label,
                r.status_code,
                (r.text or "")[:200],
            )
            return None
        body = r.json()
        if not isinstance(body, dict):
            return None
        if int(body.get("code") or 0) != 0:
            logger.warning("welcome order mid %s code=%s msg=%s", label, body.get("code"), body.get("message"))
            return None
        data = body.get("data")
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.warning("welcome order mid %s failed: %s", label, exc)
        return None


def fetch_identity_user(token: str, user_id: str) -> dict[str, Any] | None:
    if not token or not user_id:
        return None
    url = f"{identity_base()}/api/v1/identity/users/{user_id}"
    try:
        r = httpx.get(url, headers=_headers(token), timeout=10, trust_env=False)
        if r.status_code >= 400:
            return None
        body = r.json()
        data = body.get("data") if isinstance(body, dict) else None
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.warning("welcome identity user failed: %s", exc)
        return None


def fetch_helper_user_ids(token: str, user_id: str) -> list[str] | None:
    """调 identity helpers 原子读（本人 + helper_id=本人）；失败返回 None。"""
    if not token or not user_id:
        return None
    url = f"{identity_base()}/api/v1/identity/users/{user_id}/helpers"
    try:
        r = httpx.get(url, headers=_headers(token), timeout=10, trust_env=False)
        if r.status_code >= 400:
            logger.warning(
                "welcome identity helpers HTTP %s: %s",
                r.status_code,
                (r.text or "")[:200],
            )
            return None
        body = r.json()
        if not isinstance(body, dict):
            return None
        data = body.get("data")
        if not isinstance(data, dict):
            return None
        raw = data.get("user_ids") if data.get("user_ids") is not None else data.get("userIds")
        if not isinstance(raw, list):
            return None
        out: list[str] = []
        for item in raw:
            s = str(item or "").strip()
            if s and s not in out:
                out.append(s)
        return out
    except Exception as exc:
        logger.warning("welcome identity helpers failed: %s", exc)
        return None


def collect_role_menu_ids(token: str, role_ids: list[str]) -> set[str]:
    allowed: set[str] = set()
    if not token:
        return allowed
    for role_id in role_ids:
        rid = str(role_id or "").strip()
        if not rid or rid == "0":
            continue
        url = f"{identity_base()}/api/v1/identity/roles/{rid}"
        try:
            r = httpx.get(url, headers=_headers(token), timeout=10, trust_env=False)
            if r.status_code >= 400:
                continue
            body = r.json()
            data = body.get("data") if isinstance(body, dict) else None
            if not isinstance(data, dict):
                continue
            for mid in data.get("menu_ids") or data.get("menuIds") or []:
                s = str(mid or "").strip()
                if s and s != "0":
                    allowed.add(s)
        except Exception as exc:
            logger.warning("welcome role menus failed role=%s: %s", rid, exc)
    return allowed


def _get_asset_data(
    token: str,
    path: str,
    params: dict[str, Any] | None = None,
    *,
    label: str,
) -> dict[str, Any] | None:
    base = asset_base()
    if not base:
        logger.warning("welcome asset mid skipped (%s): asset URL not configured", label)
        return None
    if not token:
        logger.warning("welcome asset mid skipped (%s): no token", label)
        return None
    qs = urlencode({k: v for k, v in (params or {}).items() if v is not None and v != ""})
    url = f"{base}{path}"
    if qs:
        url = f"{url}?{qs}"
    try:
        r = httpx.get(url, headers=_headers(token), timeout=10, trust_env=False)
        if r.status_code >= 400:
            logger.warning(
                "welcome asset mid %s HTTP %s: %s",
                label,
                r.status_code,
                (r.text or "")[:200],
            )
            return None
        body = r.json()
        if not isinstance(body, dict):
            return None
        if int(body.get("code") or 0) != 0:
            logger.warning(
                "welcome asset mid %s code=%s msg=%s",
                label,
                body.get("code"),
                body.get("message"),
            )
            return None
        data = body.get("data")
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.warning("welcome asset mid %s failed: %s", label, exc)
        return None


def fetch_asset_accounts(token: str, user_id: str) -> list[dict[str, Any]] | None:
    """调 asset 中台 funds/userAccountDetail.ajax；失败返回 None（调用方 0.00+warning）。"""
    if not token or not user_id:
        return None
    url = f"{asset_base()}/api/funds/userAccountDetail.ajax"
    try:
        r = httpx.post(
            url,
            headers=_headers(token),
            json={"id": user_id, "userId": user_id},
            timeout=10,
            trust_env=False,
        )
        if r.status_code >= 400:
            return None
        body = r.json()
        if not isinstance(body, dict):
            return None
        obj = body.get("obj") if isinstance(body.get("obj"), dict) else None
        if obj and isinstance(obj.get("accounts"), list):
            return obj["accounts"]
        data = body.get("data") if isinstance(body.get("data"), dict) else None
        if data and isinstance(data.get("accounts"), list):
            return data["accounts"]
        return None
    except Exception as exc:
        logger.warning("welcome asset accounts failed: %s", exc)
        return None


def fetch_us_exchange_rate(token: str) -> str | None:
    """asset `/api/v1/asset/us-exchange-rate`；失败返回 None。"""
    data = _get_asset_data(
        token, "/api/v1/asset/us-exchange-rate", label="us-exchange-rate"
    )
    if data is None:
        return None
    raw = data.get("usExchangeRate")
    if raw is None:
        raw = data.get("us_exchange_rate")
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw).strip()


def fetch_company_user_ids(token: str, syuser_id: str) -> list[str] | None:
    """asset `/api/v1/asset/company-user-ids`；失败返回 None。"""
    if not syuser_id:
        return []
    data = _get_asset_data(
        token,
        "/api/v1/asset/company-user-ids",
        {"syuserId": syuser_id},
        label="company-user-ids",
    )
    if data is None:
        return None
    raw = data.get("userIds") if data.get("userIds") is not None else data.get("user_ids")
    if not isinstance(raw, list):
        return None
    out: list[str] = []
    for item in raw:
        s = str(item or "").strip()
        if s and s not in out:
            out.append(s)
    return out


def fetch_audit_count(
    token: str,
    *,
    order_type: str | int,
    manager_id: str,
    manager_field: str = "sale_manager",
    order_status: int | None = 20,
    pay_status: str | int | None = None,
) -> int | None:
    params: dict[str, Any] = {
        "orderType": str(order_type),
        "managerId": manager_id,
        "managerField": manager_field,
    }
    if pay_status is not None:
        params["payStatus"] = str(pay_status)
    elif order_status is not None:
        params["orderStatus"] = int(order_status)
    data = _get_order_data(token, "/api/v1/order/stats/audit-count", params, label="audit-count")
    if data is None:
        return None
    try:
        return int(data.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def fetch_timeout_count(
    token: str,
    *,
    user_id: str,
    order_status: int | None = None,
    is_timeout: int | None = None,
    scope: str = "staff",
) -> int | None:
    params: dict[str, Any] = {"userId": user_id, "scope": scope}
    if order_status is not None:
        params["orderStatus"] = int(order_status)
    if is_timeout is not None:
        params["isTimeout"] = int(is_timeout)
    data = _get_order_data(
        token, "/api/v1/order/stats/timeout-count", params, label="timeout-count"
    )
    if data is None:
        return None
    try:
        return int(data.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def fetch_trade_by_month(token: str, months: list[str]) -> list[dict[str, Any]] | None:
    if not months:
        return []
    data = _get_order_data(
        token,
        "/api/v1/order/stats/trade-by-month",
        {"months": ",".join(months), "orderTypes": "6,8", "minOrderStatus": 30},
        label="trade-by-month",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_test_count_by_month(
    token: str, *, user_id: str, year: int
) -> list[dict[str, Any]] | None:
    data = _get_order_data(
        token,
        "/api/v1/order/stats/test-count-by-month",
        {"userId": user_id, "year": year},
        label="test-count-by-month",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_finish_count_by_month(
    token: str, *, year: int, sale_user_id: str = ""
) -> list[dict[str, Any]] | None:
    params: dict[str, Any] = {"year": year}
    if sale_user_id:
        params["saleUserId"] = sale_user_id
    data = _get_order_data(
        token,
        "/api/v1/order/stats/finish-count-by-month",
        params,
        label="finish-count-by-month",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_finish_count_by_tester(
    token: str, *, year_month: str, sale_user_id: str = "", limit: int = 30
) -> list[dict[str, Any]] | None:
    params: dict[str, Any] = {"yearMonth": year_month, "limit": limit}
    if sale_user_id:
        params["saleUserId"] = sale_user_id
    data = _get_order_data(
        token,
        "/api/v1/order/stats/finish-count-by-tester",
        params,
        label="finish-count-by-tester",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_user_sale_by_month(
    token: str,
    *,
    user_ids: list[str],
    year: int,
    source: str = "exp",
    order_type_filter: str = "",
) -> list[dict[str, Any]] | None:
    if not user_ids:
        return []
    params: dict[str, Any] = {
        "userIds": ",".join(user_ids),
        "year": year,
        "source": source,
    }
    if order_type_filter:
        params["orderTypeFilter"] = order_type_filter
    data = _get_order_data(
        token,
        "/api/v1/order/stats/user-sale-by-month",
        params,
        label="user-sale-by-month",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_subcontract_sum_by_currency(
    token: str,
    *,
    user_ids: list[str],
    scope: str = "sale_user",
    year: int | None = None,
    exchange_rate: str | float | None = None,
) -> dict[str, Any] | None:
    """分包主/子单按币种 SUM；失败 None → service 空毛利+日志。"""
    if not user_ids:
        return {"parent": [], "child": [], "scope": scope}
    params: dict[str, Any] = {
        "userIds": ",".join(str(u) for u in user_ids if str(u).strip()),
        "scope": scope,
    }
    if year is not None:
        params["year"] = int(year)
    if exchange_rate is not None and str(exchange_rate).strip() != "":
        params["exchangeRate"] = str(exchange_rate).strip()
    return _get_order_data(
        token,
        "/api/v1/order/stats/subcontract-sum-by-currency",
        params,
        label="subcontract-sum-by-currency",
    )


def fetch_recent_sys_logs(
    token: str,
    *,
    limit: int = 10,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]] | None:
    """order `/api/v1/order/syslog/recent`；失败返回 None（调用方空列表+日志）。"""
    params: dict[str, Any] = {"limit": int(limit)}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    data = _get_order_data(
        token,
        "/api/v1/order/syslog/recent",
        params,
        label="syslog-recent",
    )
    if data is None:
        return None
    items = data.get("items")
    return items if isinstance(items, list) else []


def fetch_sys_logs_page(
    token: str,
    *,
    offset: int = 0,
    limit: int = 10,
    keyword: str = "",
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any] | None:
    """order `/api/v1/order/syslog/page`；失败返回 None（调用方空页+日志）。"""
    params: dict[str, Any] = {
        "offset": int(offset),
        "limit": int(limit),
    }
    if keyword:
        params["keyword"] = keyword
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    return _get_order_data(
        token,
        "/api/v1/order/syslog/page",
        params,
        label="syslog-page",
    )
