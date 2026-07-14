from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, scalar


def overview(*, dept_id: str = "", year: str = "") -> dict[str, Any]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if year:
        where += " AND DATE_FORMAT(COALESCE(t.end_time, t.expect_finishtime), '%%Y') = %(year)s"
        params["year"] = year
    if dept_id and dept_id not in ("0", ""):
        where += """
            AND t.test_user_id IN (
                SELECT id FROM sy_users WHERE dept_id = %(dept_id)s
            )
        """
        params["dept_id"] = dept_id

    finished = int(
        scalar(
            f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 2",
            params,
        )
        or 0
    )
    doing = int(
        scalar(
            f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 1",
            params,
        )
        or 0
    )
    waiting = int(
        scalar(
            f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.order_status = 0",
            params,
        )
        or 0
    )
    timeout = int(
        scalar(
            f"SELECT COUNT(*) FROM statistic_experiment_finish t {where} AND t.is_timeout = 1",
            params,
        )
        or 0
    )
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


def monthly_finish_trend(*, dept_id: str = "", year: str) -> list[dict[str, Any]]:
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
    """
    params: dict[str, Any] = {"year": year}
    if dept_id and dept_id not in ("0", ""):
        where += """
            AND t.test_user_id IN (
                SELECT id FROM sy_users WHERE dept_id = %(dept_id)s
            )
        """
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


def tester_workload(*, dept_id: str = "", year: str) -> list[dict[str, Any]]:
    where = """
        WHERE t.deleteStatus = 0
          AND t.order_status = 2
          AND DATE_FORMAT(t.end_time, '%%Y') = %(year)s
    """
    params: dict[str, Any] = {"year": year}
    if dept_id and dept_id not in ("0", ""):
        where += " AND u.dept_id = %(dept_id)s"
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
        where += " AND u.dept_id = %(dept_id)s"
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
