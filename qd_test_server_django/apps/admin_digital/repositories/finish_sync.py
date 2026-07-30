"""对齐 Java OrderTimeoutTaskAction 统计刷表逻辑。

- integralEarnings2 → refresh_statistic_finish
- integralEarnings5 → refresh_line_run_num
- integralEarnings6 → refresh_user_test_num
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from apps.core.db_utils import execute, fetch_all, fetch_one, scalar

logger = logging.getLogger(__name__)

TEST_UTOO_TYPES = ("测试人员", "测试主管", "系统管理员")
BATCH_SIZE = 200


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None


def _as_date(value: Any) -> date | None:
    dt = _as_dt(value)
    return dt.date() if dt else None


def _week_of_year(dt: datetime) -> int:
    # 近似对齐 Java DateUtil.getWeekOfYear / Calendar.WEEK_OF_YEAR
    return int(dt.isocalendar()[1])


def _quarter_of_year(dt: datetime) -> int:
    return (dt.month - 1) // 3 + 1


def _minutes_diff(start: datetime, end: datetime) -> float:
    return max((end - start).total_seconds() / 60.0, 0.0)


def truncate_finish() -> None:
    """对齐 statisticExperimentFinishService.delAll → TRUNCATE。"""
    execute("TRUNCATE TABLE statistic_experiment_finish")


def list_source_children() -> list[dict[str, Any]]:
    """对齐 ExperimentOrderChildMapper#getAllOrderList。"""
    rows = fetch_all(
        """
        SELECT
            ocf.test_user_id AS test_user_id,
            ocf.order_status AS order_status,
            ocf.expect_finishtime AS expect_finishtime,
            t.id AS order_id,
            ocf.id AS child_id,
            us.dept_id AS test_lab,
            ocf.experiment_project_id AS test_type
        FROM experiment_order t
        LEFT JOIN experiment_order pof ON t.parent_id = pof.id
        LEFT JOIN exp_qd_purchase_order_child poc ON t.id = poc.purchase_order_id
        LEFT JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
        LEFT JOIN sy_users us ON ocf.test_user_id = us.id
        WHERE t.order_status > 0
          AND t.order_type IN (10)
          AND ocf.order_status > 0
          AND ocf.id IS NOT NULL
        """
    )
    return rows


def latest_experiment_log(child_id: Any) -> dict[str, Any] | None:
    """对齐 experimentLogService.orderchildList：按 addTime desc 取第一条。"""
    return fetch_one(
        """
        SELECT start_time, end_time, addTime
        FROM experiment_log
        WHERE order_child_id = %(cid)s
        ORDER BY addTime DESC
        LIMIT 1
        """,
        {"cid": child_id},
    )


def build_finish_row(child: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    status_raw = child.get("order_status")
    try:
        child_status = int(status_raw)
    except (TypeError, ValueError):
        child_status = 0

    expect = _as_dt(child.get("expect_finishtime"))
    is_timeout = 0
    timeout_days = None

    if child_status > 38:
        order_status = 2
    elif child_status == 38:
        order_status = 1
        if expect and now > expect:
            is_timeout = 1
            expect_d = _as_date(expect)
            if expect_d:
                timeout_days = (now.date() - expect_d).days + 1
    else:
        order_status = 0
        if expect and now > expect:
            is_timeout = 1
            expect_d = _as_date(expect)
            if expect_d:
                timeout_days = (now.date() - expect_d).days + 1

    start_time = None
    end_time = None
    test_time = None
    week = 0
    quarter = 0

    log = latest_experiment_log(child.get("child_id"))
    if log:
        start_time = _as_dt(log.get("start_time"))
        end_time = _as_dt(log.get("end_time"))
        if start_time and end_time:
            test_time = round(_minutes_diff(start_time, end_time), 2)
        if end_time:
            week = _week_of_year(end_time)
            quarter = _quarter_of_year(end_time)
        if expect and end_time is None and now > expect:
            is_timeout = 1

    return {
        "addTime": now,
        "deleteStatus": 0,
        "order_id": child.get("order_id"),
        "child_id": child.get("child_id"),
        "test_user_id": child.get("test_user_id"),
        "test_lab": child.get("test_lab"),
        "test_type": child.get("test_type"),
        "order_status": order_status,
        "end_time": end_time,
        "quarter": quarter,
        "week": week,
        "start_time": start_time,
        "test_time": test_time,
        "is_timeout": is_timeout,
        "expect_finishtime": expect,
        "timeout_days": timeout_days,
    }


def insert_finish_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    sql = """
        INSERT INTO statistic_experiment_finish (
            addTime, deleteStatus, order_id, child_id, test_user_id, test_lab, test_type,
            order_status, end_time, quarter, week, start_time, test_time,
            is_timeout, expect_finishtime, timeout_days
        ) VALUES (
            %(addTime)s, %(deleteStatus)s, %(order_id)s, %(child_id)s, %(test_user_id)s,
            %(test_lab)s, %(test_type)s, %(order_status)s, %(end_time)s, %(quarter)s,
            %(week)s, %(start_time)s, %(test_time)s, %(is_timeout)s,
            %(expect_finishtime)s, %(timeout_days)s
        )
    """
    inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        for row in chunk:
            execute(sql, row)
            inserted += 1
    return inserted


def refresh_statistic_finish() -> dict[str, Any]:
    """全量重刷 statistic_experiment_finish（对齐 integralEarnings2）。"""
    started = datetime.now()
    logger.info("refresh_statistic_finish start")
    truncate_finish()
    children = list_source_children()
    rows = [build_finish_row(c, now=started) for c in children]
    count = insert_finish_rows(rows)
    elapsed = (datetime.now() - started).total_seconds()
    logger.info("refresh_statistic_finish done: source=%s inserted=%s elapsed=%.1fs", len(children), count, elapsed)
    return {
        "source": len(children),
        "inserted": count,
        "elapsedSec": round(elapsed, 2),
    }


def refresh_line_run_num() -> dict[str, Any]:
    """对齐 integralEarnings5：进行中(status=38)子单数写入 experiment_line.run_num。"""
    # 对齐 Java queryAllLine + 看板线列表过滤：deleteStatus=0 且启用
    lines = fetch_all(
        """
        SELECT id FROM experiment_line
        WHERE deleteStatus = 0 AND status = 1
        """
    )
    updated = 0
    for line in lines:
        lid = line.get("id")
        if lid is None:
            continue
        num = int(
            scalar(
                """
                SELECT COUNT(*) FROM experiment_order_child
                WHERE line_id = %(lid)s AND order_status = 38
                """,
                {"lid": lid},
            )
            or 0
        )
        execute(
            "UPDATE experiment_line SET run_num = %(num)s WHERE id = %(lid)s",
            {"num": num, "lid": lid},
        )
        updated += 1
    return {"lines": updated}


def refresh_user_test_num() -> dict[str, Any]:
    """对齐 integralEarnings6：进行中子单数写入 sy_users.test_num。"""
    users = fetch_all(
        """
        SELECT u.id
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
        """,
        {"t0": TEST_UTOO_TYPES[0], "t1": TEST_UTOO_TYPES[1], "t2": TEST_UTOO_TYPES[2]},
    )
    updated = 0
    for user in users:
        uid = user.get("id")
        if not uid:
            continue
        num = int(
            scalar(
                """
                SELECT COUNT(*) FROM experiment_order_child
                WHERE test_user_id = %(uid)s AND order_status = 38
                """,
                {"uid": uid},
            )
            or 0
        )
        execute(
            "UPDATE sy_users SET test_num = %(num)s WHERE id = %(uid)s",
            {"num": num, "uid": uid},
        )
        updated += 1
    return {"users": updated}


def refresh_all_stat_snapshots() -> dict[str, Any]:
    """统计页相关刷表：finish + 实验线 + 人员测试中数量。"""
    finish = refresh_statistic_finish()
    lines = refresh_line_run_num()
    users = refresh_user_test_num()
    return {"finish": finish, "lines": lines, "users": users}
