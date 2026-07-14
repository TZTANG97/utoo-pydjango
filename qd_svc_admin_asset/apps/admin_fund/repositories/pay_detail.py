from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one


def _dec(v: Any) -> Decimal:
    if v in (None, ""):
        return Decimal("0")
    return Decimal(str(v))


def _fill_months(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    by_month = {str(int(r.get("month") or 0)): r for r in rows if r.get("month")}
    result = []
    for i in range(1, 13):
        key = str(i)
        src = by_month.get(key) or by_month.get(f"{i:02d}") or {}
        item: dict[str, Any] = {
            "id": src.get("id") or 0,
            "month": key,
            "status": src.get("status") if src else 2,
        }
        for f in fields:
            camel = "".join(p.capitalize() if idx else p for idx, p in enumerate(f.split("_")))
            # keep both snake aliases via camel from SQL aliases
            val = src.get(camel) if camel in src else src.get(f)
            item[camel] = float(_dec(val))
        result.append(item)
    return result


def list_companies() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT u.id, u.company_name AS companyName, u.syuser_id AS syuserId
        FROM user u
        WHERE u.deleteStatus = 0 AND u.userType = 6
        ORDER BY u.company_name ASC
        """
    )


def list_pay_users() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, user_name AS userName, true_name AS trueName
        FROM sy_users
        WHERE user_status = 1 AND account_type = 0
        ORDER BY user_name ASC
        LIMIT 500
        """
    )


def list_labs() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, lab_num AS labNum, lab_name AS labName
        FROM experiment_lab
        WHERE deleteStatus = 0 AND status = 1
        ORDER BY lab_name ASC
        """
    )


# ---- company pay ----
def list_company_pay(company_id: str, year: str, account_type: int) -> list[dict[str, Any]]:
    if company_id in ("", "-1"):
        rows = fetch_all(
            """
            SELECT
                month,
                SUM(wages) AS wages, SUM(taxes) AS taxes, SUM(fees) AS fees,
                SUM(system_cost) AS systemCost, SUM(loan) AS loan,
                SUM(pay_amount) AS payAmount, 0 AS id, MAX(status) AS status
            FROM company_pay_detail
            WHERE year = %(year)s AND account_type = %(account_type)s
            GROUP BY month
            ORDER BY month
            """,
            {"year": year, "account_type": account_type},
        )
    else:
        rows = fetch_all(
            """
            SELECT
                id, month, wages, taxes, fees,
                system_cost AS systemCost, loan,
                pay_amount AS payAmount, status
            FROM company_pay_detail
            WHERE company_id = %(company_id)s
              AND year = %(year)s
              AND account_type = %(account_type)s
            ORDER BY month
            """,
            {"company_id": company_id, "year": year, "account_type": account_type},
        )
    return _fill_months(rows, ["wages", "taxes", "fees", "system_cost", "loan", "pay_amount"])


def upsert_company_pay(items: list[dict[str, Any]]) -> None:
    for item in items:
        company_id = item.get("companyId") or item.get("company_id")
        year = item.get("year")
        month = str(item.get("month") or "")
        account_type = int(item.get("accountType") or item.get("account_type") or 1)
        wages = _dec(item.get("wages"))
        taxes = _dec(item.get("taxes"))
        fees = _dec(item.get("fees"))
        system_cost = _dec(item.get("systemCost") or item.get("system_cost"))
        loan = _dec(item.get("loan"))
        pay_amount = wages + taxes + fees + system_cost + loan
        row_id = int(item.get("id") or 0)
        if row_id:
            execute(
                """
                UPDATE company_pay_detail
                SET wages=%(wages)s, taxes=%(taxes)s, fees=%(fees)s,
                    system_cost=%(system_cost)s, loan=%(loan)s, pay_amount=%(pay_amount)s
                WHERE id=%(id)s
                """,
                {
                    "wages": wages,
                    "taxes": taxes,
                    "fees": fees,
                    "system_cost": system_cost,
                    "loan": loan,
                    "pay_amount": pay_amount,
                    "id": row_id,
                },
            )
        else:
            existing = fetch_one(
                """
                SELECT id FROM company_pay_detail
                WHERE company_id=%(company_id)s AND year=%(year)s
                  AND month=%(month)s AND account_type=%(account_type)s
                LIMIT 1
                """,
                {
                    "company_id": company_id,
                    "year": year,
                    "month": month,
                    "account_type": account_type,
                },
            )
            if existing:
                execute(
                    """
                    UPDATE company_pay_detail
                    SET wages=%(wages)s, taxes=%(taxes)s, fees=%(fees)s,
                        system_cost=%(system_cost)s, loan=%(loan)s, pay_amount=%(pay_amount)s
                    WHERE id=%(id)s
                    """,
                    {
                        "wages": wages,
                        "taxes": taxes,
                        "fees": fees,
                        "system_cost": system_cost,
                        "loan": loan,
                        "pay_amount": pay_amount,
                        "id": existing["id"],
                    },
                )
            else:
                execute_insert(
                    """
                    INSERT INTO company_pay_detail
                        (addTime, deleteStatus, company_id, year, month, taxes, fees, wages,
                         pay_amount, system_cost, status, loan, account_type)
                    VALUES
                        (NOW(), 0, %(company_id)s, %(year)s, %(month)s, %(taxes)s, %(fees)s, %(wages)s,
                         %(pay_amount)s, %(system_cost)s, 2, %(loan)s, %(account_type)s)
                    """,
                    {
                        "company_id": company_id,
                        "year": year,
                        "month": month,
                        "taxes": taxes,
                        "fees": fees,
                        "wages": wages,
                        "pay_amount": pay_amount,
                        "system_cost": system_cost,
                        "loan": loan,
                        "account_type": account_type,
                    },
                )


# ---- personal pay ----
def list_user_pay(user_id: str, year: str, account_type: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            id, month, wages, taxes,
            loan_interest AS loanInterest, car_amount AS carAmount,
            order_amount AS orderAmount, other_amount AS otherAmount,
            pay_amount AS payAmount, status
        FROM user_pay_detail
        WHERE user_id = %(user_id)s AND year = %(year)s AND account_type = %(account_type)s
        ORDER BY month
        """,
        {"user_id": user_id, "year": year, "account_type": account_type},
    )
    return _fill_months(
        rows,
        ["wages", "taxes", "loan_interest", "car_amount", "order_amount", "other_amount", "pay_amount"],
    )


def upsert_user_pay(items: list[dict[str, Any]]) -> None:
    for item in items:
        user_id = item.get("userId") or item.get("user_id")
        year = item.get("year")
        month = str(item.get("month") or "")
        account_type = int(item.get("accountType") or item.get("account_type") or 1)
        wages = _dec(item.get("wages"))
        taxes = _dec(item.get("taxes"))
        loan_interest = _dec(item.get("loanInterest") or item.get("loan_interest"))
        car_amount = _dec(item.get("carAmount") or item.get("car_amount"))
        order_amount = _dec(item.get("orderAmount") or item.get("order_amount"))
        other_amount = _dec(item.get("otherAmount") or item.get("other_amount"))
        pay_amount = wages + taxes + loan_interest + car_amount + order_amount + other_amount
        row_id = int(item.get("id") or 0)
        data = {
            "wages": wages,
            "taxes": taxes,
            "loan_interest": loan_interest,
            "car_amount": car_amount,
            "order_amount": order_amount,
            "other_amount": other_amount,
            "pay_amount": pay_amount,
        }
        if row_id:
            execute(
                """
                UPDATE user_pay_detail
                SET wages=%(wages)s, taxes=%(taxes)s, loan_interest=%(loan_interest)s,
                    car_amount=%(car_amount)s, order_amount=%(order_amount)s,
                    other_amount=%(other_amount)s, pay_amount=%(pay_amount)s
                WHERE id=%(id)s
                """,
                {**data, "id": row_id},
            )
        else:
            existing = fetch_one(
                """
                SELECT id FROM user_pay_detail
                WHERE user_id=%(user_id)s AND year=%(year)s
                  AND month=%(month)s AND account_type=%(account_type)s
                LIMIT 1
                """,
                {"user_id": user_id, "year": year, "month": month, "account_type": account_type},
            )
            if existing:
                execute(
                    """
                    UPDATE user_pay_detail
                    SET wages=%(wages)s, taxes=%(taxes)s, loan_interest=%(loan_interest)s,
                        car_amount=%(car_amount)s, order_amount=%(order_amount)s,
                        other_amount=%(other_amount)s, pay_amount=%(pay_amount)s
                    WHERE id=%(id)s
                    """,
                    {**data, "id": existing["id"]},
                )
            else:
                execute_insert(
                    """
                    INSERT INTO user_pay_detail
                        (addTime, deleteStatus, user_id, year, month, wages, taxes, loan_interest,
                         car_amount, order_amount, other_amount, pay_amount, status, account_type)
                    VALUES
                        (NOW(), 0, %(user_id)s, %(year)s, %(month)s, %(wages)s, %(taxes)s, %(loan_interest)s,
                         %(car_amount)s, %(order_amount)s, %(other_amount)s, %(pay_amount)s, 2, %(account_type)s)
                    """,
                    {
                        **data,
                        "user_id": user_id,
                        "year": year,
                        "month": month,
                        "account_type": account_type,
                    },
                )


# ---- company loan ----
def list_company_loan(company_id: str, year: str, account_type: int) -> list[dict[str, Any]]:
    if company_id in ("", "-1"):
        rows = fetch_all(
            """
            SELECT month, SUM(loan) AS loan, SUM(loan) AS payAmount, 0 AS id, MAX(status) AS status
            FROM company_loan_pay
            WHERE year = %(year)s AND account_type = %(account_type)s
            GROUP BY month ORDER BY month
            """,
            {"year": year, "account_type": account_type},
        )
    else:
        rows = fetch_all(
            """
            SELECT id, month, loan, loan AS payAmount, status
            FROM company_loan_pay
            WHERE company_id = %(company_id)s AND year = %(year)s AND account_type = %(account_type)s
            ORDER BY month
            """,
            {"company_id": company_id, "year": year, "account_type": account_type},
        )
    return _fill_months(rows, ["loan", "pay_amount"])


def upsert_company_loan(items: list[dict[str, Any]]) -> None:
    for item in items:
        company_id = item.get("companyId") or item.get("company_id")
        year = item.get("year")
        month = str(item.get("month") or "")
        account_type = int(item.get("accountType") or item.get("account_type") or 1)
        loan = _dec(item.get("loan"))
        row_id = int(item.get("id") or 0)
        if row_id:
            execute(
                "UPDATE company_loan_pay SET loan=%(loan)s WHERE id=%(id)s",
                {"loan": loan, "id": row_id},
            )
        else:
            existing = fetch_one(
                """
                SELECT id FROM company_loan_pay
                WHERE company_id=%(company_id)s AND year=%(year)s
                  AND month=%(month)s AND account_type=%(account_type)s
                LIMIT 1
                """,
                {
                    "company_id": company_id,
                    "year": year,
                    "month": month,
                    "account_type": account_type,
                },
            )
            if existing:
                execute(
                    "UPDATE company_loan_pay SET loan=%(loan)s WHERE id=%(id)s",
                    {"loan": loan, "id": existing["id"]},
                )
            else:
                execute_insert(
                    """
                    INSERT INTO company_loan_pay
                        (addTime, deleteStatus, company_id, year, month, status, loan, account_type)
                    VALUES
                        (NOW(), 0, %(company_id)s, %(year)s, %(month)s, 2, %(loan)s, %(account_type)s)
                    """,
                    {
                        "company_id": company_id,
                        "year": year,
                        "month": month,
                        "loan": loan,
                        "account_type": account_type,
                    },
                )


# ---- project pay ----
def list_project_pay(lab_id: str, year: str, account_type: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            id, month,
            rent_fees AS rentFees, elec_fees AS elecFees,
            labor_fees AS laborFees, parts_fees AS partsFees,
            pay_amount AS payAmount, status
        FROM project_pay_detail
        WHERE lab_id = %(lab_id)s AND year = %(year)s AND account_type = %(account_type)s
        ORDER BY month
        """,
        {"lab_id": lab_id, "year": year, "account_type": account_type},
    )
    return _fill_months(rows, ["rent_fees", "elec_fees", "labor_fees", "parts_fees", "pay_amount"])


def upsert_project_pay(items: list[dict[str, Any]]) -> None:
    for item in items:
        lab_id = item.get("labId") or item.get("lab_id")
        year = item.get("year")
        month = str(item.get("month") or "")
        account_type = int(item.get("accountType") or item.get("account_type") or 1)
        rent_fees = _dec(item.get("rentFees") or item.get("rent_fees"))
        elec_fees = _dec(item.get("elecFees") or item.get("elec_fees"))
        labor_fees = _dec(item.get("laborFees") or item.get("labor_fees"))
        parts_fees = _dec(item.get("partsFees") or item.get("parts_fees"))
        pay_amount = rent_fees + elec_fees + labor_fees + parts_fees
        row_id = int(item.get("id") or 0)
        data = {
            "rent_fees": rent_fees,
            "elec_fees": elec_fees,
            "labor_fees": labor_fees,
            "parts_fees": parts_fees,
            "pay_amount": pay_amount,
        }
        if row_id:
            execute(
                """
                UPDATE project_pay_detail
                SET rent_fees=%(rent_fees)s, elec_fees=%(elec_fees)s,
                    labor_fees=%(labor_fees)s, parts_fees=%(parts_fees)s,
                    pay_amount=%(pay_amount)s
                WHERE id=%(id)s
                """,
                {**data, "id": row_id},
            )
        else:
            existing = fetch_one(
                """
                SELECT id FROM project_pay_detail
                WHERE lab_id=%(lab_id)s AND year=%(year)s
                  AND month=%(month)s AND account_type=%(account_type)s
                LIMIT 1
                """,
                {"lab_id": lab_id, "year": year, "month": month, "account_type": account_type},
            )
            if existing:
                execute(
                    """
                    UPDATE project_pay_detail
                    SET rent_fees=%(rent_fees)s, elec_fees=%(elec_fees)s,
                        labor_fees=%(labor_fees)s, parts_fees=%(parts_fees)s,
                        pay_amount=%(pay_amount)s
                    WHERE id=%(id)s
                    """,
                    {**data, "id": existing["id"]},
                )
            else:
                execute_insert(
                    """
                    INSERT INTO project_pay_detail
                        (addTime, deleteStatus, year, month, rent_fees, elec_fees, labor_fees,
                         parts_fees, pay_amount, status, account_type, lab_id)
                    VALUES
                        (NOW(), 0, %(year)s, %(month)s, %(rent_fees)s, %(elec_fees)s, %(labor_fees)s,
                         %(parts_fees)s, %(pay_amount)s, 2, %(account_type)s, %(lab_id)s)
                    """,
                    {
                        **data,
                        "year": year,
                        "month": month,
                        "account_type": account_type,
                        "lab_id": lab_id,
                    },
                )
