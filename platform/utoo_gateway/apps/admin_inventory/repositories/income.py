from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

PAY_TYPE_LABELS = {
    1: "进口增值税",
    2: "关税",
    3: "手续费",
    4: "运费",
    5: "其他",
}


def _dec(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def _rate() -> Decimal:
    row = fetch_one("SELECT us_exchange_rate AS rate FROM account_setting LIMIT 1") or {}
    rate = _dec(row.get("rate") or 1)
    return rate if rate > 0 else Decimal("1")


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _rent_payback_total(currency_type: int) -> Decimal:
    """对齐 StatisticRentPayBackMapper.selZlyhkze（字段是 currency_type，不是 account_type）。"""
    if currency_type == 2:
        row = fetch_one(
            """
            SELECT IFNULL(SUM(ROUND(
                t.back_total * (SELECT a.us_exchange_rate FROM account_setting a LIMIT 1),
                2
            )), 0) AS zje
            FROM statistic_rent_payback t
            WHERE t.currency_type = 2
            """
        ) or {}
    else:
        row = fetch_one(
            """
            SELECT IFNULL(SUM(t.back_total), 0) AS zje
            FROM statistic_rent_payback t
            WHERE t.currency_type = 1
            """
        ) or {}
    return _dec(row.get("zje"))


def _platform_exp_payback(currency_type: int) -> Decimal:
    """对齐 InIncomeMapper.selPtsyhkze：实验回款 × 公司账号分成比例。"""
    money_expr = (
        "t.money * (SELECT a.us_exchange_rate FROM account_setting a LIMIT 1) * tab2.scal / 100"
        if currency_type == 2
        else "t.money * tab2.scal / 100"
    )
    row = fetch_one(
        f"""
        SELECT IFNULL(ROUND(SUM(ROUND({money_expr}, 2)), 2), 0) AS zje
        FROM qd_bill t
        LEFT JOIN experiment_order ofr ON t.of_id = ofr.id
        LEFT JOIN (
            SELECT tab1.id, ROUND(SUM(tab1.scal), 2) AS scal
            FROM (
                SELECT
                    tab.id,
                    SUBSTRING_INDEX(SUBSTRING_INDEX(tab.user_scale_info1, '_', 1), '_', -1) AS uid,
                    SUBSTRING_INDEX(SUBSTRING_INDEX(tab.user_scale_info1, '_', 2), '_', -1) AS scal
                FROM (
                    SELECT
                        t.id,
                        SUBSTRING_INDEX(
                            SUBSTRING_INDEX(t.user_scale_info, ',', b.increID + 1),
                            ',',
                            -1
                        ) AS user_scale_info1
                    FROM experiment_order t
                    JOIN incre_table b
                      ON b.increID < (
                            LENGTH(t.user_scale_info)
                            - LENGTH(REPLACE(t.user_scale_info, ',', ''))
                            + 1
                         )
                    WHERE t.order_type IN (6, 8)
                ) tab
            ) tab1
            LEFT JOIN user u ON tab1.uid = u.syuser_id
            WHERE u.id IS NOT NULL
            GROUP BY tab1.id
        ) tab2 ON t.of_id = tab2.id
        WHERE ofr.order_type IN (6, 8)
          AND ofr.id IS NOT NULL
          AND t.type = 2
          AND IFNULL(ofr.order_status, 0) != 0
          AND IFNULL(t.is_split, 0) = 1
          AND ofr.currency_type = %(currency_type)s
        """,
        {"currency_type": currency_type},
    ) or {}
    return _dec(row.get("zje"))


def overview_kpis() -> dict[str, Any]:
    """对齐 Java incomeDetail.htm 当前有效汇总字段。"""
    rate = _rate()
    rmb_invest = _dec(
        (fetch_one("SELECT IFNULL(SUM(tz_amount),0) AS v FROM in_income WHERE type IN (1,2) AND account_type=1") or {}).get("v")
    )
    usd_invest = _dec(
        (fetch_one("SELECT IFNULL(SUM(tz_amount),0) AS v FROM in_income WHERE type IN (1,2) AND account_type=2") or {}).get("v")
    )
    trcbze = rmb_invest + usd_invest * rate

    # Java selKcTotalAmont：SUM(goods_price)，不含数量乘积
    kczjz = _dec(
        (
            fetch_one(
                """
                SELECT IFNULL(SUM(t.goods_price), 0) AS v
                FROM goods_inventory t
                WHERE t.gi_status NOT IN (3, 4, 21, 16)
                """
            )
            or {}
        ).get("v")
    )

    zlyhkzh = _rent_payback_total(1) + _rent_payback_total(2)
    syzhk = _platform_exp_payback(1) + _platform_exp_payback(2)

    # Java 当前 UI 这些字段硬编码为 0
    ptzlyhkze = Decimal("0")
    grzlyhkze = Decimal("0")
    zzsccbze = Decimal("0")
    zzcgwfk = Decimal("0")
    kcxscbhkze = Decimal("0")

    # 平台已回款 = 平台租赁 + 平台实验 + 库存销售毛利
    yhkze = ptzlyhkze + syzhk + zzsccbze
    # 当前总收益 = 平台已回款 - 库存总价值
    dqzsy = yhkze - kczjz

    return {
        "dqzsy": _money(dqzsy),
        "kczjz": _money(kczjz),
        "yhkze": _money(yhkze),
        "zlyhkzh": _money(zlyhkzh),
        "ptzlyhkze": _money(ptzlyhkze),
        "grzlyhkze": _money(grzlyhkze),
        "kcxscbhkze": _money(kcxscbhkze),
        "zzsccbze": _money(zzsccbze),
        "syzhk": _money(syzhk),
        "zzcgwfk": _money(zzcgwfk),
        "zlxszejz": None,
        "syxszejz": None,
        # 兼容旧前端字段
        "investTotal": _money(trcbze),
        "rmbInvest": _money(rmb_invest),
        "usdInvest": _money(usd_invest * rate),
        "exchangeRate": float(rate),
        "stockValue": _money(kczjz),
    }


def list_income(
    *,
    income_type: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if str(income_type) == "3":
        where += " AND t.type = 3"
    else:
        where += " AND t.type IN (1, 2)"
    total = int(scalar(f"SELECT COUNT(*) FROM in_income t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.type, t.account_type AS accountType,
            t.tz_amount AS tzAmount, t.th_amount AS thAmount,
            t.total_amount AS totalAmount, t.deal_time AS dealTime,
            t.user_id AS userId, t.add_user AS addUser, t.mark,
            t.pay_type AS payType, t.project_type AS projectType,
            u.user_name AS userName, u.true_name AS trueName,
            u1.user_name AS jlr,
            a.path AS voucherPath, a.name AS voucherName
        FROM in_income t
        LEFT JOIN sy_users u ON t.user_id = u.id
        LEFT JOIN sy_users u1 ON t.add_user = u1.id
        LEFT JOIN accessory a ON t.accessory_id = a.id
        {where}
        ORDER BY t.deal_time DESC, t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        pay_type = row.get("payType")
        try:
            row["payTypeLabel"] = PAY_TYPE_LABELS.get(int(pay_type), str(pay_type or ""))
        except (TypeError, ValueError):
            row["payTypeLabel"] = ""
        row["accountTypeLabel"] = "美金" if int(row.get("accountType") or 1) == 2 else "人民币"
    return rows, total


def list_ratio_matrix() -> dict[str, Any]:
    """投资比例明细：优先 statistic_in_income，否则从 in_income 推算。"""
    months_rows = fetch_all(
        """
        SELECT DISTINCT DATE_FORMAT(deal_time, '%%Y-%%m') AS month
        FROM in_income
        WHERE type IN (1, 2) AND deal_time IS NOT NULL
        ORDER BY month ASC
        """
    )
    months = [str(r["month"]) for r in months_rows if r.get("month")]
    users = fetch_all(
        """
        SELECT DISTINCT t.user_id AS userId, u.user_name AS userName
        FROM in_income t
        LEFT JOIN sy_users u ON t.user_id = u.id
        WHERE t.type IN (1, 2) AND t.user_id IS NOT NULL
        ORDER BY u.user_name ASC
        """
    )
    rate = _rate()

    def month_amount(user_id: str, month: str) -> Decimal:
        # 截至该月累计投资额
        row = fetch_one(
            """
            SELECT IFNULL(SUM(
                CASE
                  WHEN account_type = 2 THEN tz_amount * %(rate)s
                  ELSE tz_amount
                END
            ), 0) AS v
            FROM in_income
            WHERE type IN (1, 2)
              AND user_id = %(uid)s
              AND DATE_FORMAT(deal_time, '%%Y-%%m') <= %(month)s
            """,
            {"uid": user_id, "month": month, "rate": float(rate)},
        ) or {}
        return _dec(row.get("v"))

    zjelist: list[dict[str, Any]] = []
    month_totals: list[Decimal] = []
    for month in months:
        total = Decimal("0")
        for u in users:
            total += month_amount(str(u["userId"]), month)
        month_totals.append(total)
        zjelist.append({"month": month, "num": _money(total)})

    user_list: list[dict[str, Any]] = []
    for u in users:
        month_total = []
        for i, month in enumerate(months):
            amount = month_amount(str(u["userId"]), month)
            total = month_totals[i]
            scale = Decimal("0")
            if total > 0:
                scale = (amount * Decimal("100") / total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            month_total.append({"scale": float(scale), "tz_amount": _money(amount)})
        user_list.append(
            {
                "userId": u.get("userId"),
                "userName": u.get("userName"),
                "monthTotal": month_total,
            }
        )
    return {
        "months": [{"month": m, "num": zjelist[i]["num"]} for i, m in enumerate(months)],
        "userList": user_list,
        "zjelist": zjelist,
    }


def list_invest_users(*, account_type: int = 1) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT DISTINCT t.user_id AS userId, u.user_name AS userName, u.true_name AS trueName,
               (
                 SELECT IFNULL(SUM(i.tz_amount), 0)
                 FROM in_income i
                 WHERE i.user_id = t.user_id
                   AND i.account_type = %(account_type)s
                   AND i.type IN (1, 2)
               ) AS tzze
        FROM in_income t
        LEFT JOIN sy_users u ON t.user_id = u.id
        WHERE t.account_type = %(account_type)s
          AND t.project_type = 1
          AND t.user_id IS NOT NULL
        ORDER BY u.user_name ASC
        """,
        {"account_type": account_type},
    )
    return rows


def list_all_users(keyword: str = "") -> list[dict[str, Any]]:
    # 对齐后台员工选择：仅启用且 pt_type 含后台身份
    where = "WHERE user_status = 1 AND pt_type LIKE %(pt)s"
    params: dict[str, Any] = {"pt": "%2%"}
    if keyword:
        where += " AND (user_name LIKE %(kw)s OR true_name LIKE %(kw)s)"
        params["kw"] = f"%{keyword}%"
    return fetch_all(
        f"""
        SELECT id, user_name AS userName, true_name AS trueName
        FROM sy_users
        {where}
        ORDER BY user_name ASC
        LIMIT 500
        """,
        params,
    )


def _get_account(user_id: str, account_type: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, available_balance AS availableBalance, freezing_balance AS freezingBalance
        FROM account
        WHERE user_id = %(uid)s AND account_type = %(account_type)s
        LIMIT 1
        """,
        {"uid": user_id, "account_type": account_type},
    )


def _insert_account_log(
    *,
    account_id: int,
    acc_type: int,
    amount: float,
    after: float,
    info: str,
) -> None:
    from datetime import datetime as dt

    prefix = {3: "TZ", 6: "CZ", 7: "TH"}.get(acc_type, "II")
    cz_num = prefix + dt.now().strftime("%Y%m%d%H%M%S")
    execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, acc_type, log_amount, after_log_amount, log_status,
             cz_num, pd_log_info, account_id, deal_time)
        VALUES
            (NOW(), 0, %(acc_type)s, %(amount)s, %(after)s, 1,
             %(cz_num)s, %(info)s, %(account_id)s, NOW())
        """,
        {
            "acc_type": acc_type,
            "amount": amount,
            "after": after,
            "cz_num": cz_num,
            "info": info or None,
            "account_id": account_id,
        },
    )


def create_invest(
    *,
    user_id: str,
    account_type: int,
    log_amount: float,
    deal_time: str = "",
    mark: str = "",
    add_user: str = "",
    project_type: int = 1,
) -> tuple[int | None, str | None]:
    if not user_id:
        return None, "请选择参与人"
    if log_amount <= 0:
        return None, "金额必须大于0"
    acc = _get_account(user_id, account_type)
    if not acc:
        return None, "账户不存在"
    available = float(acc.get("availableBalance") or 0)
    freezing = float(acc.get("freezingBalance") or 0)
    if log_amount > available:
        return None, "投资金额不可大于可用余额"
    new_available = available - log_amount
    new_freezing = freezing + log_amount
    execute(
        """
        UPDATE account
        SET available_balance = %(av)s, freezing_balance = %(fr)s
        WHERE id = %(id)s
        """,
        {"av": new_available, "fr": new_freezing, "id": acc["id"]},
    )
    _insert_account_log(
        account_id=int(acc["id"]),
        acc_type=3,
        amount=log_amount,
        after=new_available,
        info=mark or "投资冻结",
    )
    total_amount = float(
        (
            fetch_one(
                """
                SELECT IFNULL(SUM(tz_amount), 0) AS v
                FROM in_income
                WHERE user_id = %(uid)s AND account_type = %(account_type)s AND type IN (1, 2)
                """,
                {"uid": user_id, "account_type": account_type},
            )
            or {}
        ).get("v")
        or 0
    ) + log_amount
    deal = deal_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_id = execute_insert(
        """
        INSERT INTO in_income
            (addTime, deleteStatus, account_type, tz_amount, th_amount, project_type,
             user_id, mark, type, add_user, deal_time, total_amount)
        VALUES
            (NOW(), 0, %(account_type)s, %(tz_amount)s, 0, %(project_type)s,
             %(user_id)s, %(mark)s, 1, %(add_user)s, %(deal_time)s, %(total_amount)s)
        """,
        {
            "account_type": account_type,
            "tz_amount": log_amount,
            "project_type": project_type,
            "user_id": user_id,
            "mark": mark or None,
            "add_user": add_user or None,
            "deal_time": deal,
            "total_amount": total_amount,
        },
    )
    return log_id, None


def create_disinvest(
    *,
    user_id: str,
    account_type: int,
    log_amount: float,
    th_amount: float = 0,
    deal_time: str = "",
    mark: str = "",
    add_user: str = "",
    project_type: int = 1,
) -> tuple[int | None, str | None]:
    if not user_id:
        return None, "请选择参与人"
    if log_amount <= 0:
        return None, "金额必须大于0"
    if th_amount < 0:
        return None, "退还金额不能为负"
    acc = _get_account(user_id, account_type)
    if not acc:
        return None, "账户不存在"
    available = float(acc.get("availableBalance") or 0)
    freezing = float(acc.get("freezingBalance") or 0)
    if log_amount > freezing:
        return None, "撤资金额不可大于冻结金额"
    # 解冻撤资金额，再按退还金额从可用扣减（对齐 Java 解冻+退还）
    new_freezing = freezing - log_amount
    new_available = available + log_amount - th_amount
    if new_available < 0:
        return None, "退还后可用余额不足"
    execute(
        """
        UPDATE account
        SET available_balance = %(av)s, freezing_balance = %(fr)s
        WHERE id = %(id)s
        """,
        {"av": new_available, "fr": new_freezing, "id": acc["id"]},
    )
    _insert_account_log(
        account_id=int(acc["id"]),
        acc_type=6,
        amount=log_amount,
        after=available + log_amount,
        info=mark or "撤资解冻",
    )
    if th_amount > 0:
        _insert_account_log(
            account_id=int(acc["id"]),
            acc_type=7,
            amount=th_amount,
            after=new_available,
            info=mark or "撤资退还",
        )
    total_amount = float(
        (
            fetch_one(
                """
                SELECT IFNULL(SUM(tz_amount), 0) AS v
                FROM in_income
                WHERE user_id = %(uid)s AND account_type = %(account_type)s AND type IN (1, 2)
                """,
                {"uid": user_id, "account_type": account_type},
            )
            or {}
        ).get("v")
        or 0
    ) - log_amount
    deal = deal_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_id = execute_insert(
        """
        INSERT INTO in_income
            (addTime, deleteStatus, account_type, tz_amount, th_amount, project_type,
             user_id, mark, type, add_user, deal_time, total_amount)
        VALUES
            (NOW(), 0, %(account_type)s, %(tz_amount)s, %(th_amount)s, %(project_type)s,
             %(user_id)s, %(mark)s, 2, %(add_user)s, %(deal_time)s, %(total_amount)s)
        """,
        {
            "account_type": account_type,
            "tz_amount": -abs(log_amount),
            "th_amount": th_amount,
            "project_type": project_type,
            "user_id": user_id,
            "mark": mark or None,
            "add_user": add_user or None,
            "deal_time": deal,
            "total_amount": total_amount,
        },
    )
    return log_id, None


def create_other_pay(
    *,
    account_type: int,
    log_amount: float,
    pay_type: int,
    deal_time: str = "",
    mark: str = "",
    add_user: str = "",
    accessory_id: str | None = None,
) -> tuple[int | None, str | None]:
    if log_amount <= 0:
        return None, "金额必须大于0"
    if pay_type not in PAY_TYPE_LABELS:
        return None, "请选择代付类型"
    deal = deal_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_id = execute_insert(
        """
        INSERT INTO in_income
            (addTime, deleteStatus, account_type, tz_amount, th_amount, project_type,
             user_id, mark, type, pay_type, accessory_id, add_user, deal_time, total_amount)
        VALUES
            (NOW(), 0, %(account_type)s, %(tz_amount)s, 0, 1,
             NULL, %(mark)s, 3, %(pay_type)s, %(accessory_id)s, %(add_user)s, %(deal_time)s, %(tz_amount)s)
        """,
        {
            "account_type": account_type,
            "tz_amount": log_amount,
            "mark": mark or None,
            "pay_type": pay_type,
            "accessory_id": accessory_id,
            "add_user": add_user or None,
            "deal_time": deal,
        },
    )
    return log_id, None
