from __future__ import annotations

from typing import Any

from apps.admin_fund.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_account_overview(
    *,
    user_name: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.user_status = 1 AND t.account_type = 0"
    params: dict[str, Any] = {}
    if user_name:
        where += " AND (t.user_name LIKE %(user_name)s OR t.true_name LIKE %(user_name)s)"
        params["user_name"] = f"%{user_name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM sy_users t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.true_name AS trueName, t.user_name AS userName,
            IFNULL(a.balance, '0,0') AS availables,
            IFNULL(a.freezing, '0,0') AS freezings,
            IFNULL(a.income, '0,0') AS incomes
        FROM sy_users t
        LEFT JOIN (
            SELECT
                ac.user_id,
                GROUP_CONCAT(ac.available_balance ORDER BY ac.account_type) AS balance,
                GROUP_CONCAT(ac.freezing_balance ORDER BY ac.account_type) AS freezing,
                GROUP_CONCAT(ac.income_total ORDER BY ac.account_type) AS income
            FROM account ac
            GROUP BY ac.user_id
        ) a ON t.id = a.user_id
        {where}
        ORDER BY t.user_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        av = str(row.get("availables") or "0,0").split(",")
        fr = str(row.get("freezings") or "0,0").split(",")
        inc = str(row.get("incomes") or "0,0").split(",")
        row["rmbAvailable"] = av[0] if len(av) > 0 else "0"
        row["usdAvailable"] = av[1] if len(av) > 1 else "0"
        row["rmbFreezing"] = fr[0] if len(fr) > 0 else "0"
        row["usdFreezing"] = fr[1] if len(fr) > 1 else "0"
        row["rmbIncome"] = inc[0] if len(inc) > 0 else "0"
        row["usdIncome"] = inc[1] if len(inc) > 1 else "0"
    return rows, total


def get_user_accounts(user_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            a.id, a.account_type AS accountType,
            a.available_balance AS availableBalance,
            a.freezing_balance AS freezingBalance,
            a.income_total AS incomeTotal,
            a.year_reat AS yearReat,
            u.user_name AS userName, u.true_name AS trueName
        FROM account a
        LEFT JOIN sy_users u ON a.user_id = u.id
        WHERE a.user_id = %(user_id)s
        ORDER BY a.account_type ASC
        """,
        {"user_id": user_id},
    )


def get_account_by_user(user_id: str, account_type: int = 1) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            a.id, a.account_type AS accountType,
            a.available_balance AS availableBalance,
            a.freezing_balance AS freezingBalance,
            a.income_total AS incomeTotal,
            u.user_name AS userName, u.true_name AS trueName
        FROM account a
        LEFT JOIN sy_users u ON a.user_id = u.id
        WHERE a.user_id = %(user_id)s AND a.account_type = %(account_type)s
        LIMIT 1
        """,
        {"user_id": user_id, "account_type": account_type},
    )


def list_account_logs(
    *,
    user_name: str = "",
    user_id: str = "",
    acc_type: str = "",
    account_type: str = "",
    log_status: str = "",
    order_id: str = "",
    add_time: str = "",
    exclude_zero: bool = False,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # 资金管理 listPage：不排除 0；资金账户 getLog 会 exclude_zero
    where = "WHERE IFNULL(log.deleteStatus, 0) = 0"
    params: dict[str, Any] = {}
    if exclude_zero:
        where += " AND IFNULL(log.log_amount, 0) != 0"
    if user_name:
        where += " AND u.user_name LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if user_id:
        where += " AND a.user_id = %(user_id)s"
        params["user_id"] = user_id
    if acc_type not in ("", None):
        if str(acc_type) == "-1":
            # 其他记录
            where += " AND (log.acc_type IN (3,5,6,7,8) OR (log.acc_type = 4 AND log.log_name IS NOT NULL))"
        else:
            where += " AND log.acc_type = %(acc_type)s"
            params["acc_type"] = acc_type
    if account_type not in ("", None):
        where += " AND a.account_type = %(account_type)s"
        params["account_type"] = account_type
    if log_status not in ("", None):
        where += " AND log.log_status = %(log_status)s"
        params["log_status"] = log_status
    if order_id:
        where += " AND IFNULL(log.cz_num, '') LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if add_time:
        where += " AND DATE_FORMAT(log.addTime, '%%Y-%%m-%%d') = %(add_time)s"
        params["add_time"] = add_time[:10]

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM account_log log
            LEFT JOIN account a ON log.account_id = a.id
            LEFT JOIN sy_users u ON a.user_id = u.id
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            log.id, log.addTime, log.acc_type AS accType,
            log.log_amount AS logAmount, log.after_log_amount AS afterLogAmount,
            log.log_status AS logStatus, log.cz_num AS czNum,
            log.pd_log_info AS pdLogInfo, log.bank_name AS bankName,
            log.card_num AS cardNum, log.deal_time AS dealTime,
            log.log_name AS logName, log.account_id AS accountId,
            log.order_id AS orderId, log.order_type AS orderType,
            log.in_account_id AS inAccountId,
            a.account_type AS accountType,
            u.user_name AS userName, u.true_name AS trueName,
            iu.user_name AS inUserName
        FROM account_log log
        LEFT JOIN account a ON log.account_id = a.id
        LEFT JOIN sy_users u ON a.user_id = u.id
        LEFT JOIN account ia ON log.in_account_id = ia.id
        LEFT JOIN sy_users iu ON ia.user_id = iu.id
        {where}
        ORDER BY log.addTime DESC, log.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def asset_summary(user_id: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    user_filter = ""
    if user_id:
        user_filter = " AND a.user_id = %(user_id)s"
        params["user_id"] = user_id
    rows = fetch_all(
        f"""
        SELECT
            a.account_type AS accountType,
            COALESCE(SUM(a.available_balance), 0) AS availableBalance,
            COALESCE(SUM(a.freezing_balance), 0) AS freezingBalance,
            COALESCE(SUM(a.income_total), 0) AS incomeTotal
        FROM account a
        WHERE 1=1 {user_filter}
        GROUP BY a.account_type
        ORDER BY a.account_type
        """,
        params,
    )
    result = {
        "rmbAvailable": 0,
        "usdAvailable": 0,
        "rmbFreezing": 0,
        "usdFreezing": 0,
        "rmbIncome": 0,
        "usdIncome": 0,
        "accounts": rows,
    }
    for row in rows:
        if int(row.get("accountType") or 0) == 1:
            result["rmbAvailable"] = float(row.get("availableBalance") or 0)
            result["rmbFreezing"] = float(row.get("freezingBalance") or 0)
            result["rmbIncome"] = float(row.get("incomeTotal") or 0)
        elif int(row.get("accountType") or 0) == 2:
            result["usdAvailable"] = float(row.get("availableBalance") or 0)
            result["usdFreezing"] = float(row.get("freezingBalance") or 0)
            result["usdIncome"] = float(row.get("incomeTotal") or 0)
    return result


def list_stat_years() -> list[int]:
    rows = fetch_all(
        """
        SELECT DISTINCT YEAR(addTime) AS y
        FROM account_log
        WHERE addTime IS NOT NULL
        ORDER BY y DESC
        LIMIT 20
        """
    )
    years = [int(r["y"]) for r in rows if r.get("y")]
    if not years:
        from datetime import datetime

        years = [datetime.now().year]
    return years


def _money_back_exp(*, user_id: str | None, account_type: int, year: str) -> float:
    params: dict[str, Any] = {"acc_type": 13, "account_type": account_type}
    where = """
        WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.log_status = 1
          AND t.acc_type = %(acc_type)s AND a.account_type = %(account_type)s
    """
    if user_id:
        where += " AND a.user_id = %(user_id)s"
        params["user_id"] = user_id
    if year:
        params["stat_year"] = year[:4]
        where += " AND YEAR(t.addTime) = %(stat_year)s"
    return float(
        scalar(
            f"""
            SELECT IFNULL(SUM(t.log_amount), 0)
            FROM account_log t
            LEFT JOIN account a ON t.account_id = a.id
            {where}
            """,
            params,
        )
        or 0
    )


def _sale_amount_admin(*, account_type: int, year: str) -> float:
    params: dict[str, Any] = {"account_type": account_type}
    year_sql = ""
    if year:
        params["stat_year"] = year[:4]
        year_sql = " AND LEFT(of.addTime, 4) = %(stat_year)s"
    exp = float(
        scalar(
            f"""
            SELECT IFNULL(SUM(of.totalPrice), 0)
            FROM experiment_order of
            WHERE of.order_type IN (6, 8)
              AND of.order_status >= 30
              AND of.currency_type = %(account_type)s
              {year_sql}
            """,
            params,
        )
        or 0
    )
    # orderform 可能无同类实验单
    try:
        oform = float(
            scalar(
                f"""
                SELECT IFNULL(SUM(of.totalPrice), 0)
                FROM orderform of
                WHERE of.order_type IN (6, 8)
                  AND of.order_status NOT IN (0)
                  AND of.currency_type = %(account_type)s
                  {year_sql}
                """,
                params,
            )
            or 0
        )
    except Exception:
        oform = 0.0
    return exp + oform


def _todo_exp_receive(*, account_type: int, year: str, user_id: str | None = None) -> float:
    """实验应收款总额（对齐 Java 口径，改用聚合避免相关子查询过慢）。"""
    params: dict[str, Any] = {"account_type": account_type}
    year_sql = ""
    user_sql = ""
    if year:
        params["stat_year"] = year[:4]
        year_sql = " AND LEFT(t.addTime, 4) = %(stat_year)s"
    if user_id:
        params["user_id"] = user_id
        user_sql = " AND t.sale_user = %(user_id)s"
    return float(
        scalar(
            f"""
            SELECT IFNULL(SUM(t.totalPrice - IFNULL(b.paid, 0)), 0)
            FROM experiment_order t
            LEFT JOIN (
                SELECT exp_of_id, SUM(money) AS paid, COUNT(*) AS bill_cnt
                FROM qd_bill
                WHERE type = 2
                GROUP BY exp_of_id
            ) b ON b.exp_of_id = t.id
            WHERE t.order_type IN (6, 8)
              AND t.order_status >= 30
              AND t.currency_type = %(account_type)s
              {year_sql}
              {user_sql}
              AND (
                  LENGTH(IFNULL(t.collection_time, ''))
                  - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
              ) > IFNULL(b.bill_cnt, 0)
            """,
            params,
        )
        or 0
    )


def _todo_exp_pay(*, account_type: int, year: str, user_id: str | None = None) -> float:
    """实验分包应付款总额。"""
    params: dict[str, Any] = {"account_type": account_type}
    year_sql = ""
    parent_user_sql = ""
    if year:
        params["stat_year"] = year[:4]
        year_sql = " AND LEFT(t.addTime, 4) = %(stat_year)s"
    if user_id:
        params["user_id"] = user_id
        parent_user_sql = " AND p.sale_user = %(user_id)s"
    return float(
        scalar(
            f"""
            SELECT IFNULL(SUM(t.totalPrice - IFNULL(b.paid, 0)), 0)
            FROM experiment_order t
            INNER JOIN experiment_order p ON t.parent_id = p.id AND p.order_type = 8
            LEFT JOIN (
                SELECT exp_of_id, SUM(money) AS paid, COUNT(*) AS bill_cnt
                FROM qd_bill
                WHERE type = 2
                GROUP BY exp_of_id
            ) b ON b.exp_of_id = t.id
            WHERE t.order_type = 9
              AND t.order_status >= 30
              AND t.currency_type = %(account_type)s
              {year_sql}
              {parent_user_sql}
              AND (
                  LENGTH(IFNULL(t.collection_time, ''))
                  - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
              ) > IFNULL(b.bill_cnt, 0)
            """,
            params,
        )
        or 0
    )


def exp_sum_by_year(*, year: str = "", user_id: str | None = None) -> dict[str, Any]:
    """对齐 Java selExpSumByYear.ajax（管理员视角：user_id 为空查全量）。"""
    uid = (user_id or "").strip() or None
    if uid:
        qnsyzermb = _sale_amount_admin(account_type=1, year=year)  # 有用户时仍按订单统计（简化）
        qnsyzeus = _sale_amount_admin(account_type=2, year=year)
    else:
        qnsyzermb = _sale_amount_admin(account_type=1, year=year)
        qnsyzeus = _sale_amount_admin(account_type=2, year=year)
    return {
        "qnsyzermb": qnsyzermb,
        "qnsyzeus": qnsyzeus,
        "rmbSyhkzsy": _money_back_exp(user_id=uid, account_type=1, year=year),
        "usSyhkzsy": _money_back_exp(user_id=uid, account_type=2, year=year),
        "rmbSyyskze": _todo_exp_receive(account_type=1, year=year, user_id=uid),
        "usSyyskze": _todo_exp_receive(account_type=2, year=year, user_id=uid),
        "rmbSyfbyfkze": _todo_exp_pay(account_type=1, year=year, user_id=uid),
        "usSyfbyfkze": _todo_exp_pay(account_type=2, year=year, user_id=uid),
    }


def create_recharge_or_withdraw(
    *,
    user_id: str,
    account_type: int,
    acc_type: int,
    log_amount: float,
    pd_log_info: str = "",
    bank_name: str = "",
    card_num: str = "",
) -> tuple[int | None, str | None]:
    account = get_account_by_user(user_id, account_type)
    if not account:
        return None, "账户不存在"
    available = float(account.get("availableBalance") or 0)
    freezing = float(account.get("freezingBalance") or 0)
    after = available
    if acc_type == 2:
        if log_amount > available:
            return None, "提现金额不可大于可用金额"
        after = available - log_amount
        execute(
            """
            UPDATE account
            SET available_balance = %(available)s,
                freezing_balance = %(freezing)s
            WHERE id = %(id)s
            """,
            {
                "available": after,
                "freezing": freezing + log_amount,
                "id": account["id"],
            },
        )
    prefix = "CZ" if acc_type == 1 else "TX"
    from datetime import datetime

    cz_num = prefix + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, bank_name, card_num, account_id)
        VALUES
            (NOW(), 0, %(acc_type)s, %(log_amount)s, %(after)s, 2,
             %(cz_num)s, %(pd_log_info)s, %(bank_name)s, %(card_num)s, %(account_id)s)
        """,
        {
            "acc_type": acc_type,
            "log_amount": log_amount,
            "after": after if acc_type == 2 else available,
            "cz_num": cz_num,
            "pd_log_info": pd_log_info or None,
            "bank_name": bank_name or None,
            "card_num": card_num or None,
            "account_id": account["id"],
        },
    )
    return log_id, None


def create_transfer_or_loan(
    *,
    user_id: str,
    account_type: int,
    acc_type: int,
    log_amount: float,
    pd_log_info: str = "",
    in_user_id: str = "",
) -> tuple[int | None, str | None]:
    account = get_account_by_user(user_id, account_type)
    if not account:
        return None, "账户不存在"
    available = float(account.get("availableBalance") or 0)
    if log_amount > available:
        return None, "金额不可大于可用金额"
    after = available - log_amount
    in_account_id = None
    if in_user_id:
        in_acc = get_account_by_user(in_user_id, account_type)
        if not in_acc:
            return None, "转入账户不存在"
        in_account_id = in_acc["id"]
    execute(
        "UPDATE account SET available_balance = %(available)s WHERE id = %(id)s",
        {"available": after, "id": account["id"]},
    )
    from datetime import datetime

    prefix = "ZZ" if acc_type == 11 else "JD"
    cz_num = prefix + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, in_account_id)
        VALUES
            (NOW(), 0, %(acc_type)s, %(log_amount)s, %(after)s, 2,
             %(cz_num)s, %(pd_log_info)s, %(account_id)s, %(in_account_id)s)
        """,
        {
            "acc_type": acc_type,
            "log_amount": log_amount,
            "after": after,
            "cz_num": cz_num,
            "pd_log_info": pd_log_info or None,
            "account_id": account["id"],
            "in_account_id": in_account_id,
        },
    )
    return log_id, None


def cancel_apply(log_id: int) -> str | None:
    return update_log_status(log_id, -2)


def update_log_status(log_id: int, status: int) -> str | None:
    """对齐 Java pass.ajax：通过/驳回/确认/取消。"""
    row = fetch_one(
        """
        SELECT id, acc_type AS accType, log_amount AS logAmount, log_status AS logStatus,
               account_id AS accountId, after_log_amount AS afterLogAmount
        FROM account_log WHERE id = %(id)s LIMIT 1
        """,
        {"id": log_id},
    )
    if not row:
        return "记录不存在"
    current = int(row.get("logStatus") or 0)
    acc_type = int(row.get("accType") or 0)
    amount = float(row.get("logAmount") or 0)
    account_id = row.get("accountId")

    # 取消申请
    if status == -2:
        if current not in (2, 3, 4, 5):
            return "当前状态不可取消"
        if acc_type == 2 and account_id:
            acc = fetch_one(
                "SELECT available_balance, freezing_balance FROM account WHERE id=%(id)s LIMIT 1",
                {"id": account_id},
            )
            if acc:
                execute(
                    """
                    UPDATE account
                    SET available_balance = %(av)s, freezing_balance = %(fr)s
                    WHERE id = %(id)s
                    """,
                    {
                        "av": float(acc.get("available_balance") or 0) + amount,
                        "fr": max(float(acc.get("freezing_balance") or 0) - amount, 0),
                        "id": account_id,
                    },
                )
        execute("UPDATE account_log SET log_status = -2 WHERE id = %(id)s", {"id": log_id})
        return None

    # 驳回
    if status == -1:
        if current != 2:
            return "当前状态不可驳回"
        if acc_type == 2 and account_id:
            acc = fetch_one(
                "SELECT available_balance, freezing_balance FROM account WHERE id=%(id)s LIMIT 1",
                {"id": account_id},
            )
            if acc:
                execute(
                    """
                    UPDATE account
                    SET available_balance = %(av)s, freezing_balance = %(fr)s
                    WHERE id = %(id)s
                    """,
                    {
                        "av": float(acc.get("available_balance") or 0) + amount,
                        "fr": max(float(acc.get("freezing_balance") or 0) - amount, 0),
                        "id": account_id,
                    },
                )
        execute("UPDATE account_log SET log_status = -1 WHERE id = %(id)s", {"id": log_id})
        return None

    # 审核通过（进入下一状态，尚未入账）
    if status in (3, 4) and current == 2:
        execute(
            "UPDATE account_log SET log_status = %(st)s WHERE id = %(id)s",
            {"st": status, "id": log_id},
        )
        return None

    # 交易成功 / 确认入账
    if status == 1:
        if current not in (2, 3, 4, 5):
            return "当前状态不可确认"
        if account_id and acc_type == 1:
            acc = fetch_one(
                "SELECT available_balance FROM account WHERE id=%(id)s LIMIT 1",
                {"id": account_id},
            )
            if acc:
                new_av = float(acc.get("available_balance") or 0) + amount
                execute(
                    "UPDATE account SET available_balance = %(av)s WHERE id = %(id)s",
                    {"av": new_av, "id": account_id},
                )
                execute(
                    """
                    UPDATE account_log
                    SET log_status = 1, after_log_amount = %(after)s, deal_time = NOW()
                    WHERE id = %(id)s
                    """,
                    {"after": new_av, "id": log_id},
                )
                return None
        if account_id and acc_type == 2:
            # 提现成功：解冻金额
            acc = fetch_one(
                "SELECT freezing_balance, available_balance FROM account WHERE id=%(id)s LIMIT 1",
                {"id": account_id},
            )
            if acc:
                execute(
                    "UPDATE account SET freezing_balance = %(fr)s WHERE id = %(id)s",
                    {
                        "fr": max(float(acc.get("freezing_balance") or 0) - amount, 0),
                        "id": account_id,
                    },
                )
        execute(
            "UPDATE account_log SET log_status = 1, deal_time = NOW() WHERE id = %(id)s",
            {"id": log_id},
        )
        return None

    execute(
        "UPDATE account_log SET log_status = %(st)s WHERE id = %(id)s",
        {"st": status, "id": log_id},
    )
    return None


def create_chargeback(
    *,
    user_id: str,
    account_type: int,
    log_amount: float,
    pd_log_info: str = "",
    auto_pass: bool = False,
) -> tuple[int | None, str | None]:
    account = get_account_by_user(user_id, account_type)
    if not account:
        return None, "账户不存在"
    available = float(account.get("availableBalance") or 0)
    if log_amount > available:
        return None, "扣款金额不可大于可用金额"
    after = available - log_amount
    status = 1 if auto_pass else 5
    if status == 1:
        execute(
            "UPDATE account SET available_balance = %(available)s WHERE id = %(id)s",
            {"available": after, "id": account["id"]},
        )
    from datetime import datetime

    cz_num = "KK" + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, deal_time)
        VALUES
            (NOW(), 0, 10, %(log_amount)s, %(after)s, %(status)s,
             %(cz_num)s, %(pd_log_info)s, %(account_id)s, %(deal_time)s)
        """,
        {
            "log_amount": log_amount,
            "after": after if status == 1 else available,
            "status": status,
            "cz_num": cz_num,
            "pd_log_info": pd_log_info or None,
            "account_id": account["id"],
            "deal_time": datetime.now() if status == 1 else None,
        },
    )
    return log_id, None


def create_loan_clear(
    *,
    user_id: str,
    account_type: int,
    log_amount: float,
    pd_log_info: str = "",
    auto_pass: bool = False,
) -> tuple[int | None, str | None]:
    account = get_account_by_user(user_id, account_type)
    if not account:
        return None, "账户不存在"
    available = float(account.get("availableBalance") or 0)
    status = 1 if auto_pass else 2
    after = available
    if status == 1:
        if log_amount > available:
            return None, "金额不可大于可用金额"
        after = available - log_amount
        execute(
            "UPDATE account SET available_balance = %(available)s WHERE id = %(id)s",
            {"available": after, "id": account["id"]},
        )
    from datetime import datetime

    cz_num = "LX" + datetime.now().strftime("%Y%m%d%H%M%S")
    log_id = execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, log_name)
        VALUES
            (NOW(), 0, 17, %(log_amount)s, %(after)s, %(status)s,
             %(cz_num)s, %(pd_log_info)s, %(account_id)s, '借贷利息清算')
        """,
        {
            "log_amount": log_amount,
            "after": after,
            "status": status,
            "cz_num": cz_num,
            "pd_log_info": pd_log_info or None,
            "account_id": account["id"],
        },
    )
    return log_id, None


def list_fund_users(keyword: str = "") -> list[dict[str, Any]]:
    where = "WHERE user_status = 1"
    params: dict[str, Any] = {}
    if keyword:
        where += " AND (user_name LIKE %(kw)s OR true_name LIKE %(kw)s)"
        params["kw"] = f"%{keyword}%"
    return fetch_all(
        f"""
        SELECT id, user_name AS userName, true_name AS trueName
        FROM sy_users
        {where}
        ORDER BY user_name ASC
        LIMIT 200
        """,
        params,
    )
