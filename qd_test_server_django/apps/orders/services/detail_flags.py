"""订单详情页按钮显隐 — viewReciveBtn / viewKpBtn"""
from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_one


def has_pending_payment_application(order_id: int) -> bool:
    return bool(
        fetch_one(
            """
            SELECT 1 AS ok FROM payment_application
            WHERE deleteStatus = 0
              AND orderType IN (2, 3)
              AND applyStatus = 1
              AND orderId = %(oid)s
            LIMIT 1
            """,
            {"oid": str(order_id)},
        )
    )


def has_invoice_apply_for_order(order_id: int) -> bool:
    # 表字段为 order_ids（逗号分隔 pk），不是 order_id
    return bool(
        fetch_one(
            """
            SELECT 1 AS ok FROM invoice_apply_log
            WHERE deleteStatus = 0
              AND FIND_IN_SET(%(oid)s, REPLACE(IFNULL(order_ids, ''), ' ', '')) > 0
            LIMIT 1
            """,
            {"oid": str(order_id)},
        )
    )


def compute_view_receive_btn(
    *,
    order_id: int,
    of: dict[str, Any],
    receive_bills: list[dict[str, Any]],
) -> bool:
    if has_pending_payment_application(order_id):
        return False
    ct = (of.get("collection_time") or "").strip()
    if not ct:
        return True
    parts = [p for p in ct.split(",") if p.strip()]
    if parts and len(receive_bills) >= len(parts):
        return False
    return True


def compute_view_kp_btn(
    *,
    order_id: int,
    of: dict[str, Any],
    open_bills: list[dict[str, Any]],
) -> bool:
    inv = int(of.get("invoiceType") or 0)
    if inv == 2:
        return False
    if has_invoice_apply_for_order(order_id):
        return False
    total = float(of.get("totalPrice") or of.get("total_price") or 0)
    kaip_sum = sum(float(b.get("money") or 0) for b in open_bills)
    if kaip_sum >= total and total > 0:
        return False
    ct = (of.get("collection_time") or "").strip()
    if ct:
        parts = [p for p in ct.split(",") if p.strip()]
        if parts and len(open_bills) >= len(parts):
            return False
    return True
