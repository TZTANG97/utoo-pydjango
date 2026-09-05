from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import fetch_all, scalar

IN_STATUS_LABELS = {1: "待入库", 2: "已入库", 3: "已废弃"}
OUT_STATUS_LABELS = {1: "待出库", 2: "已出库", 3: "已废弃"}

IN_FTYPE_LABELS = {
    1: "采购入库单",
    2: "租赁归还入库单",
    3: "其他入库单",
    7: "借调入库单",
    8: "维修入库单",
    14: "内部租赁入库单",
}

OUT_FTYPE_LABELS = {
    4: "租赁出库单",
    5: "其他出库单",
    6: "销售出库单",
    9: "维修出库单",
    10: "借调出库单",
    11: "无订单销售出库单",
    15: "内部租赁出库单",
}


def _list_where(
    *,
    in_out_type: int,
    out_num: str = "",
    order_id: str = "",
    yj_out_time: str = "",
    status: str = "",
    store_id: str = "",
    ftype: str = "",
) -> tuple[str, dict[str, Any]]:
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.in_out_type = %(in_out_type)s"
    params: dict[str, Any] = {"in_out_type": in_out_type}
    if out_num:
        where += " AND t.out_num LIKE %(out_num)s"
        params["out_num"] = f"%{out_num}%"
    if order_id:
        where += """
            AND (
                o.order_id LIKE %(order_id)s
                OR r.order_id LIKE %(order_id)s
                OR t2.out_num LIKE %(order_id)s
            )
        """
        params["order_id"] = f"%{order_id}%"
    if status:
        where += " AND t.status = %(status)s"
        params["status"] = status
    if store_id:
        where += " AND t.store_id = %(store_id)s"
        params["store_id"] = store_id
    if ftype:
        where += " AND t.ftype = %(ftype)s"
        params["ftype"] = ftype
    if yj_out_time:
        where += " AND DATE_FORMAT(t.yj_out_time, '%%Y-%%m-%%d') = %(yj_out_time)s"
        params["yj_out_time"] = yj_out_time[:10]
    return where, params


def list_treasury(
    *,
    in_out_type: int,
    out_num: str = "",
    order_id: str = "",
    yj_out_time: str = "",
    status: str = "",
    store_id: str = "",
    ftype: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java GoodsOutTreasuryMapper.listPages（goods_out_treasury）。"""
    where, params = _list_where(
        in_out_type=in_out_type,
        out_num=out_num,
        order_id=order_id,
        yj_out_time=yj_out_time,
        status=status,
        store_id=store_id,
        ftype=ftype,
    )
    from_sql = f"""
        FROM goods_out_treasury t
        LEFT JOIN orderform o ON t.order_id = o.id
        LEFT JOIN rent_orderform r ON t.order_id = r.id
        LEFT JOIN goods_out_treasury t2 ON t.order_id = t2.id
        LEFT JOIN sy_users u ON t.sale_user = u.id
        LEFT JOIN goods_storehouse h ON t.store_id = h.id
        LEFT JOIN qd_user_company q ON t.customer_id = q.id
        {where}
    """
    total = int(scalar(f"SELECT COUNT(*) {from_sql}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    ftype_labels = IN_FTYPE_LABELS if in_out_type == 1 else OUT_FTYPE_LABELS
    status_labels = IN_STATUS_LABELS if in_out_type == 1 else OUT_STATUS_LABELS
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.out_num AS outNum, t.out_num,
            t.yj_out_time AS yjOutTime, t.sj_out_time AS sjOutTime,
            t.status, t.ftype, t.store_id AS storeId,
            t.order_id AS orderId, t.mark,
            COALESCE(o.order_id, r.order_id, t2.out_num) AS orderNum,
            h.store_name AS storeName,
            u.user_name AS userName, u.true_name AS trueName,
            q.name AS customerName,
            CASE
                WHEN t.ftype = 1 AND o.order_status IS NOT NULL AND o.order_status < 30 THEN 1
                WHEN t.ftype = 2 AND r.order_status IS NOT NULL AND r.order_status < 30 THEN 1
                ELSE 0
            END AS ists
        {from_sql}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        st = int(row.get("status") or 0)
        ft = int(row.get("ftype") or 0)
        row["statusLabel"] = status_labels.get(st, str(st) if st else "-")
        row["ftypeLabel"] = ftype_labels.get(ft, str(ft) if ft else "-")
        row["ists"] = bool(int(row.get("ists") or 0))
        row["saleUserName"] = row.get("trueName") or row.get("userName") or ""
    return rows, total
