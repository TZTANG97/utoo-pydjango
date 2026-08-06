from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_fund.repositories import account as account_repo
from apps.core.db_utils import fetch_all, scalar


def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java IndexViewController.indexHtml（welcome.htm）的 userType。

    Java 用 compareRole 比「一级权限 roleName」，不是精确 type 名：
    - 制单员 / 公司基金 / 仓库管理 / 外部投资 / 销售人员… 的 roleName 均为「A类销售人员」
      → 在 A_SALESPERSON 分支命中 → userType=4（后续 5/6/7 分支实际不可达）
    - 仅「公司账号」→ 2（公司基金不是公司账号）
    - 公共账号 / 外部合作公司 / 外部公司 → 0（空白欢迎页，无图表）
    """
    role = (utoo_type or "").strip()
    if not role:
        return 0
    upper = role.upper()

    # 1 系统管理员
    if role == "系统管理员" or "系统管理员" in role or upper == "ADMIN" or role == "admin":
        return 1

    # 2 仅公司账号（不可把「公司基金」算进来）
    if role == "公司账号" or role == "公司" or upper == "COMPANY":
        return 2

    # 3 销售主管 / 测试主管（TEST_MANAGER.roleName=销售主管）
    if (
        role in ("销售主管", "测试主管")
        or "销售主管" in role
        or "测试主管" in role
        or upper in ("SALE_MANAGER", "TEST_MANAGER")
    ):
        return 3

    # 4 A类销售人员族 + C/R 类 + 测试人员
    # 含：销售人员、制单员、公司基金、仓库管理、外部投资、原厂、内勤、C类、R类…
    a_sale_exact = {
        "销售人员",
        "制单员",
        "公司基金",
        "仓库管理",
        "外部投资",
        "原厂销售人员",
        "内勤主管",
        "A类销售人员",
        "测试人员",
    }
    if role in a_sale_exact:
        return 4
    if any(
        key in role
        for key in (
            "制单",
            "公司基金",
            "仓库",
            "外部投资",
            "原厂",
            "内勤",
            "C类",
            "R类",
            "A类销售",
        )
    ):
        return 4
    if role == "测试人员" or (
        "测试人员" in role and "测试主管" not in role
    ) or upper == "TEST_USER":
        return 4
    # 泛匹配「销售人员」类（已排除销售主管）
    if "销售" in role and "销售主管" not in role:
        return 4

    # 14 H类用户
    if "H类" in role or role.startswith("H类") or upper.startswith("H_"):
        return 14

    # 0 公共账号 / 外部合作公司 / 外部公司 等
    return 0


def _resolve_welcome_user_type2(utoo_type: str | None, user_type: int) -> int:
    """对齐 Java IndexViewController userType2（精确名称判断）。

    1=管理员交易图；3=测试人员测试数量；4=销售人员测试年/月图；5=测试主管测试数量。
    C类/原厂/R类/制单员/公司基金等 → 0（无额外图表，仅资产+运营卡）。
    """
    role = (utoo_type or "").strip()
    upper = role.upper()
    if "测试主管" in role or upper == "TEST_MANAGER":
        return 5
    if role == "测试人员" or (
        "测试人员" in role and "测试主管" not in role
    ) or upper == "TEST_USER":
        return 3
    # Java：仅 utoo_type 精确等于「销售人员」
    if role == "销售人员" or upper in ("A_SALESPERSON",):
        return 4
    if user_type == 1:
        return 1
    return 0


def _resolve_welcome_user_type3(utoo_type: str | None) -> int:
    """对齐 Java userType3：2=显示「我的实际/实验销售额」。

    仅 type 为「销售人员」或「销售主管」；C类销售人员等为 0。
    """
    role = (utoo_type or "").strip()
    if role in ("销售人员", "销售主管"):
        return 2
    return 0


def _is_test_manager(utoo_type: str | None) -> bool:
    role = (utoo_type or "").strip()
    return "测试主管" in role or role.upper() == "TEST_MANAGER"


def _is_sale_manager_exact(utoo_type: str | None) -> bool:
    """Java：仅 utoo_type 精确为「销售主管」走 selOrderNumBySaleManager。"""
    return (utoo_type or "").strip() == "销售主管"


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


def _count_audit_by_manager(
    *,
    order_type: str | int,
    manager_id: str,
    manager_field: str = "sale_manager",
) -> int:
    """对齐 Java getAuditOrders / getAuditOrders1128：order_status=20 + 主管字段。"""
    if not manager_id:
        return 0
    if manager_field not in ("sale_manager", "test_manager"):
        manager_field = "sale_manager"
    return int(
        scalar(
            f"""
            SELECT COUNT(*) FROM experiment_order
            WHERE CAST(order_type AS CHAR) = CAST(%(ot)s AS CHAR)
              AND order_status = 20
              AND CAST({manager_field} AS CHAR) = CAST(%(uid)s AS CHAR)
            """,
            {"ot": str(order_type), "uid": manager_id},
        )
        or 0
    )


def _count_pay_audit(*, manager_id: str, order_type: str | int = 9) -> int:
    """对齐 Java getAuditPayOrders：pay_status=32。"""
    if not manager_id:
        return 0
    return int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order
            WHERE CAST(order_type AS CHAR) = CAST(%(ot)s AS CHAR)
              AND CAST(pay_status AS CHAR) = '32'
              AND CAST(sale_manager AS CHAR) = CAST(%(uid)s AS CHAR)
            """,
            {"ot": str(order_type), "uid": manager_id},
        )
        or 0
    )


def _pending_for_manager(*, user_id: str, is_test_manager: bool) -> dict[str, Any]:
    """对齐 Java welcome.html userType=3 五张待审卡。

    1/2/3/5：sale_manager；4：测试主管用 test_manager，销售主管用 sale_manager。
    """
    type9_field = "test_manager" if is_test_manager else "sale_manager"
    return {
        "expOrder": _count_audit_by_manager(order_type=6, manager_id=user_id),
        "selfChildOrder": _count_audit_by_manager(order_type=10, manager_id=user_id),
        "subcontractOrder": _count_audit_by_manager(order_type=8, manager_id=user_id),
        "subcontractSubOrder": _count_audit_by_manager(
            order_type=9, manager_id=user_id, manager_field=type9_field
        ),
        # 字段名兼容前端：实际为「待审核付款实验分包子订单」
        "materialSubOrder": _count_pay_audit(manager_id=user_id, order_type=9),
    }


def _count_timeout_ops(
    *,
    user_id: str,
    order_status: int | None = None,
    is_timeout: int | None = None,
    by_sale_manager: bool = False,
) -> int:
    """对齐 Java selOrderNum / selOrderNumBySaleManager（statistic_experiment_timeout）。"""
    if not user_id:
        return 0
    params: dict[str, Any] = {"uid": user_id}
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0"
    if by_sale_manager:
        where += " AND CAST(t.audit_manager_id AS CHAR) = CAST(%(uid)s AS CHAR)"
    else:
        where += """
          AND (
            CAST(t.test_user_id AS CHAR) = CAST(%(uid)s AS CHAR)
            OR CAST(t.sale_user_id AS CHAR) = CAST(%(uid)s AS CHAR)
            OR CAST(t.audit_manager_id AS CHAR) = CAST(%(uid)s AS CHAR)
            OR CAST(t.lab_manager_id AS CHAR) = CAST(%(uid)s AS CHAR)
          )
        """
    if order_status is not None:
        where += " AND t.order_status = %(st)s"
        params["st"] = int(order_status)
    if is_timeout is not None:
        where += " AND t.is_timeout = %(to)s"
        params["to"] = int(is_timeout)
    try:
        return int(
            scalar(
                f"SELECT COUNT(t.id) FROM statistic_experiment_timeout t {where}",
                params,
            )
            or 0
        )
    except Exception:
        return 0


def _ops_counts(
    *,
    user_id: str,
    user_type: int,
    user_type2: int,
    utoo_type: str = "",
) -> dict[str, int]:
    """运营 KPI（对齐 Java welcome.htm / IndexViewController）。

    文案统一：未开始测试订单 / 进行中测试订单 / 测试超时订单。
    - 销售主管：statistic_experiment_timeout + audit_manager_id
    - 测试人员及其他：同表 selOrderNum（test/sale/audit/lab_manager 命中本人）
    注意：Java 测试人员第三卡也是「测试超时」，不是「测试通过/已完成」。
    """
    del user_type, user_type2  # 欢迎页运营卡不区分 finish 通过态
    by_sm = _is_sale_manager_exact(utoo_type)
    return {
        "notStarted": _count_timeout_ops(
            user_id=user_id, order_status=0, by_sale_manager=by_sm
        ),
        "inProgress": _count_timeout_ops(
            user_id=user_id, order_status=1, by_sale_manager=by_sm
        ),
        "passed": 0,
        "timeout": _count_timeout_ops(
            user_id=user_id, is_timeout=1, by_sale_manager=by_sm
        ),
        "opsMode": "manager",
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
        "saleUserId": str(sale_user_id or ""),
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
            t.test_user_id AS userId,
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
        "userIds": [str(r.get("userId") or "") for r in rows],
        "saleUserId": str(sale_user_id or ""),
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


def _chart_user_test_count(months: list[str], user_id: str, *, year: int) -> list[str]:
    """对齐 Java statisticTestNumMonthService.selListGroupByMonth。

    优先 statistic_test_num_month_utoo；表不存在时回退子单计数。
    """
    if not months or not user_id:
        return ["0"] * len(months)
    try:
        rows = fetch_all(
            """
            SELECT t.month AS ym, SUM(IFNULL(t.order_count, 0)) AS cnt
            FROM statistic_test_num_month_utoo t
            WHERE CAST(t.test_user_id AS CHAR) = CAST(%(user_id)s AS CHAR)
              AND CAST(t.year AS CHAR) = CAST(%(year)s AS CHAR)
            GROUP BY t.month
            ORDER BY t.month
            """,
            {"user_id": user_id, "year": str(year)},
        )
        by_month: dict[str, Any] = {}
        for r in rows:
            ym = str(r.get("ym") or "")
            if ym and len(ym) == 7:
                by_month[ym] = r.get("cnt")
            elif ym:
                # 表里 month 可能是 yyyy-MM 或 MM
                by_month[f"{year:04d}-{ym.zfill(2)}"] = r.get("cnt")
        if by_month or rows is not None:
            return _fill_months(months, by_month, as_wan=False)
    except Exception:
        pass

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


def _helper_user_ids(user_id: str) -> list[str]:
    """对齐 Java queryUsersByHelper：本人 + helper_id=本人。"""
    ids = [str(user_id)]
    if not user_id:
        return ids
    rows = fetch_all(
        """
        SELECT id FROM sy_users
        WHERE CAST(helper_id AS CHAR) = CAST(%(uid)s AS CHAR)
        """,
        {"uid": user_id},
    )
    for r in rows:
        hid = str(r.get("id") or "")
        if hid and hid not in ids:
            ids.append(hid)
    return ids


def _us_exchange_rate() -> Decimal:
    try:
        val = scalar("SELECT us_exchange_rate FROM account_setting LIMIT 1", {})
        return Decimal(str(val or 1)) or Decimal("1")
    except Exception:
        return Decimal("1")


def _user_has_company_account(user_id: str) -> bool:
    if not user_id:
        return False
    try:
        return bool(
            scalar(
                """
                SELECT u.id FROM `user` u
                WHERE CAST(u.syuser_id AS CHAR) = CAST(%(uid)s AS CHAR)
                  AND IFNULL(u.deleteStatus, 0) = 0
                LIMIT 1
                """,
                {"uid": user_id},
            )
        )
    except Exception:
        return False


def _subcontract_gross_profit(*, user_id: str, year: int | None = None) -> tuple[str, str]:
    """对齐 Java welcome：毛利 = 分包订单总额 − 分包子订单总额（美元按汇率折 RMB）。"""
    if not user_id:
        return "0.00", "0.00"
    fx = _us_exchange_rate()
    year_sql_t = ""
    year_sql_t2 = ""
    params: dict[str, Any] = {"uid": user_id}
    if year:
        year_sql_t = " AND DATE_FORMAT(t.order_time,'%%Y') = %(year)s"
        year_sql_t2 = " AND DATE_FORMAT(t2.order_time,'%%Y') = %(year)s"
        params["year"] = str(year)

    if _user_has_company_account(user_id):
        sale_filter = """
          AND t.supplier_name IN (
            SELECT id FROM `user` WHERE CAST(syuser_id AS CHAR) = CAST(%(uid)s AS CHAR)
          )
        """
        parent_sale_filter = """
          AND t2.supplier_name IN (
            SELECT id FROM `user` WHERE CAST(syuser_id AS CHAR) = CAST(%(uid)s AS CHAR)
          )
        """
    else:
        sale_filter = """
          AND (
            CAST(t.sale_user AS CHAR) = CAST(%(uid)s AS CHAR)
            OR t.sale_user IN (
              SELECT id FROM sy_users WHERE CAST(helper_id AS CHAR) = CAST(%(uid)s AS CHAR)
            )
          )
        """
        parent_sale_filter = """
          AND (
            CAST(t2.sale_user AS CHAR) = CAST(%(uid)s AS CHAR)
            OR t2.sale_user IN (
              SELECT id FROM sy_users WHERE CAST(helper_id AS CHAR) = CAST(%(uid)s AS CHAR)
            )
          )
        """

    try:
        parent_rows = fetch_all(
            f"""
            SELECT IFNULL(SUM(t.totalPrice), 0) AS amt, IFNULL(t.currency_type, 1) AS ct
            FROM experiment_order t
            WHERE t.order_status >= 30 AND CAST(t.order_type AS CHAR) = '8'
              {year_sql_t}
              {sale_filter}
            GROUP BY IFNULL(t.currency_type, 1)
            """,
            params,
        )
        child_rows = fetch_all(
            f"""
            SELECT IFNULL(SUM(t.totalPrice), 0) AS amt, IFNULL(t.currency_type, 1) AS ct
            FROM experiment_order t
            WHERE t.order_status > 0 AND CAST(t.order_type AS CHAR) = '9'
              AND t.parent_id IN (
                SELECT t2.id FROM experiment_order t2
                WHERE t2.order_status >= 30 AND CAST(t2.order_type AS CHAR) = '8'
                  {year_sql_t2}
                  {parent_sale_filter}
              )
            GROUP BY IFNULL(t.currency_type, 1)
            """,
            params,
        )
    except Exception:
        return "0.00", "0.00"

    def to_rmb(rows: list[dict[str, Any]]) -> Decimal:
        total = Decimal("0")
        for r in rows:
            try:
                amt = Decimal(str(r.get("amt") or 0))
            except Exception:
                amt = Decimal("0")
            try:
                ct = int(r.get("ct") or 1)
            except Exception:
                ct = 1
            if ct == 2:
                total += (amt * fx).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                total += amt
        return total

    parent_rmb = to_rmb(parent_rows)
    child_rmb = to_rmb(child_rows)
    profit = parent_rmb - child_rmb
    rate = Decimal("0")
    if profit != 0 and parent_rmb != 0:
        rate = (profit / parent_rmb * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return (
        format(profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        format(rate, "f"),
    )


def _user_sale_by_year(
    *,
    user_id: str,
    year: int,
    order_type_filter: str = "",
) -> dict[str, Any]:
    """对齐 Java selUserSaleByYear：读 statistic_user_sale_exp / _sm。

    order_type_filter: ''=全部(1+2)，'1'=实验，'2'=实验分包（统计表 order_type）。
    """
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

    use_sm = False
    urow = fetch_all(
        "SELECT utoo_type AS ut FROM sy_users WHERE CAST(id AS CHAR)=CAST(%(id)s AS CHAR) LIMIT 1",
        {"id": user_id},
    )
    utoo = str((urow[0].get("ut") if urow else "") or "")
    use_sm = _is_sale_manager_exact(utoo)
    table = "statistic_user_sale_exp_sm" if use_sm else "statistic_user_sale_exp"
    try:
        fetch_all(f"SELECT 1 AS ok FROM {table} LIMIT 1")
    except Exception:
        grml, grml_rate = _subcontract_gross_profit(user_id=user_id, year=year)
        empty["grmlzhbigdecimal"] = grml
        empty["grmlllbigdecimal"] = grml_rate
        return empty

    uids = [str(user_id)] if use_sm else _helper_user_ids(user_id)
    placeholders = ", ".join(f"%(u{i})s" for i in range(len(uids)))
    params: dict[str, Any] = {f"u{i}": u for i, u in enumerate(uids)}
    params["year"] = str(year)

    type_sql = ""
    if order_type_filter == "1":
        type_sql = "AND t.order_type = 1"
    elif order_type_filter == "2":
        type_sql = "AND t.order_type = 2"
    else:
        type_sql = "AND t.order_type IN (1, 2)"

    try:
        rows = fetch_all(
            f"""
            SELECT
                SUM(IFNULL(t.sale_amount, 0)) AS sumtotal,
                SUM(IFNULL(t.order_count, 0)) AS sumordercount,
                t.account_type AS account_type,
                t.`month` AS m
            FROM {table} t
            WHERE t.type = 0
              AND CAST(t.user_id AS CHAR) IN ({placeholders})
              AND LEFT(t.`month`, 4) = %(year)s
              {type_sql}
            GROUP BY t.account_type, t.`month`
            ORDER BY t.`month`
            """,
            params,
        )
    except Exception:
        rows = []

    rmb_by: dict[str, Decimal] = {m: Decimal("0") for m in months}
    usd_by: dict[str, Decimal] = {m: Decimal("0") for m in months}
    cnt_rmb = 0
    cnt_usd = 0
    for r in rows:
        m = str(r.get("m") or "")
        if m not in rmb_by:
            rmb_by[m] = Decimal("0")
            usd_by[m] = Decimal("0")
            months.append(m)
        try:
            at = int(r.get("account_type") or 1)
        except Exception:
            at = 1
        try:
            price = Decimal(str(r.get("sumtotal") or 0))
        except Exception:
            price = Decimal("0")
        try:
            cnt = int(r.get("sumordercount") or 0)
        except Exception:
            cnt = 0
        if at == 2:
            usd_by[m] = usd_by.get(m, Decimal("0")) + price
            cnt_usd += cnt
        else:
            rmb_by[m] = rmb_by.get(m, Decimal("0")) + price
            cnt_rmb += cnt

    months = sorted(set(months))

    def series(src: dict[str, Decimal]) -> list[str]:
        out: list[str] = []
        for m in months:
            v = src.get(m, Decimal("0"))
            out.append(format(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"))
        return out

    rmb_s = series(rmb_by)
    usd_s = series(usd_by)
    sum_rmb = sum((Decimal(x) for x in rmb_s), Decimal("0"))
    sum_usd = sum((Decimal(x) for x in usd_s), Decimal("0"))
    grml, grml_rate = _subcontract_gross_profit(user_id=user_id, year=year)
    return {
        "year": str(year),
        "xmonths": months,
        "userSaleAryrmb": rmb_s,
        "userSaleAryus": usd_s,
        "qnxsrmb": format(sum_rmb.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "qnxsus": format(sum_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "ddslrmb": cnt_rmb,
        "ddslus": cnt_usd,
        "grmlzhbigdecimal": grml,
        "grmlllbigdecimal": grml_rate,
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


def build_welcome_payload(
    user: dict[str, Any],
    *,
    chart_year: int | None = None,
    order_type_filter: str = "",
) -> dict[str, Any]:
    user_id = str(user.get("user_id") or "")
    login_name = str(user.get("user_name") or "")
    utoo_type = user.get("utoo_type") or user.get("type")
    role_text = str(utoo_type) if utoo_type else ""
    user_type = _resolve_welcome_user_type(role_text)
    user_type2 = _resolve_welcome_user_type2(role_text, user_type)
    user_type3 = _resolve_welcome_user_type3(role_text)
    is_test_mgr = _is_test_manager(role_text)
    dept_name = staff_repo.find_dept_name(user.get("dept_id"))

    today = date.today()
    year = today.year
    six_months = previous_six_months(today=today)
    try:
        cy = int(chart_year) if chart_year else year
    except (TypeError, ValueError):
        cy = year
    if cy < 2000 or cy > year + 1:
        cy = year
    ot_filter = str(order_type_filter or "").strip()
    if ot_filter not in ("", "1", "2"):
        ot_filter = ""

    # 管理员近 6 月交易
    ydata: list[str] = []
    if user_type2 == 1:
        ydata = _chart_admin_trade(six_months)

    # 个人销售额：Java userType3==2（销售主管 / 销售人员；C类无此图）
    sale = (
        _user_sale_by_year(user_id=user_id, year=cy, order_type_filter=ot_filter)
        if user_type3 == 2
        else {
            "year": str(cy),
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

    # 测试人员(ut2=3) / 测试主管(ut2=5)：我的测试数量
    show_test_chart = user_type2 in (3, 5)
    test_months = _months_of_year(cy, today=today) if show_test_chart else []
    test_ydata = (
        _chart_user_test_count(test_months, user_id, year=cy) if show_test_chart else []
    )

    account_rmb, account_us = _user_available_balances(user_id)
    # Java welcome.html：资产饼图 DOM 在 userType 2/3/4/7/14（及不可达的 6）；
    # userType=0（公共账号/外部合作）为空白页，不得展示图表。
    show_assets = user_type in (2, 3, 4, 6, 7, 14)
    show_logs = user_type == 1

    pending = (
        _pending_for_manager(user_id=user_id, is_test_manager=is_test_mgr)
        if user_type == 3
        else {
            "expOrder": 0,
            "selfChildOrder": 0,
            "subcontractOrder": 0,
            "subcontractSubOrder": 0,
            "materialSubOrder": 0,
        }
    )
    # Java：userType 3/4/5/6/7 均展示未开始/进行中/超时
    show_ops = user_type in (3, 4, 5, 6, 7) or user_type2 in (3, 5)
    ops = (
        _ops_counts(
            user_id=user_id,
            user_type=user_type,
            user_type2=user_type2,
            utoo_type=role_text,
        )
        if show_ops
        else {
            "notStarted": 0,
            "inProgress": 0,
            "passed": 0,
            "timeout": 0,
            "opsMode": "",
        }
    )

    # Java userType2==4（销售人员）：测试数量(年) + 测试人员测试数量(月)
    is_a_salesperson = user_type2 == 4
    test_year_chart: dict[str, Any] = {"year": str(year), "months": [], "values": []}
    tester_month_chart: dict[str, Any] = {"month": "", "names": [], "values": []}
    if is_a_salesperson:
        test_year_chart = _test_qty_year_chart(year=year, sale_user_id=user_id)
        tester_month_chart = _tester_qty_month_chart(
            year=year, month=today.month, sale_user_id=user_id
        )

    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": login_name,
        "currentUser": login_name,
        "currentUserId": user_id,
        "userType": user_type,
        "userType2": user_type2,
        "userType3": user_type3,
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
        # 测试人员 / 测试主管：本人测试数量
        "expmonth": test_months if show_test_chart else [],
        "expTestAry": test_ydata,
        "testChartYear": str(cy) if show_test_chart else "",
        # 销售人员：测试数量年/月两图
        "showSaleTestCharts": is_a_salesperson,
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
