"""订单详情进度 jdshow — 对齐 Java orderDetailAjax"""
from __future__ import annotations

from apps.core.db_utils import fetch_all, fetch_one


def _max_purchase_order(sale_order_id: int) -> tuple[int, int] | None:
    row = fetch_one(
        """
        SELECT id, order_status
        FROM experiment_order
        WHERE parent_id = %(sid)s AND order_status > 0
        ORDER BY order_status DESC
        LIMIT 1
        """,
        {"sid": sale_order_id},
    )
    if not row:
        return None
    return int(row["id"]), int(row.get("order_status") or 0)


def _all_purchase_line_children_complete(purchase_order_id: int) -> bool:
    rows = fetch_all(
        """
        SELECT eoc.order_status
        FROM exp_qd_purchase_order_child poc
        JOIN experiment_order_child eoc ON eoc.id = poc.order_child_id
        WHERE poc.purchase_order_id = %(pid)s
        """,
        {"pid": purchase_order_id},
    )
    if not rows:
        return False
    return all(int(r.get("order_status") or 0) == 50 for r in rows)


def compute_jdshow(sale_order_id: int, isfk: str) -> int:
    paid = str(isfk) == "1"
    jd = 1 if paid else 0
    po = _max_purchase_order(sale_order_id)
    if not po:
        return jd
    po_id, st = po
    if 36 <= st < 38:
        jd = 2 if paid else 1
    if 38 <= st < 50:
        jd = 3 if paid else 2
    if _all_purchase_line_children_complete(po_id):
        jd = 4 if paid else 3
    return jd
