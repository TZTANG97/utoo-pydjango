"""实验主链前缀：gateway → utoo_biz → order 中台（薄透传，禁止 `_internal` twin）。"""
from __future__ import annotations

# 与 utoo_gateway config/urls.py _UTOO_BIZ_ORDER_PREFIXES、utoo_biz urls_legacy 保持一致
EXPERIMENT_ORDER_PREFIXES: tuple[str, ...] = (
    "adminExperiment",
    "experimentOrder",
    "experimentChildOrder",
    "experimentSubOrder",
    "expSubPurchaseOrder",
    "retestapplication",
    "ordersampleinfomation",
    "sampleAttributeManage",
    "experimentManage",
    "experimentProject",
    "experimentGoods",
)


def experiment_order_proxy_path(full_path: str) -> str | None:
    """命中实验主链则返回原 path（方案 B：固定打 order，禁止改写 `/api/_internal/...`）。"""
    path = full_path.split("?", 1)[0]
    for prefix in EXPERIMENT_ORDER_PREFIXES:
        root = f"/api/{prefix}"
        if path == root or path.startswith(f"{root}/"):
            return path
    return None
