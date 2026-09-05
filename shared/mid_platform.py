"""经营域调用身份中台 HTTP 接口（sales 等业务服务内聚合，前端只打经营 API）。"""

import httpx
from django.conf import settings
from rest_framework.exceptions import APIException


def _mid_base() -> str:
    return (getattr(settings, "IDENTITY_MID_SERVICE_URL", "") or "").strip().rstrip("/")


def fetch_sales_console_options(
    authorization: str,
    *,
    channel: str = "mall_qd",
    customer_keyword: str = "",
    timeout: float = 10.0,
) -> dict:
    """GET identity/mall/sales-console-options"""
    base = _mid_base()
    if not base:
        return {"companies": [], "customers": [], "users": [], "managers": []}
    headers = {"Authorization": authorization, "X-Channel": channel}
    params = {}
    if customer_keyword:
        params["customer_keyword"] = customer_keyword
    try:
        response = httpx.get(
            f"{base}/api/v1/identity/mall/sales-console-options",
            headers=headers,
            params=params,
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise APIException(detail="身份中台不可用，无法加载销售主数据") from exc
    if response.status_code >= 400:
        raise APIException(detail=f"身份中台返回 {response.status_code}，无法加载销售主数据")
    payload = response.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return {"companies": [], "customers": [], "users": [], "managers": []}
    return {
        "companies": data.get("companies") or [],
        "customers": data.get("customers") or [],
        "users": data.get("users") or [],
        "managers": data.get("managers") or [],
    }
