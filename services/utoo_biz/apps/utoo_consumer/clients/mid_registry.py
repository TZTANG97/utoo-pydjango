"""各中台 base URL（从 settings 读取）。"""
from __future__ import annotations

from django.conf import settings

from shared.utoo_consumer_routes import MidTarget


def _pick(*keys: str, default: str = "") -> str:
    for key in keys:
        val = getattr(settings, key, None) or ""
        val = str(val).strip().rstrip("/")
        if val:
            return val
    return default.rstrip("/")


def order_mid_configured() -> bool:
    return bool(_pick("UTOO_ORDER_MID_SERVICE_URL", "UTOO_ORDER_SERVICE_URL", "SVC_ORDER_URL"))


def base_url_for(target: MidTarget) -> str:
    if target == MidTarget.ORDER:
        # 未显式配置时返回空串 → proxy_mid_path 503（禁止默认 localhost / 回落网关 twin）
        return _pick("UTOO_ORDER_MID_SERVICE_URL", "UTOO_ORDER_SERVICE_URL", "SVC_ORDER_URL")
    if target == MidTarget.PAYMENT:
        return _pick("UTOO_PAYMENT_MID_SERVICE_URL", "SVC_PAYMENT_URL")
    if target == MidTarget.PLATFORM:
        return _pick("UTOO_PLATFORM_MID_SERVICE_URL", "SVC_ADMIN_PLATFORM_URL")
    if target == MidTarget.IDENTITY:
        return _pick(
            "UTOO_IDENTITY_MID_SERVICE_URL",
            "IDENTITY_MID_SERVICE_URL",
            "SVC_IDENTITY_URL",
        )
    return _pick("UTOO_GATEWAY_INTERNAL_URL", default="http://127.0.0.1:18083")


def service_label(target: MidTarget) -> str:
    return {
        MidTarget.ORDER: "订单中台",
        MidTarget.PAYMENT: "支付中台",
        MidTarget.PLATFORM: "Platform中台",
        MidTarget.IDENTITY: "身份中台",
        MidTarget.GATEWAY_INTERNAL: "愉兔网关(过渡)",
        MidTarget.BIZ_LOCAL: "utoo_biz本地",
    }.get(target, "上游服务")
