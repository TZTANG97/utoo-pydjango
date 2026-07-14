from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


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
