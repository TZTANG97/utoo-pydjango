from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_openids(
    *,
    openid: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if openid:
        where += " AND t.openid = %(openid)s"
        params["openid"] = openid
    total = int(scalar(f"SELECT COUNT(*) FROM exp_openid t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.*
        FROM exp_openid t
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def insert_openid(openid: str) -> int:
    return execute_insert(
        """
        INSERT INTO exp_openid (addTime, deleteStatus, openid)
        VALUES (NOW(), 0, %(openid)s)
        """,
        {"openid": openid},
    )


def soft_delete_openid(record_id: int) -> None:
    execute(
        "UPDATE exp_openid SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": record_id},
    )


def update_openid_status(record_id: int, *, enabled: bool) -> bool:
    row = fetch_one(
        "SELECT id FROM exp_openid WHERE id = %(id)s LIMIT 1",
        {"id": record_id},
    )
    if not row:
        return False
    execute(
        "UPDATE exp_openid SET deleteStatus = %(delete_status)s WHERE id = %(id)s",
        {"id": record_id, "delete_status": 0 if enabled else 1},
    )
    return True
