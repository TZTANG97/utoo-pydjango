from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from apps.admin_fund.repositories import account as account_repo
from apps.admin_fund.repositories import settings as settings_repo
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


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


def list_project_users() -> list[dict[str, Any]]:
    """各项目资金支出：选择项目 = 实验室关联账号（对齐 Java queryAllUser）。"""
    return fetch_all(
        """
        SELECT DISTINCT t.syuser_id AS id, u.user_name AS userName, u.user_name AS user_name
        FROM experiment_lab t
        JOIN sy_users u ON t.syuser_id = u.id
        WHERE t.deleteStatus = 0 AND t.syuser_id IS NOT NULL AND t.syuser_id != ''
        ORDER BY u.user_name ASC
        """
    )


def list_labs_by_syuser(syuser_id: str) -> list[dict[str, Any]]:
    """按关联账号级联实验室（对齐 Java queryAllUserByType2 / selBySyuserId2）。"""
    if not syuser_id:
        return []
    return fetch_all(
        """
        SELECT id, lab_num AS labNum, lab_name AS labName, lab_name AS lab_name
        FROM experiment_lab
        WHERE deleteStatus = 0 AND syuser_id = %(sid)s
        ORDER BY addTime ASC
        """,
        {"sid": syuser_id},
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


def _sum_operate_log_amount(cpd_id: int, acc_type: int, log_type: int) -> Decimal:
    """对齐 Java accountLogService.selectByCpdID。"""
    try:
        val = scalar(
            """
            SELECT IFNULL(SUM(t.log_amount), 0)
            FROM account_log t
            WHERE t.id IN (
                SELECT l.account_log_id FROM account_operate_log l
                WHERE l.pay_detial_id = %(cpd_id)s AND l.log_type = %(log_type)s
            )
              AND t.acc_type = %(acc_type)s
            """,
            {"cpd_id": cpd_id, "log_type": log_type, "acc_type": acc_type},
        )
        return _dec(val)
    except Exception:
        return Decimal("0")


def _insert_operate_log(
    *,
    account_log_id: int,
    log_user: str,
    pay_detail_id: int,
    pay_amount: Decimal,
    log_type: int,
    log_info: str,
) -> None:
    try:
        execute_insert(
            """
            INSERT INTO account_operate_log
                (addTime, account_log_id, log_user_id, pay_detial_id, pay_amount, log_type, log_info)
            VALUES
                (NOW(), %(account_log_id)s, %(log_user)s, %(pay_detail_id)s,
                 %(pay_amount)s, %(log_type)s, %(log_info)s)
            """,
            {
                "account_log_id": account_log_id,
                "log_user": log_user or "",
                "pay_detail_id": pay_detail_id,
                "pay_amount": pay_amount,
                "log_type": log_type,
                "log_info": log_info,
            },
        )
    except Exception:
        pass


def company_pay_charge_back(
    *,
    company_id: str,
    year: str,
    month: str,
    pay_amount: Any,
    taxes: Any,
    fees: Any,
    wages: Any,
    system_cost: Any,
    loan: Any,
    account_type: int,
    row_id: int = 0,
    operator: str = "",
) -> str | None:
    """对齐 Java companyPay/chargeBack.ajax。失败返回错误文案。"""
    company_id = str(company_id or "").strip()
    year = str(year or "").strip()
    month = str(month or "").strip()
    if not company_id or not year or not month:
        return "请先选择所属公司和年份"
    wages_d = _dec(wages)
    taxes_d = _dec(taxes)
    fees_d = _dec(fees)
    system_d = _dec(system_cost)
    loan_d = _dec(loan)
    pay_d = _dec(pay_amount) if pay_amount not in (None, "") else (
        wages_d + taxes_d + fees_d + system_d + loan_d
    )
    # 规范化月份：存库用数字字符串，兼容 01 / 1
    try:
        month_n = str(int(month))
    except (TypeError, ValueError):
        month_n = month

    cpd_id = int(row_id or 0)
    if cpd_id:
        execute(
            """
            UPDATE company_pay_detail
            SET wages=%(wages)s, taxes=%(taxes)s, fees=%(fees)s,
                system_cost=%(system_cost)s, loan=%(loan)s, pay_amount=%(pay_amount)s
            WHERE id=%(id)s
            """,
            {
                "wages": wages_d,
                "taxes": taxes_d,
                "fees": fees_d,
                "system_cost": system_d,
                "loan": loan_d,
                "pay_amount": pay_d,
                "id": cpd_id,
            },
        )
    else:
        existing = fetch_one(
            """
            SELECT id FROM company_pay_detail
            WHERE company_id=%(company_id)s AND year=%(year)s
              AND CAST(month AS UNSIGNED)=CAST(%(month)s AS UNSIGNED)
              AND account_type=%(account_type)s
            LIMIT 1
            """,
            {
                "company_id": company_id,
                "year": year,
                "month": month_n,
                "account_type": account_type,
            },
        )
        if existing:
            cpd_id = int(existing["id"])
            execute(
                """
                UPDATE company_pay_detail
                SET wages=%(wages)s, taxes=%(taxes)s, fees=%(fees)s,
                    system_cost=%(system_cost)s, loan=%(loan)s, pay_amount=%(pay_amount)s
                WHERE id=%(id)s
                """,
                {
                    "wages": wages_d,
                    "taxes": taxes_d,
                    "fees": fees_d,
                    "system_cost": system_d,
                    "loan": loan_d,
                    "pay_amount": pay_d,
                    "id": cpd_id,
                },
            )
        else:
            cpd_id = int(
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
                        "month": month_n,
                        "taxes": taxes_d,
                        "fees": fees_d,
                        "wages": wages_d,
                        "pay_amount": pay_d,
                        "system_cost": system_d,
                        "loan": loan_d,
                        "account_type": account_type,
                    },
                )
                or 0
            )

    company = fetch_one(
        "SELECT id, syuser_id AS syuserId FROM `user` WHERE id=%(id)s LIMIT 1",
        {"id": company_id},
    )
    syuser_id = str((company or {}).get("syuserId") or "").strip()
    if not syuser_id:
        return "该用户目前没有开通账号,请重试!!!!"
    account = account_repo.get_account_by_user(syuser_id, account_type)
    if not account:
        return "该用户目前没有开通账号,请重试!!!!"

    cpd = fetch_one(
        """
        SELECT id, log_id AS logId, loan_log_id AS loanLogId, status
        FROM company_pay_detail WHERE id=%(id)s LIMIT 1
        """,
        {"id": cpd_id},
    ) or {}
    old_je = Decimal("0")
    if cpd.get("logId"):
        old_je = _sum_operate_log_amount(cpd_id, 10, 1)
    kkje = pay_d - old_je
    available = _dec(account.get("availableBalance"))
    after = available - kkje
    setting = settings_repo.get_setting() or {}
    rmb_rate = _dec(setting.get("rmbRate") or setting.get("rmb_rate") or 0)

    execute(
        """
        UPDATE account
        SET available_balance=%(available)s, year_reat=%(rate)s
        WHERE id=%(id)s
        """,
        {"available": after, "rate": rmb_rate, "id": account["id"]},
    )
    cz_num = "KK" + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, year_reat, deal_time)
        VALUES
            (NOW(), 0, 10, %(log_amount)s, %(after)s, 1,
             %(cz_num)s, %(pd_log_info)s, %(account_id)s, %(rate)s, NOW())
        """,
        {
            "log_amount": kkje,
            "after": after,
            "cz_num": cz_num,
            "pd_log_info": f"{year}{month_n}月份公司费用扣除",
            "account_id": account["id"],
            "rate": rmb_rate,
        },
    )
    _insert_operate_log(
        account_log_id=int(log_id or 0),
        log_user=operator,
        pay_detail_id=cpd_id,
        pay_amount=pay_d,
        log_type=1,
        log_info=f"各公司资金支出明细：{year}{month_n}月份费用扣除",
    )

    loan_log_id = None
    if loan_d > 0:
        old_jd = Decimal("0")
        if cpd.get("loanLogId"):
            old_jd = _sum_operate_log_amount(cpd_id, 19, 1)
        jdje = loan_d - old_jd
        jd_cz = "JD" + datetime.now().strftime("%Y%m%d%H%M%S")
        loan_log_id = execute_insert(
            """
            INSERT INTO account_log
                (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
                 cz_num, account_id, log_name, year_reat, deal_time)
            VALUES
                (NOW(), 0, 19, %(log_amount)s, %(after)s, 1,
                 %(cz_num)s, %(account_id)s, '借贷款利息支出', %(rate)s, NOW())
            """,
            {
                "log_amount": jdje,
                "after": after,
                "cz_num": jd_cz,
                "account_id": account["id"],
                "rate": rmb_rate,
            },
        )
        _insert_operate_log(
            account_log_id=int(loan_log_id or 0),
            log_user=operator,
            pay_detail_id=cpd_id,
            pay_amount=loan_d,
            log_type=1,
            log_info="各公司资金支出明细：借贷款利息支出",
        )

    if loan_log_id:
        execute(
            """
            UPDATE company_pay_detail
            SET status=1, log_id=%(log_id)s, loan_log_id=%(loan_log_id)s
            WHERE id=%(id)s
            """,
            {"log_id": log_id, "loan_log_id": loan_log_id, "id": cpd_id},
        )
    else:
        execute(
            "UPDATE company_pay_detail SET status=1, log_id=%(log_id)s WHERE id=%(id)s",
            {"log_id": log_id, "id": cpd_id},
        )
    return None


def company_pay_update_status(*, row_id: int) -> str | None:
    """对齐 Java companyPay/companyPayUpdate.ajax（修正：status→2）。"""
    if not row_id:
        return "请保存后再重试,请重试!!!!"
    row = fetch_one("SELECT id FROM company_pay_detail WHERE id=%(id)s LIMIT 1", {"id": row_id})
    if not row:
        return "请保存后再重试,请重试!!!!"
    execute("UPDATE company_pay_detail SET status=2 WHERE id=%(id)s", {"id": row_id})
    return None


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


def user_pay_charge_back(
    *,
    user_id: str,
    year: str,
    month: str,
    pay_amount: Any,
    taxes: Any,
    wages: Any,
    loan_interest: Any,
    car_amount: Any,
    order_amount: Any,
    other_amount: Any,
    account_type: int,
    row_id: int = 0,
    operator: str = "",
) -> str | None:
    """对齐 Java userPay/chargeBack.ajax。失败返回错误文案。"""
    user_id = str(user_id or "").strip()
    year = str(year or "").strip()
    month = str(month or "").strip()
    if not user_id or not year or not month:
        return "请先选择用户和年份"
    wages_d = _dec(wages)
    taxes_d = _dec(taxes)
    loan_d = _dec(loan_interest)
    car_d = _dec(car_amount)
    order_d = _dec(order_amount)
    other_d = _dec(other_amount)
    pay_d = _dec(pay_amount) if pay_amount not in (None, "") else (
        wages_d + taxes_d + loan_d + car_d + order_d + other_d
    )
    try:
        month_n = str(int(month))
    except (TypeError, ValueError):
        month_n = month

    cpd_id = int(row_id or 0)
    vals = {
        "wages": wages_d,
        "taxes": taxes_d,
        "loan_interest": loan_d,
        "car_amount": car_d,
        "order_amount": order_d,
        "other_amount": other_d,
        "pay_amount": pay_d,
    }
    if cpd_id:
        execute(
            """
            UPDATE user_pay_detail
            SET wages=%(wages)s, taxes=%(taxes)s, loan_interest=%(loan_interest)s,
                car_amount=%(car_amount)s, order_amount=%(order_amount)s,
                other_amount=%(other_amount)s, pay_amount=%(pay_amount)s
            WHERE id=%(id)s
            """,
            {**vals, "id": cpd_id},
        )
    else:
        existing = fetch_one(
            """
            SELECT id FROM user_pay_detail
            WHERE user_id=%(user_id)s AND year=%(year)s
              AND CAST(month AS UNSIGNED)=CAST(%(month)s AS UNSIGNED)
              AND account_type=%(account_type)s
            LIMIT 1
            """,
            {
                "user_id": user_id,
                "year": year,
                "month": month_n,
                "account_type": account_type,
            },
        )
        if existing:
            cpd_id = int(existing["id"])
            execute(
                """
                UPDATE user_pay_detail
                SET wages=%(wages)s, taxes=%(taxes)s, loan_interest=%(loan_interest)s,
                    car_amount=%(car_amount)s, order_amount=%(order_amount)s,
                    other_amount=%(other_amount)s, pay_amount=%(pay_amount)s
                WHERE id=%(id)s
                """,
                {**vals, "id": cpd_id},
            )
        else:
            cpd_id = int(
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
                        **vals,
                        "user_id": user_id,
                        "year": year,
                        "month": month_n,
                        "account_type": account_type,
                    },
                )
                or 0
            )

    account = account_repo.get_account_by_user(user_id, account_type)
    if not account:
        return "该用户目前没有开通账号,请重试!!!!"

    cpd = fetch_one(
        "SELECT id, log_id AS logId FROM user_pay_detail WHERE id=%(id)s LIMIT 1",
        {"id": cpd_id},
    ) or {}
    old_je = Decimal("0")
    if cpd.get("logId"):
        old_je = _sum_operate_log_amount(cpd_id, 10, 2)
    kkje = pay_d - old_je
    available = _dec(account.get("availableBalance"))
    after = available - kkje
    setting = settings_repo.get_setting() or {}
    rmb_rate = _dec(setting.get("rmbRate") or setting.get("rmb_rate") or 0)

    execute(
        """
        UPDATE account
        SET available_balance=%(available)s, year_reat=%(rate)s
        WHERE id=%(id)s
        """,
        {"available": after, "rate": rmb_rate, "id": account["id"]},
    )
    cz_num = "KK" + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, year_reat, deal_time)
        VALUES
            (NOW(), 0, 10, %(log_amount)s, %(after)s, 1,
             %(cz_num)s, %(pd_log_info)s, %(account_id)s, %(rate)s, NOW())
        """,
        {
            "log_amount": kkje,
            "after": after,
            "cz_num": cz_num,
            "pd_log_info": f"{year}{month_n}月份个人费用扣除",
            "account_id": account["id"],
            "rate": rmb_rate,
        },
    )
    _insert_operate_log(
        account_log_id=int(log_id or 0),
        log_user=operator,
        pay_detail_id=cpd_id,
        pay_amount=pay_d,
        log_type=2,
        log_info=f"个人资金支出明细:{year}{month_n}月份费用扣除",
    )
    execute(
        "UPDATE user_pay_detail SET status=1, log_id=%(log_id)s WHERE id=%(id)s",
        {"log_id": log_id, "id": cpd_id},
    )
    return None


def user_pay_update_status(*, row_id: int) -> str | None:
    """对齐 Java userPay/companyPayUpdate.ajax（修正：status→2）。"""
    if not row_id:
        return "请保存后再重试,请重试!!!!"
    row = fetch_one("SELECT id FROM user_pay_detail WHERE id=%(id)s LIMIT 1", {"id": row_id})
    if not row:
        return "请保存后再重试,请重试!!!!"
    execute("UPDATE user_pay_detail SET status=2 WHERE id=%(id)s", {"id": row_id})
    return None


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
def list_project_pay(
    lab_id: str, year: str, account_type: int, user_id: str = ""
) -> list[dict[str, Any]]:
    where = "WHERE year = %(year)s AND account_type = %(account_type)s"
    params: dict[str, Any] = {"year": year, "account_type": account_type}
    if user_id and user_id != "-1":
        where += " AND user_id = %(user_id)s"
        params["user_id"] = user_id
    if lab_id:
        where += " AND lab_id = %(lab_id)s"
        params["lab_id"] = lab_id
    if user_id == "-1" and not lab_id:
        rows = fetch_all(
            f"""
            SELECT
                month,
                SUM(rent_fees) AS rentFees, SUM(elec_fees) AS elecFees,
                SUM(labor_fees) AS laborFees, SUM(parts_fees) AS partsFees,
                SUM(pay_amount) AS payAmount, 0 AS id, MAX(status) AS status
            FROM project_pay_detail
            {where}
            GROUP BY month
            ORDER BY month
            """,
            params,
        )
    else:
        rows = fetch_all(
            f"""
            SELECT
                id, month,
                rent_fees AS rentFees, elec_fees AS elecFees,
                labor_fees AS laborFees, parts_fees AS partsFees,
                pay_amount AS payAmount, status
            FROM project_pay_detail
            {where}
            ORDER BY month
            """,
            params,
        )
    return _fill_months(rows, ["rent_fees", "elec_fees", "labor_fees", "parts_fees", "pay_amount"])


def upsert_project_pay(items: list[dict[str, Any]]) -> None:
    for item in items:
        lab_id = item.get("labId") or item.get("lab_id")
        user_id = str(item.get("userId") or item.get("user_id") or "").strip()
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
                         parts_fees, pay_amount, status, account_type, lab_id, user_id)
                    VALUES
                        (NOW(), 0, %(year)s, %(month)s, %(rent_fees)s, %(elec_fees)s, %(labor_fees)s,
                         %(parts_fees)s, %(pay_amount)s, 2, %(account_type)s, %(lab_id)s, %(user_id)s)
                    """,
                    {
                        **data,
                        "year": year,
                        "month": month,
                        "account_type": account_type,
                        "lab_id": lab_id,
                        "user_id": user_id or None,
                    },
                )
