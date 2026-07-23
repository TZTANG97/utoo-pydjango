from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar

TEST_UTOO_TYPES = ("测试人员", "测试主管", "系统管理员")


def _fmt_dt(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _period_clause(
    *,
    order_status: int | None,
    period_type: str,
    year: str,
    month: str,
    week: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
    params: dict[str, Any],
) -> str:
    """对齐 Java selListByStatus / selOrderNum 的时间维度。

    order_status: 0/-1 → expect_finishtime；2 → end_time；其余默认 end_time。
    type: 1=周 2=月 3=季 5=自定义(跳过 year)。
    """
    if not period_type and not year and not start_date:
        return ""

    # 选时间列（对齐 Java selOrderNum：总单用 order_time）
    if order_status is None:
        col = "eo.order_time"
    elif order_status in (0, -1):
        col = "t.expect_finishtime"
    elif order_status == 2:
        col = "t.end_time"
    else:
        col = "t.end_time"

    # Java 前端年数据 type=4，MyBatis 无专门分支，等价于仅按 year 过滤
    if period_type in ("4", "0", "year"):
        period_type = ""

    clauses: list[str] = []
    if period_type == "1" and week:
        if order_status == 2:
            clauses.append("AND t.week = %(week)s")
        else:
            clauses.append(f"AND WEEKOFYEAR({col}) = %(week)s")
        params["week"] = int(week)
        if year and period_type != "5":
            clauses.append(f"AND DATE_FORMAT({col}, '%%Y') = %(year)s")
            params["year"] = year
    elif period_type == "2" and month:
        # month 可为 "07" 或 "7"
        mon = str(month).zfill(2)
        if year:
            params["ym"] = f"{year}-{mon}"
            clauses.append(f"AND DATE_FORMAT({col}, '%%Y-%%m') = %(ym)s")
        else:
            params["month"] = int(mon)
            clauses.append(f"AND MONTH({col}) = %(month)s")
    elif period_type == "3" and quarter:
        if order_status == 2:
            clauses.append("AND t.quarter = %(quarter)s")
        else:
            clauses.append(f"AND QUARTER({col}) = %(quarter)s")
        params["quarter"] = int(quarter)
        if year and period_type != "5":
            clauses.append(f"AND DATE_FORMAT({col}, '%%Y') = %(year)s")
            params["year"] = year
    elif period_type == "5":
        if start_date:
            clauses.append(f"AND {col} >= %(start_date)s")
            params["start_date"] = start_date if " " in start_date else f"{start_date} 00:00:00"
        if end_date:
            clauses.append(f"AND {col} <= %(end_date)s")
            params["end_date"] = end_date if " " in end_date else f"{end_date} 23:59:59"
    else:
        # 仅年，或 type 为空但有 year
        if year and period_type != "5":
            clauses.append(f"AND DATE_FORMAT({col}, '%%Y') = %(year)s")
            params["year"] = year
            if month and not period_type:
                mon = str(month).zfill(2)
                params["ym"] = f"{year}-{mon}"
                clauses.append(f"AND DATE_FORMAT({col}, '%%Y-%%m') = %(ym)s")

    return "\n".join(clauses)


def _base_filters(
    *,
    user_id: str = "",
    test_lab: str = "",
    order_status: int | None = None,
    is_timeout: int | None = None,
) -> tuple[str, dict[str, Any]]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if user_id:
        where += " AND t.test_user_id = %(user_id)s"
        params["user_id"] = user_id
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    if order_status is not None and order_status != -1:
        where += " AND t.order_status = %(order_status)s"
        params["order_status"] = order_status
    if is_timeout is not None:
        where += " AND t.is_timeout = %(is_timeout)s"
        params["is_timeout"] = is_timeout
    return where, params


def list_by_status(
    *,
    test_lab: str = "",
    user_id: str = "",
    order_status: int | None = None,
    is_timeout: int | None = None,
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    where, params = _base_filters(
        user_id=user_id,
        test_lab=test_lab,
        order_status=order_status,
        is_timeout=is_timeout,
    )
    where += "\n" + _period_clause(
        order_status=order_status,
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    order_by = "ORDER BY t.end_time DESC" if order_status == 2 else "ORDER BY t.expect_finishtime ASC"
    # 明细列表默认不截断（对齐 Java）；仅调用方显式传 limit 时才限制
    limit_sql = ""
    if limit is not None and limit > 0:
        params["limit"] = int(limit)
        limit_sql = "LIMIT %(limit)s"
    rows = fetch_all(
        f"""
        SELECT
            u.true_name AS user_name,
            t.order_id,
            t.timeout_days,
            eo.order_id AS orderNum,
            eo.order_time,
            ep.project_name,
            el.line_num,
            t.expect_finishtime,
            t.start_time,
            t.end_time,
            c.experiment_class_name,
            c.experiment_project_name
        FROM statistic_experiment_finish t
        LEFT JOIN sy_users u ON t.test_user_id = u.id
        LEFT JOIN experiment_order eo ON t.order_id = eo.id
        LEFT JOIN experiment_order_child c ON t.child_id = c.id
        LEFT JOIN experiment_line el ON c.line_id = el.id
        LEFT JOIN experiment_project ep ON t.test_type = ep.id
        {where}
        {order_by}
        {limit_sql}
        """,
        params,
    )
    for row in rows:
        row["expect_finishtime"] = _fmt_dt(row.get("expect_finishtime"))
        row["start_time"] = _fmt_dt(row.get("start_time"))
        row["end_time"] = _fmt_dt(row.get("end_time"))
        row["finish_time"] = row["end_time"]
        row["order_time"] = _fmt_dt(row.get("order_time"))
        if row.get("timeout_days") is None:
            row["timeout_days"] = ""
    return rows


def order_count(
    *,
    user_id: str = "",
    order_status: int | None = None,
    is_timeout: int | None = None,
    test_lab: str = "",
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> int:
    where, params = _base_filters(
        user_id=user_id,
        test_lab=test_lab,
        order_status=order_status,
        is_timeout=is_timeout,
    )
    where += "\n" + _period_clause(
        order_status=order_status,
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    return int(
        scalar(
            f"""
            SELECT COUNT(t.id)
            FROM statistic_experiment_finish t
            LEFT JOIN experiment_order eo ON t.order_id = eo.id
            {where}
            """,
            params,
        )
        or 0
    )


def dept_lab_ids(dept_id: str) -> list[int]:
    if not dept_id:
        return []
    row = fetch_one("SELECT lab_ids FROM sy_dept WHERE id = %(id)s", {"id": dept_id})
    if not row or not row.get("lab_ids"):
        return []
    ids: list[int] = []
    for part in str(row["lab_ids"]).split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


def list_experiment_lines(*, lab_ids: list[int] | None = None, user_id: str = "") -> list[dict[str, Any]]:
    where = "WHERE t.deleteStatus = 0 AND t.status = 1"
    params: dict[str, Any] = {}
    if lab_ids:
        placeholders = []
        for i, lid in enumerate(lab_ids):
            key = f"lab_{i}"
            placeholders.append(f"%({key})s")
            params[key] = lid
        where += f" AND t.lab_id IN ({', '.join(placeholders)})"
    if user_id:
        where += """
            AND t.id IN (
                SELECT c.line_id
                FROM statistic_experiment_finish sf
                LEFT JOIN experiment_order_child c ON sf.child_id = c.id
                WHERE sf.deleteStatus = 0 AND sf.test_user_id = %(user_id)s
                GROUP BY c.line_id
            )
        """
        params["user_id"] = user_id
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.line_num,
            t.line_status,
            t.run_num,
            lab.lab_name
        FROM experiment_line t
        LEFT JOIN experiment_lab lab ON t.lab_id = lab.id
        {where}
        ORDER BY t.line_status DESC, t.line_num ASC
        """,
        params,
    )
    for row in rows:
        status = row.get("line_status")
        if status in (1, "1"):
            row["lineStatusLabel"] = "进行中"
        else:
            row["lineStatusLabel"] = "未开始"
    return rows


def list_test_users(*, dept_id: str = "") -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "t0": TEST_UTOO_TYPES[0],
        "t1": TEST_UTOO_TYPES[1],
        "t2": TEST_UTOO_TYPES[2],
    }
    dept_clause = ""
    if dept_id and dept_id not in ("0", ""):
        dept_clause = "AND u.dept_id = %(dept_id)s"
        params["dept_id"] = dept_id
    return fetch_all(
        f"""
        SELECT
            u.id,
            u.user_name AS userName,
            u.true_name AS trueName,
            IFNULL(u.test_num, 0) AS test_num,
            u.dept_id AS deptId,
            sd.dept_name AS deptName
        FROM sy_users u
        LEFT JOIN sy_dept sd ON u.dept_id = sd.id
        WHERE u.id IN (
            SELECT DISTINCT t.id
            FROM sy_users t
            LEFT JOIN sy_user_expmanage sue ON t.id = sue.user_id
            WHERE t.pt_type LIKE '%%2%%'
              AND t.user_status = 1
              AND (
                    t.utoo_type IN (%(t0)s, %(t1)s, %(t2)s)
                    OR sue.exp_manage_id IS NOT NULL
              )
        )
        {dept_clause}
        ORDER BY u.register_time DESC
        """,
        params,
    )


def count_test_users(*, dept_id: str = "") -> int:
    params: dict[str, Any] = {
        "t0": TEST_UTOO_TYPES[0],
        "t1": TEST_UTOO_TYPES[1],
        "t2": TEST_UTOO_TYPES[2],
    }
    dept_clause = ""
    if dept_id and dept_id not in ("0", ""):
        dept_clause = "AND u.dept_id = %(dept_id)s"
        params["dept_id"] = dept_id
    return int(
        scalar(
            f"""
            SELECT COUNT(DISTINCT u.id)
            FROM sy_users u
            WHERE u.id IN (
                SELECT DISTINCT t.id
                FROM sy_users t
                LEFT JOIN sy_user_expmanage sue ON t.id = sue.user_id
                WHERE t.pt_type LIKE '%%2%%'
                  AND t.user_status = 1
                  AND (
                        t.utoo_type IN (%(t0)s, %(t1)s, %(t2)s)
                        OR sue.exp_manage_id IS NOT NULL
                  )
            )
            {dept_clause}
            """,
            params,
        )
        or 0
    )


def list_users_by_dept(*, dept_id: str = "") -> list[dict[str, Any]]:
    """筛选下拉：部门下测试平台人员。"""
    where = "WHERE t.pt_type LIKE '%%2%%' AND t.user_status = 1"
    params: dict[str, Any] = {}
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.dept_id = %(dept_id)s"
        params["dept_id"] = dept_id
    return fetch_all(
        f"""
        SELECT t.id, t.user_name AS userName, t.true_name AS trueName
        FROM sy_users t
        LEFT JOIN sy_user_type sut ON t.utoo_type = sut.type_name
        {where}
          AND (sut.type = 2 OR sut.type IS NULL)
        ORDER BY t.true_name ASC, t.user_name ASC
        """,
        params,
    )


def board1_monthly(*, year: str, month: str, dept_id: str = "") -> dict[str, Any]:
    """对齐 board1.ajax：本月完成量 Top + 最佳测试员 + 人数。"""
    mon = str(month).zfill(2)
    ymonth = f"{year}-{mon}"
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND DATE_FORMAT(t.end_time, '%%Y-%%m') = %(ymonth)s
    """
    params: dict[str, Any] = {"ymonth": ymonth}
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id

    rows = fetch_all(
        f"""
        SELECT
            t.test_user_id,
            su.true_name AS user_name,
            su.user_name AS account,
            sd.dept_name,
            COUNT(*) AS total_count,
            COUNT(
                CASE
                    WHEN t.is_timeout = 0
                     AND t.end_time IS NOT NULL
                     AND t.expect_finishtime IS NOT NULL
                     AND t.end_time <= t.expect_finishtime
                    THEN 1
                END
            ) AS no_timeout_count
        FROM statistic_experiment_finish t
        LEFT JOIN sy_dept sd ON t.test_lab = sd.id
        LEFT JOIN sy_users su ON t.test_user_id = su.id
        {where}
        GROUP BY t.test_user_id, su.true_name, su.user_name, sd.dept_name
        ORDER BY total_count DESC
        """,
        params,
    )

    sum_rate = 0.0
    for row in rows:
        total = int(row.get("total_count") or 0)
        no_to = int(row.get("no_timeout_count") or 0)
        zsl = (no_to * 100.0 / total) if total else 0.0
        row["zsl"] = round(zsl, 2)
        row["total_count"] = total
        row["no_timeout_count"] = no_to
        sum_rate += zsl

    avg_rate = round(sum_rate / len(rows), 2) if rows else 0.0
    sy_user_max = rows[0] if rows else None
    top3 = rows[:3]

    dept_name = "所有部门"
    if dept_id and dept_id not in ("0", ""):
        d = fetch_one("SELECT dept_name FROM sy_dept WHERE id = %(id)s", {"id": dept_id})
        if d and d.get("dept_name"):
            dept_name = d["dept_name"]

    return {
        "dept": dept_name,
        "syUsers": rows,
        "top3List": top3,
        "syUserMax": sy_user_max,
        "avgOnTimeRate": avg_rate,
        "syUsersNum": count_test_users(dept_id=dept_id),
    }


def monthly_finish_trend(*, dept_id: str = "", year: str) -> list[dict[str, Any]]:
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
    """
    params: dict[str, Any] = {"year": year}
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id
    return fetch_all(
        f"""
        SELECT DATE_FORMAT(t.end_time, '%%m') AS mon, COUNT(*) AS num
        FROM statistic_experiment_finish t
        {where}
        GROUP BY DATE_FORMAT(t.end_time, '%%Y-%%m')
        ORDER BY mon ASC
        """,
        params,
    )


def dashboard_overview(
    *,
    test_lab: str = "",
    user_id: str = "",
    period_type: str = "2",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict[str, Any]:
    """对齐 selDateOverviewByYear.ajax 核心返回。"""
    # 完成列表：按筛选时间
    ywc_list = list_by_status(
        test_lab=test_lab,
        user_id=user_id,
        order_status=2,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    # 进行中 / 未开始 / 超时：与 Java 一致，不做年月过滤（实时看板）
    jxz_list = list_by_status(test_lab=test_lab, user_id=user_id, order_status=1)
    nostart_list = list_by_status(test_lab=test_lab, user_id=user_id, order_status=0)
    wfp_list = list_by_status(
        test_lab=test_lab,
        user_id=user_id,
        order_status=-1,
        is_timeout=1,
    )
    # Java KPI「未开始订单」用 selOrderNum(..., status=0, type=5) 的 COUNT，不是 list.length
    wfpsl = order_count(
        user_id=user_id,
        order_status=0,
        test_lab=test_lab,
        period_type="5",
    )
    jxzsl = order_count(
        user_id=user_id,
        order_status=1,
        test_lab=test_lab,
        period_type="5",
    )
    cssl = order_count(
        user_id=user_id,
        order_status=-1,
        is_timeout=1,
        test_lab=test_lab,
        period_type="5",
    )

    lab_ids = dept_lab_ids(test_lab) if test_lab else None
    linelist = list_experiment_lines(lab_ids=lab_ids if lab_ids else None, user_id="")

    test_user_list = list_test_users(dept_id=test_lab)
    # 完成趋势：按 end_time 所在年/月，统计 order_status=2 的完成单量（全年 12 个月）
    trend = monthly_finish_trend(dept_id=test_lab, year=year or "")

    return {
        "wfpsl": wfpsl,
        "jxzsl": jxzsl,
        "ywcsl": len(ywc_list),
        "cssl": cssl,
        "nostartsl": wfpsl,
        "wfpList": wfp_list,
        "jxzList": jxz_list,
        "ywcList": ywc_list,
        "nostartList": nostart_list,
        "linelist": linelist,
        "testUserList": test_user_list,
        "selOrderList": ywc_list,
        "trend": trend,
    }


def _end_time_period_sql(
    *,
    period_type: str,
    year: str,
    month: str,
    week: str,
    quarter: str,
    start_date: str,
    end_date: str,
    params: dict[str, Any],
) -> str:
    """完成相关统计一律按 end_time（对齐 selTestType / selTestUserStats / selTestLong）。"""
    if period_type in ("4", "0", "year"):
        period_type = ""
    clauses: list[str] = []
    if period_type == "1" and week:
        clauses.append("AND t.week = %(week)s")
        params["week"] = int(week)
        if year:
            clauses.append("AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s")
            params["year"] = year
    elif period_type == "2" and month:
        mon = str(month).zfill(2)
        clauses.append("AND DATE_FORMAT(t.end_time, '%%m') = %(month)s")
        params["month"] = mon
        if year:
            clauses.append("AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s")
            params["year"] = year
    elif period_type == "3" and quarter:
        clauses.append("AND t.quarter = %(quarter)s")
        params["quarter"] = int(quarter)
        if year:
            clauses.append("AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s")
            params["year"] = year
    elif period_type == "5":
        if start_date:
            clauses.append("AND t.end_time >= %(start_date)s")
            params["start_date"] = start_date if " " in start_date else f"{start_date} 00:00:00"
        if end_date:
            clauses.append("AND t.end_time <= %(end_date)s")
            params["end_date"] = end_date if " " in end_date else f"{end_date} 23:59:59"
    elif year:
        clauses.append("AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s")
        params["year"] = year
    return "\n".join(clauses)


def order_count_ontime(
    *,
    user_id: str = "",
    test_lab: str = "",
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> int:
    """准时完成数：order_status=2 且 end_time <= expect_finishtime。"""
    where = "WHERE t.deleteStatus = 0 AND t.order_status = 2 AND t.end_time <= t.expect_finishtime"
    params: dict[str, Any] = {}
    if user_id:
        where += " AND t.test_user_id = %(user_id)s"
        params["user_id"] = user_id
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    where += "\n" + _end_time_period_sql(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    return int(scalar(f"SELECT COUNT(t.id) FROM statistic_experiment_finish t {where}", params) or 0)


def sum_test_minutes(
    *,
    user_id: str = "",
    test_lab: str = "",
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> float:
    where = "WHERE t.deleteStatus = 0 AND t.order_status = 2"
    params: dict[str, Any] = {}
    if user_id:
        where += " AND t.test_user_id = %(user_id)s"
        params["user_id"] = user_id
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    where += "\n" + _end_time_period_sql(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    val = scalar(f"SELECT SUM(IFNULL(t.test_time, 0)) FROM statistic_experiment_finish t {where}", params)
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def finish_trend_year(*, test_lab: str = "", year: str) -> list[dict[str, Any]]:
    """全年完成趋势（按月），对齐 selTestTrend(order_status=2, year)。"""
    return monthly_finish_trend(dept_id=test_lab, year=year)


def plan_count_for_ym(*, test_lab: str = "", ym: str) -> int:
    """对齐 selTestTrendPlan：status=0 且 end_time 落在指定 YYYY-MM。"""
    params: dict[str, Any] = {"ym": ym}
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 0
          AND DATE_FORMAT(t.end_time, '%%Y-%%m') = %(ym)s
    """
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    return int(scalar(f"SELECT COUNT(t.id) FROM statistic_experiment_finish t {where}", params) or 0)


def test_type_distribution(
    *,
    test_lab: str = "",
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> list[dict[str, Any]]:
    where = "WHERE t.deleteStatus = 0 AND t.order_status = 2"
    params: dict[str, Any] = {}
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    where += "\n" + _end_time_period_sql(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    return fetch_all(
        f"""
        SELECT tab.num, tab.test_type, ep.project_name
        FROM (
            SELECT COUNT(t.id) AS num, t.test_type
            FROM statistic_experiment_finish t
            {where}
            GROUP BY t.test_type
        ) tab
        LEFT JOIN experiment_project ep ON tab.test_type = ep.id
        ORDER BY tab.num DESC
        """,
        params,
    )


def test_user_finish_stats(
    *,
    test_lab: str = "",
    period_type: str = "",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
    ontime_only: bool = False,
) -> list[dict[str, Any]]:
    where = "WHERE t.deleteStatus = 0 AND t.order_status = 2"
    params: dict[str, Any] = {}
    if ontime_only:
        where += " AND t.end_time <= t.expect_finishtime"
    if test_lab and test_lab not in ("0", ""):
        where += " AND t.test_lab = %(test_lab)s"
        params["test_lab"] = test_lab
    where += "\n" + _end_time_period_sql(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        params=params,
    )
    return fetch_all(
        f"""
        SELECT tab.num, tab.test_user_id, u.true_name AS user_name
        FROM (
            SELECT COUNT(t.id) AS num, t.test_user_id
            FROM statistic_experiment_finish t
            {where}
            GROUP BY t.test_user_id
        ) tab
        LEFT JOIN sy_users u ON tab.test_user_id = u.id
        ORDER BY tab.num DESC
        """,
        params,
    )


def order_manage(
    *,
    test_lab: str = "",
    user_id: str = "",
    period_type: str = "2",
    year: str = "",
    week: str = "",
    month: str = "",
    quarter: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict[str, Any]:
    """对齐 Java selOrderManage.ajax。"""
    zongsl = order_count(
        user_id=user_id,
        order_status=None,
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    jxzsl = order_count(user_id=user_id, order_status=1, test_lab=test_lab, period_type="5")
    cssl = order_count(
        user_id=user_id,
        order_status=-1,
        is_timeout=1,
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    ywcsl = order_count(
        user_id=user_id,
        order_status=2,
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    zssl = order_count_ontime(
        user_id=user_id,
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    zsl = round(zssl * 100.0 / ywcsl, 2) if ywcsl else 0.0
    total_min = sum_test_minutes(
        user_id=user_id,
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    # Java: 先 /60 再 /ywcsl → 小时
    pjsc = round((total_min / 60.0) / ywcsl, 2) if ywcsl else 0.0

    xdate: list[str] = []
    wcvalues: list[int] = []
    jhvalues: list[int] = []
    trend_rows = finish_trend_year(test_lab=test_lab, year=year)
    for m in range(1, 13):
        ym = f"{year}-{str(m).zfill(2)}"
        xdate.append(ym)
        mon_key = str(m).zfill(2)
        num = 0
        for r in trend_rows:
            if str(r.get("mon")).zfill(2) == mon_key:
                num = int(r.get("num") or 0)
                break
        wcvalues.append(num)
        jhvalues.append(plan_count_for_ym(test_lab=test_lab, ym=ym))

    test_type_ary = test_type_distribution(
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    ywc_ary = test_user_finish_stats(
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        ontime_only=False,
    )
    zs_raw = test_user_finish_stats(
        test_lab=test_lab,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
        ontime_only=True,
    )
    zs_map = {str(r.get("test_user_id")): int(r.get("num") or 0) for r in zs_raw}
    test_user_zs_ary = []
    for row in ywc_ary:
        uid = str(row.get("test_user_id") or "")
        num = int(row.get("num") or 0)
        numzs = zs_map.get(uid, 0)
        rate = round(numzs * 100.0 / num, 2) if num else 0.0
        test_user_zs_ary.append({"name": row.get("user_name") or "", "value": rate})

    dept_name = "所有部门"
    if test_lab and test_lab not in ("0", ""):
        d = fetch_one("SELECT dept_name FROM sy_dept WHERE id = %(id)s", {"id": test_lab})
        if d and d.get("dept_name"):
            dept_name = d["dept_name"]

    return {
        "zongsl": zongsl,
        "jxzsl": jxzsl,
        "cssl": cssl,
        "ywcsl": ywcsl,
        "zsl": zsl,
        "pjsc": pjsc,
        "xdate": xdate,
        "wcvalues": wcvalues,
        "jhvalues": jhvalues,
        "testTypeAry": test_type_ary,
        "testUserYwcAry": ywc_ary,
        "testUserZsAry": test_user_zs_ary,
        "dept": dept_name,
    }


def annual_tester_monthly(*, year: str, dept_id: str = "") -> list[dict[str, Any]]:
    """对齐 board.ajax / selListByParam2：每人每年 12 个月完成量。"""
    params: dict[str, Any] = {
        "year": year,
        "t0": TEST_UTOO_TYPES[0],
        "t1": TEST_UTOO_TYPES[1],
        "t2": TEST_UTOO_TYPES[2],
    }
    dept_clause = ""
    lab_clause = ""
    if dept_id and dept_id not in ("0", ""):
        dept_clause = "AND u.dept_id = %(dept_id)s"
        lab_clause = "AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id

    month_union = " UNION ALL ".join(
        [f"SELECT CONCAT(%(year)s, '-{str(i).zfill(2)}') AS stat_month" for i in range(1, 13)]
    )

    return fetch_all(
        f"""
        SELECT
            tt.test_user_id,
            tt.user_name,
            tt.dept_name,
            sm.stat_month,
            IFNULL(ts.test_count, 0) AS total_count
        FROM (
            SELECT DISTINCT
                u.id AS test_user_id,
                u.true_name AS user_name,
                sd.dept_name AS dept_name
            FROM sy_users u
            LEFT JOIN sy_dept sd ON u.dept_id = sd.id
            WHERE u.id IN (
                SELECT DISTINCT t.id
                FROM sy_users t
                LEFT JOIN sy_user_expmanage sue ON t.id = sue.user_id
                WHERE t.pt_type LIKE '%%2%%'
                  AND t.user_status = 1
                  AND (
                        t.utoo_type IN (%(t0)s, %(t1)s, %(t2)s)
                        OR sue.exp_manage_id IS NOT NULL
                  )
            )
            {dept_clause}
        ) AS tt
        CROSS JOIN (
            {month_union}
        ) AS sm
        LEFT JOIN (
            SELECT
                t.test_user_id,
                DATE_FORMAT(t.end_time, '%%Y-%%m') AS stat_month,
                COUNT(*) AS test_count
            FROM statistic_experiment_finish t
            WHERE t.deleteStatus = 0
              AND t.test_user_id IS NOT NULL
              AND t.order_status = 2
              AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
              {lab_clause}
            GROUP BY t.test_user_id, DATE_FORMAT(t.end_time, '%%Y-%%m')
        ) AS ts ON tt.test_user_id = ts.test_user_id AND sm.stat_month = ts.stat_month
        ORDER BY tt.test_user_id, sm.stat_month
        """,
        params,
    )


# ---- 兼容旧 overview.ajax ----

def overview(*, dept_id: str = "", year: str = "") -> dict[str, Any]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if year:
        where += " AND DATE_FORMAT(COALESCE(t.end_time, t.expect_finishtime), '%%Y') = %(year)s"
        params["year"] = year
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id

    finished = int(scalar(f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 2", params) or 0)
    doing = int(scalar(f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 1", params) or 0)
    waiting = int(scalar(f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 0", params) or 0)
    timeout = int(scalar(f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.is_timeout = 1", params) or 0)
    ontime = int(
        scalar(
            f"""
            SELECT COUNT(*) FROM statistic_experiment_finish t
            {where}
              AND t.order_status = 2
              AND t.end_time IS NOT NULL
              AND t.expect_finishtime IS NOT NULL
              AND t.end_time <= t.expect_finishtime
            """,
            params,
        )
        or 0
    )
    ontime_rate = round(ontime * 100.0 / finished, 2) if finished else 0
    return {
        "finished": finished,
        "doing": doing,
        "waiting": waiting,
        "timeout": timeout,
        "ontime": ontime,
        "ontimeRate": ontime_rate,
    }


def tester_workload(*, dept_id: str = "", year: str) -> list[dict[str, Any]]:
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
    """
    params: dict[str, Any] = {"year": year}
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id
    return fetch_all(
        f"""
        SELECT
            u.true_name AS trueName,
            COUNT(*) AS finishNum,
            SUM(IFNULL(c.reference_price, 0)) AS amount
        FROM statistic_experiment_finish t
        LEFT JOIN sy_users u ON u.id = t.test_user_id
        LEFT JOIN experiment_order_child c ON c.id = t.child_id
        {where}
        GROUP BY t.test_user_id, u.true_name
        ORDER BY finishNum DESC
        LIMIT 50
        """,
        params,
    )


def recent_finished(*, dept_id: str = "", limit: int = 20) -> list[dict[str, Any]]:
    where = "WHERE t.deleteStatus = 0 AND t.order_status = 2"
    params: dict[str, Any] = {"limit": limit}
    if dept_id and dept_id not in ("0", ""):
        where += " AND t.test_lab = %(dept_id)s"
        params["dept_id"] = dept_id
    return fetch_all(
        f"""
        SELECT
            t.id,
            eo.order_id AS orderId,
            u.true_name AS trueName,
            t.end_time AS endTime,
            t.expect_finishtime AS expectFinishTime,
            t.is_timeout AS isTimeout,
            IFNULL(c.reference_price, 0) AS amount
        FROM statistic_experiment_finish t
        LEFT JOIN experiment_order eo ON eo.id = t.order_id
        LEFT JOIN experiment_order_child c ON c.id = t.child_id
        LEFT JOIN sy_users u ON u.id = t.test_user_id
        {where}
        ORDER BY t.end_time DESC
        LIMIT %(limit)s
        """,
        params,
    )
