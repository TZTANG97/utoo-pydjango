from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar


def overview(year: str) -> dict[str, Any]:
    """Simplified digital manage center KPIs (full Java board is much larger)."""
    company_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM company_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    user_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM user_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    loan_pay = fetch_one(
        """
        SELECT COALESCE(SUM(loan), 0) AS amount
        FROM company_loan_pay
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    project_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM project_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    balances = fetch_all(
        """
        SELECT
            account_type AS accountType,
            COALESCE(SUM(available_balance), 0) AS availableBalance,
            COALESCE(SUM(freezing_balance), 0) AS freezingBalance
        FROM account
        GROUP BY account_type
        """
    )
    log_count = int(
        scalar(
            """
            SELECT COUNT(*) FROM account_log
            WHERE deleteStatus = 0 AND YEAR(addTime) = %(year)s
            """,
            {"year": year},
        )
        or 0
    )
    monthly = fetch_all(
        """
        SELECT month, COALESCE(SUM(pay_amount), 0) AS amount
        FROM company_pay_detail
        WHERE year = %(year)s
        GROUP BY month
        ORDER BY month
        """,
        {"year": year},
    )
    return {
        "year": year,
        "companyPayTotal": float(company_pay.get("amount") or 0),
        "userPayTotal": float(user_pay.get("amount") or 0),
        "loanPayTotal": float(loan_pay.get("amount") or 0),
        "projectPayTotal": float(project_pay.get("amount") or 0),
        "balances": balances,
        "logCount": log_count,
        "monthlyCompanyPay": monthly,
    }


def _year_clause(year: str, alias: str = "eo") -> tuple[str, dict[str, Any]]:
    y = str(year or "").strip()
    if not y or y in ("全部", "选择年份", "all", "ALL"):
        return "", {}
    return f" AND LEFT({alias}.addTime, 4) = %(stat_year)s", {"stat_year": y[:4]}


def sel_company_sale_by_year(year: str = "", type_code: str = "1") -> dict[str, Any]:
    """公司实验金额列表（对齐 Java/MP selCompanySaleByYear）。

    - year 空/全部：不限年
    - type: 1=全部（当前仅年份维度；预留实验分类）
    - 口径：order_type=6 实验主单、RMB(currency_type=1)、status>=30，按所属公司汇总
    """
    del type_code  # 预留：type=2 按实验分类过滤
    year_sql, params = _year_clause(year)
    rows = fetch_all(
        f"""
        SELECT
            u.id AS id,
            IFNULL(NULLIF(TRIM(u.company_name), ''), CONCAT('公司#', u.id)) AS company_name,
            IFNULL(SUM(eo.totalPrice), 0) AS syrmb
        FROM experiment_order eo
        INNER JOIN `user` u ON eo.supplier_name = u.id
        WHERE eo.order_type = 6
          AND eo.order_status >= 30
          AND eo.currency_type = 1
          {year_sql}
        GROUP BY u.id, u.company_name
        HAVING IFNULL(SUM(eo.totalPrice), 0) > 0
        ORDER BY syrmb DESC
        """,
        params,
    )
    company_info: list[dict[str, Any]] = []
    total = 0.0
    for r in rows:
        amt = float(r.get("syrmb") or 0)
        total += amt
        company_info.append(
            {
                "id": r.get("id"),
                "company_name": str(r.get("company_name") or ""),
                "syrmb": round(amt, 2),
            }
        )
    company_info.append(
        {
            "id": 0,
            "company_name": f"总额 {round(total, 2)}元",
            "syrmb": round(total, 2),
            "isTotal": True,
        }
    )
    return {"companyInfo": company_info, "total": round(total, 2)}


def sel_exp_sale_by_year(
    year: str = "",
    test_type: str = "",
    order_type: int | str = 6,
) -> dict[str, Any]:
    """实验/分包订单金额按月柱图（对齐 Java/MP selExpSaleByYear）。

    test_type 预留（实验分类），本阶段仅按年份 + order_type 聚合。
    """
    del test_type
    try:
        ot = int(order_type)
    except (TypeError, ValueError):
        ot = 6
    if ot not in (6, 8):
        ot = 6

    year_sql, params = _year_clause(year)
    params["order_type"] = ot

    rows = fetch_all(
        f"""
        SELECT
            MONTH(eo.addTime) AS m,
            IFNULL(SUM(eo.totalPrice), 0) AS amount
        FROM experiment_order eo
        WHERE eo.order_type = %(order_type)s
          AND eo.order_status >= 30
          AND eo.currency_type = 1
          {year_sql}
        GROUP BY MONTH(eo.addTime)
        ORDER BY m
        """,
        params,
    )

    by_month = {int(r.get("m") or 0): float(r.get("amount") or 0) for r in rows if r.get("m")}
    expmonth = [f"{i}月" for i in range(1, 13)]
    exp_sale = [round(by_month.get(i, 0.0), 2) for i in range(1, 13)]
    total = round(sum(exp_sale), 2)
    return {
        "expmonth": expmonth,
        "expSaleAryrmb": exp_sale,
        "expqnxsrmb": total,
    }
