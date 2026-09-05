"""阶段 C：asset / gateway internal base URL。"""
from __future__ import annotations

from django.conf import settings

from shared.utoo_admin_routes import AdminMidTarget


def _pick(*keys: str, default: str = "") -> str:
    for key in keys:
        val = getattr(settings, key, None) or ""
        val = str(val).strip().rstrip("/")
        if val:
            return val
    return default.rstrip("/")


def asset_mid_configured() -> bool:
    return bool(_pick("UTOO_ASSET_MID_SERVICE_URL", "SVC_ADMIN_ASSET_URL"))


def base_url_for(target: AdminMidTarget) -> str:
    if target == AdminMidTarget.ASSET:
        # 未显式配置时返回空串 → proxy_mid_path 503（禁止默认回落网关 twin）
        return _pick("UTOO_ASSET_MID_SERVICE_URL", "SVC_ADMIN_ASSET_URL")
    if target == AdminMidTarget.BIZ_LOCAL:
        return ""
    return _pick("UTOO_GATEWAY_INTERNAL_URL", default="http://127.0.0.1:18083")


def service_label(target: AdminMidTarget) -> str:
    return {
        AdminMidTarget.ASSET: "Asset中台",
        AdminMidTarget.GATEWAY_INTERNAL: "愉兔网关(过渡)",
        AdminMidTarget.BIZ_LOCAL: "utoo_biz本地",
    }.get(target, "上游服务")
