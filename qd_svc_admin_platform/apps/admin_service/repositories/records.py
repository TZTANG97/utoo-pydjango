from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def list_records(
    *,
    user_id: str = "",
    keywords: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE (cr.deleteStatus = 0 OR cr.deleteStatus IS NULL OR cr.deleteStatus = false)"
    params: dict[str, Any] = {}
    if user_id:
        where += " AND cr.user_id = %(user_id)s"
        params["user_id"] = user_id
    if keywords:
        where += (
            " AND (cr.problem_content LIKE %(keywords)s"
            " OR cr.reply_content LIKE %(keywords)s)"
        )
        params["keywords"] = f"%{keywords}%"
    if order_startime:
        where += " AND cr.addTime >= %(order_startime)s"
        params["order_startime"] = order_startime
    if order_endtime:
        where += " AND cr.addTime <= CONCAT(%(order_endtime)s, ' 23:59:59')"
        params["order_endtime"] = order_endtime

    total = int(
        scalar(f"SELECT COUNT(*) FROM communication_records cr {where}", params) or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            cr.id,
            cr.addTime,
            cr.deleteStatus,
            cr.problem_content,
            cr.reply_content,
            cr.common_problem_id,
            cr.user_id,
            u.userName AS userName,
            u.trueName AS trueName,
            u.mobile AS mobile
        FROM communication_records cr
        LEFT JOIN user u ON u.id = cr.user_id
        {where}
        ORDER BY cr.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_record(record_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            cr.id,
            cr.addTime,
            cr.deleteStatus,
            cr.problem_content,
            cr.reply_content,
            cr.common_problem_id,
            cr.user_id,
            u.userName AS userName,
            u.trueName AS trueName,
            u.mobile AS mobile
        FROM communication_records cr
        LEFT JOIN user u ON u.id = cr.user_id
        WHERE cr.id = %(id)s
        LIMIT 1
        """,
        {"id": record_id},
    )
    return normalize_row(row)


def delete_record(record_id: int) -> int:
    return execute(
        """
        UPDATE communication_records
        SET deleteStatus = 1
        WHERE id = %(id)s
        """,
        {"id": record_id},
    )
