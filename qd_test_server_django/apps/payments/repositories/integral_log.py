from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.db_utils import execute, fetch_all, scalar


def _type_filter_clause(log_type: str) -> str:
    if log_type == "1":
        return " AND t.integral > 0"
    if log_type == "2":
        return " AND t.integral < 0"
    return ""


def _union_base_sql(*, type_clause: str, time_clause: str) -> str:
    return f"""
        SELECT t.id, t.addTime, t.deleteStatus, t.integral, t.type,
               t.order_id AS orderId, t.user_id AS userId, t.company_id AS companyId,
               eo.order_id AS orderNum
        FROM integrallog t
        LEFT JOIN experiment_order eo ON t.order_id = eo.id
        WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s
        {type_clause}{time_clause}
        UNION ALL
        SELECT t.id, t.addTime, t.deleteStatus, t.integral, t.type,
               t.order_id AS orderId, NULL AS userId, t.company_id AS companyId,
               eo.order_id AS orderNum
        FROM company_integral_log t
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        LEFT JOIN experiment_order eo ON t.order_id = eo.id
        WHERE t.deleteStatus = 0 AND quc.contract_phone = %(mobile)s
        {type_clause}{time_clause}
    """


def count_union_logs(
    *,
    user_id: int,
    mobile: str,
    log_type: str = "",
    start_time=None,
) -> int:
    type_clause = _type_filter_clause((log_type or "").strip())
    time_clause = ""
    params: dict[str, Any] = {"user_id": user_id, "mobile": mobile}
    if start_time:
        time_clause = " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    base_sql = _union_base_sql(type_clause=type_clause, time_clause=time_clause)
    return int(scalar(f"SELECT COUNT(1) FROM ({base_sql}) tab", params, 0) or 0)


def list_union_logs(
    *,
    user_id: int,
    mobile: str,
    offset: int,
    limit: int,
    log_type: str = "",
    start_time=None,
) -> list[dict[str, Any]]:
    type_clause = _type_filter_clause((log_type or "").strip())
    time_clause = ""
    params: dict[str, Any] = {
        "user_id": user_id,
        "mobile": mobile,
        "offset": offset,
        "limit": limit,
    }
    if start_time:
        time_clause = " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    base_sql = _union_base_sql(type_clause=type_clause, time_clause=time_clause)
    return fetch_all(
        f"""
        SELECT * FROM ({base_sql}) tab
        ORDER BY tab.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )


def fetch_redeem_order_num(redeem_log_id: int) -> str | None:
    rows = fetch_all(
        "SELECT orderId FROM redeem_goods_log WHERE id = %(id)s LIMIT 1",
        {"id": redeem_log_id},
    )
    if rows:
        return rows[0].get("orderId")
    return None


def enrich_redeem_order_nums(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        if str(row.get("type")) == "2" and row.get("orderId") and not row.get("orderNum"):
            order_num = fetch_redeem_order_num(int(row["orderId"]))
            if order_num:
                row["orderNum"] = order_num


def insert_company_integral_deduction(
    *, order_id: int, points: Decimal, company_id: Any
) -> None:
    execute(
        """
        INSERT INTO company_integral_log
            (addTime, deleteStatus, integral, order_id, type, company_id)
        VALUES (NOW(), 0, %(pts)s, %(oid)s, '3', %(cid)s)
        """,
        {"pts": float(-points), "oid": order_id, "cid": company_id},
    )


def insert_user_integral_deduction(
    *, order_id: int, points: Decimal, user_id: Any
) -> None:
    execute(
        """
        INSERT INTO integrallog
            (addTime, deleteStatus, integral, order_id, type, user_id)
        VALUES (NOW(), 0, %(pts)s, %(oid)s, '3', %(uid)s)
        """,
        {"pts": float(-points), "oid": order_id, "uid": user_id},
    )


def deduct_integral_for_order(order: dict[str, Any], points: Decimal) -> None:
    if points <= 0:
        return
    oid = int(order["id"])
    if order.get("customer_name"):
        insert_company_integral_deduction(
            order_id=oid, points=points, company_id=order["customer_name"]
        )
    elif order.get("custom_user_id"):
        insert_user_integral_deduction(
            order_id=oid, points=points, user_id=order["custom_user_id"]
        )
