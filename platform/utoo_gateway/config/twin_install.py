"""P3：twin 包是否进入 INSTALLED_APPS（条件卸载，不 git rm）。

biz 开启（生产常态）：不装纯应急 twin；GW-LOCAL 强依赖包除外。
未开 biz：全部装上，供 `_internal` / 公开 twin 应急。
"""

from __future__ import annotations

# 公开 GW-LOCAL 仍 import 视图：seller/swf_upload、lab expOrderList、celery 刷表
TWIN_GW_LOCAL_APPS: tuple[str, ...] = (
    "apps.pc_compat",
    "apps.admin_digital",
)

# 仅未开 biz 的 `_internal` / 公开 twin 应急；biz 开时不进 INSTALLED_APPS
TWIN_EMERGENCY_ONLY_APPS: tuple[str, ...] = (
    "apps.admin_inventory",
    "apps.admin_fund",
)

# 文档 / 扫描用：历史上的 twin 候选全集（含 GW-LOCAL 保留）
TWIN_ALL_CANDIDATE_APPS: tuple[str, ...] = TWIN_GW_LOCAL_APPS + TWIN_EMERGENCY_ONLY_APPS


def twin_apps_for_installed(*, biz_enabled: bool) -> tuple[str, ...]:
    """返回应写入 INSTALLED_APPS 的 twin 包。"""
    if biz_enabled:
        return TWIN_GW_LOCAL_APPS
    return TWIN_ALL_CANDIDATE_APPS
