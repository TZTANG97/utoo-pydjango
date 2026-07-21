from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.core.db_utils import fetch_all, scalar


def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java IndexViewController.welcome.htm 的 userType 粗分。"""
    role = (utoo_type or "").strip()
    if not role:
        return 0
    if "系统管理员" in role or role.upper() == "ADMIN":
        return 1
    if "公司" in role:
        return 2
    if "销售主管" in role:
        return 3
    if "销售" in role or "原厂" in role:
        return 4
    if "制单" in role:
        return 5
    if "投资" in role:
        return 6
    if "仓库" in role:
        return 7
    if role.startswith("H") or "H类" in role:
        return 14
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


def _chart_y_datas(months: list[str]) -> list[str]:
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
    values: list[str] = []
    for m in months:
        raw = by_month.get(m)
        if raw is None or raw == "":
            values.append("0")
            continue
        try:
            v = (Decimal(str(raw)) / Decimal(10000)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            values.append(format(v, "f"))
        except Exception:
            values.append("0")
    return values


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
    user_type = _resolve_welcome_user_type(str(utoo_type) if utoo_type else None)
    dept_name = staff_repo.find_dept_name(user.get("dept_id"))
    xdate = previous_six_months()
    ydata = _chart_y_datas(xdate)
    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": user.get("user_name") or "",
        "userType": user_type,
        "roleName": user.get("type") or user.get("utoo_type") or "",
        "deptName": dept_name or "",
        "email": user.get("email") or "",
        "mobilePhoneNumber": user.get("mobile_phone_number") or "",
        "menuCount": len(staff_repo.fetch_user_menus(user_id)),
        "xdate": xdate,
        "ydata": ydata,
        "newlogs": list_recent_sys_logs(10),
    }
