"""员工端创建实验子订单页 — createOrderPage / createOrderPagexcx。"""
from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one
from qd_common.serialize import to_jsonable


def _pending_childs(sale_order_pk: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            c.id,
            c.order_id AS orderId,
            c.goods_name AS goodsName,
            c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrandName,
            c.goods_nums AS goodsNums,
            c.experiment_project_name AS experiment_project_name,
            c.experiment_class_name AS experiment_class_name,
            c.experiment_class_id AS experiment_class_id,
            c.test_user_id AS test_user_id,
            c.line_id AS line_id,
            u.user_name AS test_user,
            u.true_name AS test_user_true,
            el.line_num AS line
        FROM experiment_order_child c
        LEFT JOIN sy_users u ON c.test_user_id = u.id
        LEFT JOIN experiment_line el ON c.line_id = el.id
        WHERE c.order_form_id = %(oid)s
          AND IFNULL(c.delete_status, 2) <> 1
          AND IFNULL(c.op_status, 0) = 1
        ORDER BY c.id ASC
        """,
        {"oid": sale_order_pk},
    )
    out: list[dict[str, Any]] = []
    for r in rows or []:
        item = dict(r)
        item["test_user"] = item.get("test_user_true") or item.get("test_user") or ""
        item.pop("test_user_true", None)
        out.append(to_jsonable(item))
    return out


def create_order_page(*, sale_order_id: int) -> dict[str, Any]:
    """对齐 Java createOrderPage.ajax：obj.saleOrder 为订单号字符串。"""
    if sale_order_id <= 0:
        return {"saleOrder": ""}
    row = fetch_one(
        """
        SELECT id, order_id
        FROM experiment_order
        WHERE id = %(oid)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"oid": sale_order_id},
    )
    if not row:
        return {"saleOrder": ""}
    return {"saleOrder": row.get("order_id") or ""}


def create_order_page_xcx(*, sale_order_id: int) -> dict[str, Any]:
    """对齐 Java createOrderPagexcx.ajax：可选产品行 childs（op_status=1）。"""
    page = create_order_page(sale_order_id=sale_order_id)
    childs = _pending_childs(sale_order_id) if sale_order_id > 0 else []
    return {**page, "childs": childs}
