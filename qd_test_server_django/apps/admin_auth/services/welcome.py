from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_digital.repositories import stats as stats_repo
from apps.admin_fund.repositories import account as account_repo
from apps.core.db_utils import fetch_all, scalar


def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java IndexViewController.indexHtml（welcome.htm）的 userType。"""
    role = (utoo_type or "").strip()
    if not role:
        return 0
    upper = role.upper()
    if "系统管理员" in role or upper == "ADMIN" or role == "admin":
        return 1
    if "公司基金" in role or "公司账号" in role or role == "公司":
        return 2
    if "销售主管" in role:
        return 3
    if role == "测试人员" or "测试人员" in role:
        return 4
    if "制单" in role:
        return 5
    if "外部投资" in role or role == "投资":
        return 6
    if "仓库" in role:
        return 7
    if "H类" in role or role.startswith("H类") or upper.startswith("H_"):
        return 14
    if "销售" in role or "原厂" in role or "C类" in role:
        return 4
    return 0


def _resolve_welcome_user_type2(utoo_type: str | None, user_type: int) -> int:
    role = (utoo_type or "").strip()
    if role == "测试人员" or "测试人员" in role:
        return 3
    if user_type == 1:
        return 1
    if user_type in (3, 4, 14) or "销售" in role or "H类" in role:
        if "测试" in role and "测试人员" not in role:
            return 0
        return 2
    return 0


def previous_six_months(*, today: date | None = None) -> list[str]:
    base = today or date.today()
    year, month = base.year, base.month
    months: list[str] = [""] * 6
    for i in range(5, -1, -1):
        months[i] = f"{year:04d}-{month:02d}"
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return months


def _months_of_year(year: int, *, today: date | None = None) -> list[str]:
    """当年截至本月（或往年 12 个月）的 yyyy-MM 列表。"""
    base = today or date.today()
    end_m = 12 if year < base.year else base.month
    return [f"{year:04d}-{m:02d}" for m in range(1, end_m + 1)]


def _money_wan(raw: Any) -> str:
    if raw is None or raw == "":
        return "0"
    try:
        v = (Decimal(str(raw)) / Decimal(10000)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return format(v, "f")
    except Exception:
        return "0"


def _fill_months(months: list[str], by_month: dict[str, Any], *, as_wan: bool) -> list[str]:
    values: list[str] = []
    for m in months:
        raw = by_month.get(m)
        if raw is None or raw == "":
            values.append("0")
            continue
        if as_wan:
            values.append(_money_wan(raw))
        else:
            try:
                values.append(str(int(Decimal(str(raw)))))
            except Exception:
                values.append("0")
    return values


def _count_audit(order_type: str | int) -> int:
    return int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order
            WHERE CAST(order_type AS CHAR) = CAST(%(ot)s AS CHAR)
              AND order_status = 20
            """,
            {"ot": str(order_type)},
        )
        or 0
    )


def _pending_for_sale_manager() -> dict[str, Any]:
    """销售主管待审 KPI —— 对齐图一命名（类型：6/10/8/9）。"""
    return {
        "expOrder": _count_audit(6),
        "selfChildOrder": _count_audit(10),
        "subcontractOrder": _count_audit(8),
        "subcontractSubOrder": _count_audit(9),
        # 物资分包子单：暂无稳定表映射，保持字段供前端展示
        "materialSubOrder": 0,
    }


def _count_finish_by_sale_user(*, sale_user_id: str, order_status: int) -> int:
    """销售人员名下主单关联的测试完成表状态计数（对齐 Java getOrderListSize*）。"""
    if not sale_user_id:
        return 0
    return int(
        scalar(
            """
            SELECT COUNT(t.id)
            FROM statistic_experiment_finish t
            INNER JOIN experiment_order eo ON t.order_id = eo.id
            WHERE IFNULL(t.deleteStatus, 0) = 0
              AND CAST(eo.sale_user AS CHAR) = CAST(%(uid)s AS CHAR)
              AND t.order_status = %(st)s
            """,
            {"uid": sale_user_id, "st": int(order_status)},
        )
        or 0
    )


def _ops_counts(*, user_id: str, user_type: int, user_type2: int) -> dict[str, int]:
    """运营 KPI。

    - 销售人员(userType=4,ut2=2)：未开始/进行中/测试通过（按 sale_user 过滤）
    - 销售主管：未开始/进行中/超时（全量）
    - 测试人员：本人未开始/进行中/通过
    """
    # 销售人员：按本人销售主单关联的测试单
    if user_type == 4 and user_type2 == 2:
        return {
            "notStarted": _count_finish_by_sale_user(sale_user_id=user_id, order_status=0),
            "inProgress": _count_finish_by_sale_user(sale_user_id=user_id, order_status=1),
            "passed": _count_finish_by_sale_user(sale_user_id=user_id, order_status=2),
            "timeout": 0,
            "opsMode": "salesperson",
        }

    scope_uid = ""
    if user_type2 == 3:
        scope_uid = user_id
    try:
        not_started = int(
            stats_repo.order_count(user_id=scope_uid, order_status=0, period_type="5") or 0
        )
        in_progress = int(
            stats_repo.order_count(user_id=scope_uid, order_status=1, period_type="5") or 0
        )
        if user_type2 == 3:
            passed = int(
                stats_repo.order_count(user_id=scope_uid, order_status=2, period_type="5") or 0
            )
            timeout = 0
            mode = "tester"
        else:
            passed = 0
            timeout = int(
                stats_repo.order_count(
                    user_id=scope_uid, order_status=-1, is_timeout=1, period_type="5"
                )
                or 0
            )
            mode = "manager"
    except Exception:
        not_started = in_progress = passed = timeout = 0
        mode = "manager"
    return {
        "notStarted": not_started,
        "inProgress": in_progress,
        "passed": passed,
        "timeout": timeout,
        "opsMode": mode,
    }


def _test_qty_year_chart(*, year: int, sale_user_id: str = "") -> dict[str, Any]:
    """测试数量(年)：按月完成量。销售人员限定其主单关联。"""
    months = _months_of_year(year)
    params: dict[str, Any] = {"year": str(year)}
    sale_sql = ""
    join_sql = ""
    if sale_user_id:
        join_sql = "INNER JOIN experiment_order eo ON t.order_id = eo.id"
        sale_sql = "AND CAST(eo.sale_user AS CHAR) = CAST(%(uid)s AS CHAR)"
        params["uid"] = sale_user_id
    rows = fetch_all(
        f"""
        SELECT DATE_FORMAT(t.end_time, '%%Y-%%m') AS ym, COUNT(*) AS cnt
        FROM statistic_experiment_finish t
        {join_sql}
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND t.order_status = 2
          AND t.end_time IS NOT NULL
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
          {sale_sql}
        GROUP BY DATE_FORMAT(t.end_time, '%%Y-%%m')
        ORDER BY ym
        """,
        params,
    )
    by_m = {str(r.get("ym") or ""): int(r.get("cnt") or 0) for r in rows}
    return {
        "year": str(year),
        "months": months,
        "values": [by_m.get(m, 0) for m in months],
    }


def _tester_qty_month_chart(*, year: int, month: int, sale_user_id: str = "") -> dict[str, Any]:
    """测试人员测试数量(月)：当月各测试员完成量。"""
    ym = f"{year:04d}-{month:02d}"
    params: dict[str, Any] = {"ym": ym}
    sale_sql = ""
    join_sql = ""
    if sale_user_id:
        join_sql = "INNER JOIN experiment_order eo ON t.order_id = eo.id"
        sale_sql = "AND CAST(eo.sale_user AS CHAR) = CAST(%(uid)s AS CHAR)"
        params["uid"] = sale_user_id
    rows = fetch_all(
        f"""
        SELECT
            IFNULL(NULLIF(TRIM(u.true_name), ''), IFNULL(u.user_name, t.test_user_id)) AS name,
            COUNT(*) AS cnt
        FROM statistic_experiment_finish t
        {join_sql}
        LEFT JOIN sy_users u ON CAST(u.id AS CHAR) = CAST(t.test_user_id AS CHAR)
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND t.order_status = 2
          AND t.test_user_id IS NOT NULL
          AND DATE_FORMAT(t.end_time, '%%Y-%%m') = %(ym)s
          {sale_sql}
        GROUP BY t.test_user_id, name
        ORDER BY cnt DESC
        LIMIT 30
        """,
        params,
    )
    return {
        "month": ym,
        "names": [str(r.get("name") or "") for r in rows],
        "values": [int(r.get("cnt") or 0) for r in rows],
    }


def _chart_admin_trade(months: list[str]) -> list[str]:
    if not months:
        return []
    placeholders = ", ".join(f"%(m{i})s" for i in range(len(months)))
    params = {f"m{i}": m for i, m in enumerate(months)}
    rows = fetch_all(
        f"""
        SELECT
            DATE_FORMAT(order_time, '%%Y-%%m') AS xdate,
            SUM(totalPrice) AS price
        FROM experiment_order
        WHERE order_type IN (6, 8)
          AND order_status >= 30
          AND DATE_FORMAT(order_time, '%%Y-%%m') IN ({placeholders})
        GROUP BY DATE_FORMAT(order_time, '%%Y-%%m')
        """,
        params,
    )
    by_month = {str(r.get("xdate") or ""): r.get("price") for r in rows}
    return _fill_months(months, by_month, as_wan=True)


def _chart_user_test_count(months: list[str], user_id: str) -> list[str]:
    if not months or not user_id:
        return ["0"] * len(months)
    placeholders = ", ".join(f"%(m{i})s" for i in range(len(months)))
    params: dict[str, Any] = {f"m{i}": m for i, m in enumerate(months)}
    params["user_id"] = user_id
    rows = fetch_all(
        f"""
        SELECT
            DATE_FORMAT(c.add_time, '%%Y-%%m') AS xdate,
            COUNT(*) AS cnt
        FROM experiment_order_child c
        WHERE CAST(c.test_user_id AS CHAR) = CAST(%(user_id)s AS CHAR)
          AND c.test_user_id IS NOT NULL
          AND CAST(c.test_user_id AS CHAR) NOT IN ('', '22')
          AND DATE_FORMAT(c.add_time, '%%Y-%%m') IN ({placeholders})
        GROUP BY DATE_FORMAT(c.add_time, '%%Y-%%m')
        """,
        params,
    )
    by_month = {str(r.get("xdate") or ""): r.get("cnt") for r in rows}
    return _fill_months(months, by_month, as_wan=False)


def _user_sale_by_year(
    *,
    user_id: str,
    year: int,
    order_type_filter: str = "",
) -> dict[str, Any]:
    """对齐 Java selUserSaleByYear / welcome 注入的双币种月柱图。"""
    months = _months_of_year(year)
    empty = {
        "year": str(year),
        "xmonths": months,
        "userSaleAryrmb": ["0"] * len(months),
        "userSaleAryus": ["0"] * len(months),
        "qnxsrmb": "0.00",
        "qnxsus": "0.00",
        "ddslrmb": 0,
        "ddslus": 0,
        "grmlzhbigdecimal": "0.00",
        "grmlllbigdecimal": "0.00",
    }
    if not user_id or not months:
        return empty

    type_sql = "AND order_type IN (6, 8)"
    if order_type_filter == "1":
        type_sql = "AND CAST(order_type AS CHAR) = '6'"
    elif order_type_filter == "2":
        type_sql = "AND CAST(order_type AS CHAR) = '8'"

    params: dict[str, Any] = {"user_id": user_id, "year": str(year)}
    rows = fetch_all(
        f"""
        SELECT
            DATE_FORMAT(order_time, '%%Y-%%m') AS xdate,
            IFNULL(currency_type, 1) AS currencyType,
            SUM(IFNULL(totalPrice, 0)) AS price,
            COUNT(*) AS cnt
        FROM experiment_order
        WHERE CAST(sale_user AS CHAR) = CAST(%(user_id)s AS CHAR)
          AND order_status >= 30
          {type_sql}
          AND DATE_FORMAT(order_time, '%%Y') = %(year)s
        GROUP BY DATE_FORMAT(order_time, '%%Y-%%m'), IFNULL(currency_type, 1)
        """,
        params,
    )
    rmb_by: dict[str, Decimal] = {}
    usd_by: dict[str, Decimal] = {}
    cnt_rmb = 0
    cnt_usd = 0
    for r in rows:
        m = str(r.get("xdate") or "")
        try:
            ct = int(r.get("currencyType") or 1)
        except Exception:
            ct = 1
        try:
            price = Decimal(str(r.get("price") or 0))
        except Exception:
            price = Decimal(0)
        try:
            cnt = int(r.get("cnt") or 0)
        except Exception:
            cnt = 0
        if ct == 2:
            usd_by[m] = usd_by.get(m, Decimal(0)) + price
            cnt_usd += cnt
        else:
            rmb_by[m] = rmb_by.get(m, Decimal(0)) + price
            cnt_rmb += cnt

    def series(src: dict[str, Decimal]) -> list[str]:
        out: list[str] = []
        for m in months:
            v = src.get(m, Decimal(0))
            out.append(format(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"))
        return out

    rmb_s = series(rmb_by)
    usd_s = series(usd_by)
    sum_rmb = sum((Decimal(x) for x in rmb_s), Decimal(0))
    sum_usd = sum((Decimal(x) for x in usd_s), Decimal(0))
    return {
        "year": str(year),
        "xmonths": months,
        "userSaleAryrmb": rmb_s,
        "userSaleAryus": usd_s,
        "qnxsrmb": format(sum_rmb.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "qnxsus": format(sum_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "ddslrmb": cnt_rmb,
        "ddslus": cnt_usd,
        "grmlzhbigdecimal": "0.00",
        "grmlllbigdecimal": "0.00",
    }


def _user_available_balances(user_id: str) -> tuple[str, str]:
    if not user_id:
        return "0.00", "0.00"
    rows = account_repo.get_user_accounts(user_id)
    rmb, usd = "0.00", "0.00"
    for row in rows:
        try:
            at = int(row.get("accountType") or 0)
        except Exception:
            continue
        bal = row.get("availableBalance")
        try:
            text = format(Decimal(str(bal or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")
        except Exception:
            text = "0.00"
        if at == 1:
            rmb = text
        elif at == 2:
            usd = text
    return rmb, usd


def _fmt_time(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    text = str(value)
    return text[:19] if len(text) >= 19 else text


def list_recent_sys_logs(limit: int = 10) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            sl.id, sl.addTime, sl.content, sl.ip, sl.title, sl.type,
            sl.user_id AS userId,
            IFNULL(u.true_name, IFNULL(u.user_name, '')) AS userName
        FROM exp_syslog sl
        LEFT JOIN sy_users u ON CAST(sl.user_id AS CHAR) = CAST(u.id AS CHAR)
        ORDER BY sl.addTime DESC
        LIMIT %(limit)s
        """,
        {"limit": int(limit)},
    )
    return [
        {
            "id": r.get("id"),
            "addTime": _fmt_time(r.get("addTime")),
            "content": r.get("content") or "",
            "ip": r.get("ip") or "",
            "title": r.get("title") or "",
            "type": r.get("type"),
            "userId": r.get("userId"),
            "userName": r.get("userName") or "",
        }
        for r in rows
    ]


def list_sys_logs_page(
    *,
    offset: int,
    limit: int,
    keyword: str = "",
    add_time: str = "",
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if keyword:
        where += " AND (u.user_name LIKE %(kw)s OR u.true_name LIKE %(kw)s OR sl.content LIKE %(kw)s)"
        params["kw"] = f"%{keyword}%"
    if add_time:
        where += " AND sl.addTime >= %(add_time)s"
        params["add_time"] = add_time
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM exp_syslog sl
            LEFT JOIN sy_users u ON CAST(sl.user_id AS CHAR) = CAST(u.id AS CHAR)
            {where}
            """,
            params,
        )
        or 0
    )
    params["offset"] = int(offset)
    params["limit"] = int(limit)
    rows = fetch_all(
        f"""
        SELECT
            sl.id, sl.addTime, sl.content, sl.ip, sl.title, sl.type,
            sl.user_id AS userId,
            IFNULL(u.true_name, IFNULL(u.user_name, '')) AS userName,
            u.user_name AS loginName
        FROM exp_syslog sl
        LEFT JOIN sy_users u ON CAST(sl.user_id AS CHAR) = CAST(u.id AS CHAR)
        {where}
        ORDER BY sl.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )
    out = []
    for r in rows:
        out.append(
            {
                "id": r.get("id"),
                "addTime": _fmt_time(r.get("addTime")),
                "content": r.get("content") or "",
                "ip": r.get("ip") or "",
                "title": r.get("title") or "",
                "type": r.get("type"),
                "userId": r.get("userId"),
                "userName": r.get("userName") or "",
                "loginName": r.get("loginName") or "",
            }
        )
    return out, total


def build_welcome_payload(user: dict[str, Any]) -> dict[str, Any]:
    user_id = str(user.get("user_id") or "")
    login_name = str(user.get("user_name") or "")
    utoo_type = user.get("utoo_type") or user.get("type")
    role_text = str(utoo_type) if utoo_type else ""
    user_type = _resolve_welcome_user_type(role_text)
    user_type2 = _resolve_welcome_user_type2(role_text, user_type)
    dept_name = staff_repo.find_dept_name(user.get("dept_id"))

    today = date.today()
    year = today.year
    six_months = previous_six_months(today=today)

    # 管理员近 6 月交易
    ydata: list[str] = []
    if user_type2 == 1:
        ydata = _chart_admin_trade(six_months)

    # 个人销售额（双币种，整年）
    sale = (
        _user_sale_by_year(user_id=user_id, year=year)
        if user_type2 == 2
        else {
            "year": str(year),
            "xmonths": [],
            "userSaleAryrmb": [],
            "userSaleAryus": [],
            "qnxsrmb": "0.00",
            "qnxsus": "0.00",
            "ddslrmb": 0,
            "ddslus": 0,
            "grmlzhbigdecimal": "0.00",
            "grmlllbigdecimal": "0.00",
        }
    )

    # 测试数量
    test_months = six_months
    test_ydata = _chart_user_test_count(test_months, user_id) if user_type2 == 3 else []

    account_rmb, account_us = _user_available_balances(user_id)
    show_assets = user_type in (0, 2, 3, 4, 6, 7, 14)
    show_logs = user_type == 1

    pending = _pending_for_sale_manager() if user_type == 3 else {
        "expOrder": 0,
        "selfChildOrder": 0,
        "subcontractOrder": 0,
        "subcontractSubOrder": 0,
        "materialSubOrder": 0,
    }
    # 销售主管 / 销售 / 测试相关 KPI
    show_ops = user_type in (3, 4) or user_type2 == 3
    ops = _ops_counts(user_id=user_id, user_type=user_type, user_type2=user_type2) if show_ops else {
        "notStarted": 0,
        "inProgress": 0,
        "passed": 0,
        "timeout": 0,
        "opsMode": "",
    }

    # 销售人员：测试数量(年) + 测试人员测试数量(月)
    is_salesperson = user_type == 4 and user_type2 == 2
    test_year_chart: dict[str, Any] = {"year": str(year), "months": [], "values": []}
    tester_month_chart: dict[str, Any] = {"month": "", "names": [], "values": []}
    if is_salesperson:
        test_year_chart = _test_qty_year_chart(year=year, sale_user_id=user_id)
        tester_month_chart = _tester_qty_month_chart(
            year=year, month=today.month, sale_user_id=user_id
        )

    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": login_name,
        "currentUser": login_name,
        "userType": user_type,
        "userType2": user_type2,
        "roleName": role_text,
        "deptName": dept_name or "",
        "email": user.get("email") or "",
        "mobilePhoneNumber": user.get("mobile_phone_number") or "",
        "menuCount": len(staff_repo.fetch_user_menus(user_id)),
        # admin trade (6 months)
        "xdate": six_months if user_type2 == 1 else [],
        "ydata": ydata,
        # dual-currency personal sale
        "saleYear": sale.get("year"),
        "xmonths": sale.get("xmonths") or [],
        "userSaleAryrmb": sale.get("userSaleAryrmb") or [],
        "userSaleAryus": sale.get("userSaleAryus") or [],
        "qnxsrmb": sale.get("qnxsrmb"),
        "qnxsus": sale.get("qnxsus"),
        "ddslrmb": sale.get("ddslrmb"),
        "ddslus": sale.get("ddslus"),
        "grmlzhbigdecimal": sale.get("grmlzhbigdecimal"),
        "grmlllbigdecimal": sale.get("grmlllbigdecimal"),
        # 测试人员本人测试数量
        "expmonth": test_months if user_type2 == 3 else [],
        "expTestAry": test_ydata,
        # 销售人员：测试数量年/月两图
        "showSaleTestCharts": is_salesperson,
        "testYearChart": test_year_chart,
        "testerMonthChart": tester_month_chart,
        # assets
        "showAssets": show_assets,
        "accountRMB": account_rmb,
        "accountUS": account_us,
        # KPIs
        "pendingCounts": pending,
        "opsCounts": ops,
        "showOpsCounts": show_ops,
        "newlogs": list_recent_sys_logs(10) if show_logs else [],
    }
