from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from apps.admin_digital.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

# 对齐 Java mainOrderStatus（绩效明细列表展示）
_ORDER_STATUS_LABEL = {
    0: "已取消",
    5: "订单未发起审核",
    10: "已驳回",
    15: "审核中",
    20: "待审核",
    25: "待确认",
    30: "已审核",
    40: "已确认",
    50: "已完成",
    55: "已评价",
    60: "已关闭",
    66: "待平台确认",
    67: "待客户确认",
    70: "已开票待收款",
}


def list_test_targets(*, test_user_id: str, year: str | None = None) -> list[dict[str, Any]]:
    where = "WHERE deleteStatus = 0 AND test_user_id = %(uid)s"
    params: dict[str, Any] = {"uid": test_user_id}
    if year:
        where += " AND year = %(year)s"
        params["year"] = year
    return fetch_all(
        f"""
        SELECT id, addTime, test_user_id AS testUserId, year, amount
        FROM statistic_testuser_performance
        {where}
        ORDER BY year ASC
        """,
        params,
    )


def get_test_target(*, test_user_id: str, year: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, addTime, test_user_id AS testUserId, year, amount
        FROM statistic_testuser_performance
        WHERE deleteStatus = 0 AND test_user_id = %(uid)s AND year = %(year)s
        LIMIT 1
        """,
        {"uid": test_user_id, "year": year},
    )


def save_test_target(*, target_id: int | None, test_user_id: str, year: str, amount) -> int:
    if target_id:
        execute(
            """
            UPDATE statistic_testuser_performance
            SET year = %(year)s, amount = %(amount)s, test_user_id = %(uid)s
            WHERE id = %(id)s
            """,
            {"id": target_id, "year": year, "amount": amount, "uid": test_user_id},
        )
        return int(target_id)
    return execute_insert(
        """
        INSERT INTO statistic_testuser_performance
            (addTime, deleteStatus, test_user_id, year, amount)
        VALUES (NOW(), 0, %(uid)s, %(year)s, %(amount)s)
        """,
        {"uid": test_user_id, "year": year, "amount": amount},
    )


def list_sale_targets(
    *,
    sale_user_id: str,
    year: str | None = None,
    month: str | None = None,
) -> list[dict[str, Any]]:
    where = "WHERE deleteStatus = 0 AND sale_user_id = %(uid)s"
    params: dict[str, Any] = {"uid": sale_user_id}
    if year:
        where += " AND year = %(year)s"
        params["year"] = year
    if month:
        where += " AND month = %(month)s"
        params["month"] = month
    return fetch_all(
        f"""
        SELECT id, addTime, sale_user_id AS saleUserId, year, month, amount
        FROM statistic_saleuser_performance
        {where}
        ORDER BY month ASC
        """,
        params,
    )


def get_sale_target(*, sale_user_id: str, month: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, addTime, sale_user_id AS saleUserId, year, month, amount
        FROM statistic_saleuser_performance
        WHERE deleteStatus = 0 AND sale_user_id = %(uid)s AND month = %(month)s
        LIMIT 1
        """,
        {"uid": sale_user_id, "month": month},
    )


def save_sale_target(*, target_id: int | None, sale_user_id: str, month: str, amount) -> int:
    year = str(month)[:4]
    if target_id:
        execute(
            """
            UPDATE statistic_saleuser_performance
            SET year = %(year)s, month = %(month)s, amount = %(amount)s, sale_user_id = %(uid)s
            WHERE id = %(id)s
            """,
            {
                "id": target_id,
                "year": year,
                "month": month,
                "amount": amount,
                "uid": sale_user_id,
            },
        )
        return int(target_id)
    return execute_insert(
        """
        INSERT INTO statistic_saleuser_performance
            (addTime, deleteStatus, sale_user_id, year, month, amount)
        VALUES (NOW(), 0, %(uid)s, %(year)s, %(month)s, %(amount)s)
        """,
        {"uid": sale_user_id, "year": year, "month": month, "amount": amount},
    )


def monthly_finish_amount(*, test_user_id: str, year: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT DATE_FORMAT(t.end_time, '%%m') AS mon,
               SUM(IFNULL(c.reference_price, 0)) AS je
        FROM statistic_experiment_finish t
        LEFT JOIN experiment_order_child c ON t.child_id = c.id
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND t.test_user_id = %(uid)s
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
        GROUP BY DATE_FORMAT(t.end_time, '%%Y-%%m')
        """,
        {"uid": test_user_id, "year": year},
    )


def sale_month_actual(*, user_id: str, month: str, type_: int) -> Decimal:
    row = fetch_one(
        """
        SELECT IFNULL(SUM(tab.sale_amount), 0) AS totalAmount FROM (
            SELECT t.sale_amount
            FROM statistic_experiment_saleuser_utoo t
            WHERE t.account_type = 1
              AND t.month = %(month)s
              AND t.user_id = %(uid)s
              AND t.type = %(type)s
            UNION ALL
            SELECT ROUND(
                t.sale_amount * (SELECT a.us_exchange_rate FROM account_setting a LIMIT 1),
                2
            ) AS sale_amount
            FROM statistic_experiment_saleuser_utoo t
            WHERE t.account_type = 2
              AND t.month = %(month)s
              AND t.user_id = %(uid)s
              AND t.type = %(type)s
        ) tab
        """,
        {"uid": user_id, "month": month, "type": type_},
    )
    if not row:
        return Decimal("0")
    return Decimal(str(row.get("totalAmount") or 0))


def _pct(actual: Decimal, target: Decimal) -> Decimal:
    if target > 0:
        return (actual * Decimal("100") / target).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if actual > 0:
        return Decimal("100")
    return Decimal("0")


def build_lab_test_rows(*, users: list[dict[str, Any]], year: str) -> list[dict[str, Any]]:
    months = [f"{i:02d}" for i in range(1, 13)]
    result: list[dict[str, Any]] = []
    for user in users:
        uid = str(user.get("id"))
        target_row = get_test_target(test_user_id=uid, year=year)
        target = Decimal(str((target_row or {}).get("amount") or 0))
        monthly = {str(r.get("mon")): Decimal(str(r.get("je") or 0)) for r in monthly_finish_amount(test_user_id=uid, year=year)}
        month_values = []
        actual = Decimal("0")
        for m in months:
            val = monthly.get(m, Decimal("0"))
            month_values.append(float(val))
            actual += val
        dcl = _pct(actual, target)
        result.append(
            {
                "userId": uid,
                "trueName": user.get("trueName") or user.get("userName"),
                "grccmb": float(target),
                "monthvalues": month_values,
                "sjcc": float(actual),
                "dcl": float(dcl),
            }
        )
    result.sort(key=lambda x: Decimal(str(x["dcl"])), reverse=True)
    rank = 0
    prev = None
    for i, row in enumerate(result):
        cur = Decimal(str(row["dcl"]))
        if i == 0 or cur < prev:
            rank += 1
        row["pm"] = rank
        prev = cur
    return result


def _norm_month_key(value: Any) -> str:
    text = str(value or "").strip()
    parts = text.split("-")
    if len(parts) == 2 and parts[1].isdigit():
        return f"{parts[0]}-{int(parts[1]):02d}"
    return text


def build_lab_sale_rows(*, user_id: str, year: str) -> dict[str, Any]:
    months = [f"{i:02d}" for i in range(1, 13)]
    targets = {
        _norm_month_key(r.get("month")): Decimal(str(r.get("amount") or 0))
        for r in list_sale_targets(sale_user_id=user_id, year=year)
    }
    order_list: list[dict[str, Any]] = []
    invoice_list: list[dict[str, Any]] = []
    receipt_list: list[dict[str, Any]] = []
    for m in months:
        key = f"{year}-{m}"
        target = targets.get(key, Decimal("0"))
        order_actual = sale_month_actual(user_id=user_id, month=key, type_=1)
        invoice_actual = sale_month_actual(user_id=user_id, month=key, type_=2)
        receipt_actual = sale_month_actual(user_id=user_id, month=key, type_=3)
        order_list.append(
            {
                "month": m,
                "mbyj": float(target),
                "sjyj": float(order_actual),
                "dcl": float(_pct(order_actual, target)),
            }
        )
        invoice_list.append(
            {
                "month": m,
                "mbyj": 0,
                "sjyj": float(invoice_actual),
                "dcl": float(_pct(invoice_actual, Decimal("0"))),
            }
        )
        receipt_list.append(
            {
                "month": m,
                "mbyj": 0,
                "sjyj": float(receipt_actual),
                "dcl": float(_pct(receipt_actual, Decimal("0"))),
            }
        )
    return {
        "year": year,
        "resultList": order_list,
        "resultListkp": invoice_list,
        "resultListsk": receipt_list,
    }


def list_lab_sale_perf_orders(
    *,
    sale_user_id: str,
    month: str,
    type_: int,
    customer_name: str = "",
    order_id: str = "",
    goods_name: str = "",
    supplier_name: str = "",
    sale_manager: str = "",
    order_status: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java ExperimentOrderMapper#explistPages_labPerSaleUser。

    表别名用 eo（勿用 of：MySQL 8 保留字，会导致 SQL 失败）。
    """
    where = [
        "(eo.order_type = 6 OR eo.order_type = 8)",
        "eo.sale_user = %(sale_user_id)s",
        "DATE_FORMAT(eo.order_time, '%%Y-%%m') = %(month)s",
    ]
    params: dict[str, Any] = {
        "sale_user_id": sale_user_id,
        "month": month,
    }
    joins = ["LEFT JOIN qd_user_company quc ON eo.customer_name = quc.id"]
    if int(type_) == 1:
        where.append("eo.order_status >= 30")
    elif int(type_) == 2:
        joins.append(
            """
            LEFT JOIN (
                SELECT qb.exp_of_id, SUM(qb.money) kpje
                FROM qd_bill qb WHERE qb.type = 1
                GROUP BY qb.exp_of_id
            ) qdtab1 ON eo.id = qdtab1.exp_of_id
            """
        )
        where.append("eo.order_status != 0")
        where.append("IFNULL(qdtab1.kpje, 0) > 0")
    elif int(type_) == 3:
        joins.append(
            """
            LEFT JOIN (
                SELECT qb.exp_of_id, SUM(qb.money) kpje
                FROM qd_bill qb WHERE qb.type = 2
                GROUP BY qb.exp_of_id
            ) qdtab1 ON eo.id = qdtab1.exp_of_id
            """
        )
        where.append("eo.order_status != 0")
        where.append("IFNULL(qdtab1.kpje, 0) > 0")
    if customer_name:
        where.append("quc.name LIKE %(customer_name)s")
        params["customer_name"] = f"%{customer_name.strip('%')}%"
    if order_id:
        where.append("eo.order_id LIKE %(order_id)s")
        params["order_id"] = f"%{order_id}%"
    if goods_name:
        joins.append("JOIN experiment_order_child ocf ON eo.id = ocf.order_form_id")
        where.append(
            "(ocf.goods_name LIKE %(goods_name)s OR ocf.goods_spec LIKE %(goods_name)s)"
        )
        params["goods_name"] = f"%{goods_name}%"
    if supplier_name:
        where.append("eo.supplier_name = %(supplier_name)s")
        params["supplier_name"] = supplier_name
    if sale_manager:
        where.append("eo.sale_manager = %(sale_manager)s")
        params["sale_manager"] = sale_manager
    if order_status != "":
        where.append("eo.order_status = %(order_status)s")
        params["order_status"] = order_status

    where_sql = " AND ".join(where)
    join_sql = "\n".join(joins)
    total = int(
        scalar(
            f"""
            SELECT COUNT(DISTINCT eo.id)
            FROM experiment_order eo
            {join_sql}
            WHERE {where_sql}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.addTime,
            t.order_id AS orderId,
            t.order_status AS orderStatus,
            t.totalPrice,
            t.invoiceType,
            t.order_time AS orderTime,
            2 AS isOut,
            q.name AS customerName,
            u.company_name AS supplierName,
            sm.user_name AS managerName,
            sm.true_name AS managerTrueName,
            su.user_name AS saleUserName,
            su.true_name AS saleUserTrueName
        FROM experiment_order t
        INNER JOIN (
            SELECT DISTINCT eo.id
            FROM experiment_order eo
            {join_sql}
            WHERE {where_sql}
        ) ids ON t.id = ids.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN `user` u ON t.supplier_name = u.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        try:
            st = int(r.get("orderStatus")) if r.get("orderStatus") is not None else None
        except (TypeError, ValueError):
            st = None
        r["orderStatusLabel"] = _ORDER_STATUS_LABEL.get(
            st, str(r.get("orderStatus") if r.get("orderStatus") is not None else "-")
        )
        inv = r.get("invoiceType")
        r["invoiceLabel"] = "是" if inv in (1, "1") else "否"
        for key in ("addTime", "orderTime"):
            val = r.get(key)
            if val is not None and hasattr(val, "strftime"):
                r[key] = val.strftime("%Y-%m-%d %H:%M:%S") if key == "addTime" else val.strftime("%Y-%m-%d")
            elif val is not None:
                r[key] = str(val)[:19]
    return rows, total
