"""管理端 welcome / billing / 资金·数字化 → 中台或 biz 本地。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# 与 utoo_gateway config/urls.py _ADMIN_ASSET_PREFIXES 保持一致
ASSET_PREFIXES: tuple[str, ...] = (
    "digital",
    "testUserStats",
    "testUserPerformance",
    "saleUserPerformance",
    "labPerformanceSaleuser",
    "labPerformance",
    "storeHouse",
    "samplestoreHouse",
    "sampleremainstoreHouse",
    "inventory",
    "lab",
    "inTreasury",
    "expLog",
    "inIncome",
    "funds",
    "companyPay",
    "userPay",
    "companyLoanPay",
    "projectPay",
    "digitalManage",
    "getLog.ajax",
    "getAccountLog.ajax",
    "selExpSumByYear.ajax",
    "selExpSumByYearxcx.ajax",
    "yesterdayIncome.ajax",
    "yesterdayIncomexcx.ajax",
    "account_User.ajax",
    "pass.ajax",
    "supplier/queryAllPay.ajax",
)

# 阶段 C：仅 welcome 经 utoo_biz 本地编排。
# 开票/付款/复测改回网关 BFF 直挂（去掉 biz→_internal 假转发）；后续再迁中台/biz。
VUE_BIZ_EXACT: frozenset[str] = frozenset(
    {
        "welcome.ajax",
    }
)


class AdminMidTarget(str, Enum):
    ASSET = "asset"
    GATEWAY_INTERNAL = "gateway_internal"
    BIZ_LOCAL = "biz_local"


@dataclass(frozen=True)
class AdminRouteDecision:
    target: AdminMidTarget
    channel: str
    path: str


def _matches_asset(path: str) -> bool:
    for prefix in ASSET_PREFIXES:
        if prefix.endswith(".ajax") or "/" in prefix:
            if path == f"/api/{prefix}":
                return True
        elif path.startswith(f"/api/{prefix}/"):
            return True
    return False


def resolve_admin_path(full_path: str, *, asset_mid_configured: bool = True) -> AdminRouteDecision:
    path = full_path.split("?", 1)[0]

    if path.startswith("/api/vue/"):
        sub = path[len("/api/vue/") :]
        if sub in VUE_BIZ_EXACT:
            # welcome 等：utoo_biz urls_legacy 本地编排，禁止改写 _internal
            return AdminRouteDecision(AdminMidTarget.BIZ_LOCAL, "admin", path)

    if _matches_asset(path):
        # 方案 B：缺 asset 中台 → 由上游代理返回 503，禁止 silent twin `_internal`
        # asset_mid_configured 仍传入，供调用方/单测感知；路由目标固定 ASSET
        _ = asset_mid_configured
        return AdminRouteDecision(AdminMidTarget.ASSET, "admin", path)

    return AdminRouteDecision(
        AdminMidTarget.GATEWAY_INTERNAL,
        "admin",
        path.replace("/api/", "/api/_internal/", 1) if path.startswith("/api/") else path,
    )
