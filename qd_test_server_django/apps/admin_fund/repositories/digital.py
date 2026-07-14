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
