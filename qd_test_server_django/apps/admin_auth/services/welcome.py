from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_fund.repositories import account as account_repo
from apps.core.db_utils import fetch_all, scalar


def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java IndexViewController.indexHtml（welcome.htm）的 userType。

    1 系统管理员 / 2 公司基金·公司账号 / 3 销售主管 / 4 销售人员·测试人员
    / 5 制单 / 6 外部投资 / 7 仓库 / 14 H类 / 0 其它（含测试主管）
    """
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
    # Java HTML：测试人员与销售人员同属 userType=4（图表靠 userType2 区分）
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
    # 测试主管等未单独枚举 → 0
    return 0


def _resolve_welcome_user_type2(utoo_type: str | None, user_type: int) -> int:
    """对齐 welcome：1=管理员交易图 2=销售额 3=测试数量 0=无个人业绩图。"""
    role = (utoo_type or "").strip()
    if role == "测试人员" or "测试人员" in role:
        return 3
    if user_type == 1:
        return 1
    if user_type in (3, 4, 14) or "销售" in role or "H类" in role:
        # userType=4 且已是测试人员时上面已返回 3
        if "测试" in role and "测试人员" not in role:
            # 测试主管等：无销售额图
            return 0
        return 2
    return 0


def previous_six_months(*, today: date | None = None) -> list[str]:
    """对齐 CommUtil.getPreviousMonth：含本月共 6 个 YYYY-MM。"""
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
        ORDER BY DATE_FORMAT(order_time, '%%Y-%%m')
        """,
        params,
    )
    by_month = {str(r.get("xdate") or ""): r.get("price") for r in rows}
    return _fill_months(months, by_month, as_wan=True)


def _chart_user_sale(months: list[str], user_id: str) -> list[str]:
    """个人实验销售额（万元），按 sale_user。"""
    if not months or not user_id:
        return ["0"] * len(months)
    placeholders = ", ".join(f"%(m{i})s" for i in range(len(months)))
    params: dict[str, Any] = {f"m{i}": m for i, m in enumerate(months)}
    params["user_id"] = user_id
    rows = fetch_all(
        f"""
        SELECT
            DATE_FORMAT(order_time, '%%Y-%%m') AS xdate,
            SUM(totalPrice) AS price
        FROM experiment_order
        WHERE order_type IN (6, 8)
          AND order_status >= 30
          AND CAST(sale_user AS CHAR) = CAST(%(user_id)s AS CHAR)
          AND DATE_FORMAT(order_time, '%%Y-%%m') IN ({placeholders})
        GROUP BY DATE_FORMAT(order_time, '%%Y-%%m')
        """,
        params,
    )
    by_month = {str(r.get("xdate") or ""): r.get("price") for r in rows}
    return _fill_months(months, by_month, as_wan=True)


def _chart_user_test_count(months: list[str], user_id: str) -> list[str]:
    """个人测试数量：子单 test_user_id 按月计数。"""
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


def _user_available_balances(user_id: str) -> tuple[str, str]:
    """account_type 1=人民币 2=美元（对齐 Java accountRMB / accountUS）。"""
    if not user_id:
        return "0", "0"
    rows = account_repo.get_user_accounts(user_id)
    rmb, usd = "0", "0"
    for row in rows:
        try:
            at = int(row.get("accountType") or 0)
        except Exception:
            continue
        bal = row.get("availableBalance")
        text = "0" if bal is None or bal == "" else str(bal)
        if at == 1:
            rmb = text
        elif at == 2:
            usd = text
    return rmb, usd


def _pending_audit_counts(user_id: str) -> dict[str, int]:
    """销售主管欢迎页待审核角标（order_status=20）。"""
    del user_id  # 主管看全量待审，与 Java 快捷入口一致
    exp = int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order
            WHERE order_type IN (6, 8) AND order_status = 20
            """
        )
        or 0
    )
    return {
        "expOrder": exp,
        "subcontractOrder": 0,
        "subcontractSubOrder": 0,
    }


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
            sl.id,
            sl.addTime,
            sl.content,
            sl.ip,
            sl.title,
            sl.type,
            sl.user_id AS userId,
            IFNULL(u.true_name, IFNULL(u.user_name, '')) AS userName
        FROM exp_syslog sl
        LEFT JOIN sy_users u ON CAST(sl.user_id AS CHAR) = CAST(u.id AS CHAR)
        ORDER BY sl.addTime DESC
        LIMIT %(limit)s
        """,
        {"limit": int(limit)},
    )
    out: list[dict[str, Any]] = []
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
            }
        )
    return out


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
            sl.id,
            sl.addTime,
            sl.content,
            sl.ip,
            sl.title,
            sl.type,
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
    out: list[dict[str, Any]] = []
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
    utoo_type = user.get("utoo_type") or user.get("type")
    role_text = str(utoo_type) if utoo_type else ""
    user_type = _resolve_welcome_user_type(role_text)
    user_type2 = _resolve_welcome_user_type2(role_text, user_type)
    dept_name = staff_repo.find_dept_name(user.get("dept_id"))
    xdate = previous_six_months()

    chart_kind = "none"
    chart_title = ""
    chart_unit = ""
    ydata: list[str] = []
    if user_type2 == 1:
        chart_kind = "admin_trade"
        chart_title = "最近 6 个月交易记录"
        chart_unit = "销售订单金额（万元）"
        ydata = _chart_admin_trade(xdate)
    elif user_type2 == 2:
        chart_kind = "user_sale"
        chart_title = "我的实验销售额"
        chart_unit = "销售额（万元）"
        ydata = _chart_user_sale(xdate, user_id)
    elif user_type2 == 3:
        chart_kind = "user_test"
        chart_title = "我的测试数量"
        chart_unit = "测试数量（单）"
        ydata = _chart_user_test_count(xdate, user_id)

    account_rmb, account_us = _user_available_balances(user_id)
    show_assets = user_type in (0, 2, 3, 4, 6, 7, 14)
    show_logs = user_type == 1

    pending = _pending_audit_counts(user_id) if user_type == 3 else {
        "expOrder": 0,
        "subcontractOrder": 0,
        "subcontractSubOrder": 0,
    }

    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": user.get("user_name") or "",
        "userType": user_type,
        "userType2": user_type2,
        "roleName": role_text,
        "deptName": dept_name or "",
        "email": user.get("email") or "",
        "mobilePhoneNumber": user.get("mobile_phone_number") or "",
        "menuCount": len(staff_repo.fetch_user_menus(user_id)),
        "xdate": xdate,
        "ydata": ydata,
        "chartKind": chart_kind,
        "chartTitle": chart_title,
        "chartUnit": chart_unit,
        "showAssets": show_assets,
        "accountRMB": account_rmb,
        "accountUS": account_us,
        "pendingCounts": pending,
        "newlogs": list_recent_sys_logs(10) if show_logs else [],
    }
