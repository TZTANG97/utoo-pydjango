from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_whitelist(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE w.deleteStatus = 0"
    total = int(scalar(f"SELECT COUNT(*) FROM whitelist w {where}") or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            w.id,
            w.addTime,
            w.deleteStatus,
            w.syuser_id AS syuserId,
            w.type,
            u.user_name AS userName
        FROM whitelist w
        LEFT JOIN sy_users u ON w.syuser_id = u.id
        {where}
        ORDER BY w.addTime DESC
        {clause}
        """,
        page_params,
    )
    return rows, total


def get_whitelist(item_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            w.id,
            w.addTime,
            w.syuser_id AS syuserId,
            w.type,
            u.user_name AS userName
        FROM whitelist w
        LEFT JOIN sy_users u ON w.syuser_id = u.id
        WHERE w.deleteStatus = 0 AND w.id = %(id)s
        LIMIT 1
        """,
        {"id": item_id},
    )


def exists_user_type(syuser_id: str, wl_type: int, exclude_id: int | None = None) -> bool:
    sql = """
        SELECT COUNT(*) FROM whitelist
        WHERE deleteStatus = 0 AND syuser_id = %(syuser_id)s AND type = %(type)s
    """
    params: dict[str, Any] = {"syuser_id": syuser_id, "type": wl_type}
    if exclude_id:
        sql += " AND id <> %(id)s"
        params["id"] = exclude_id
    return int(scalar(sql, params) or 0) > 0


def insert_whitelist(*, syuser_id: str, wl_type: int) -> int:
    return execute_insert(
        """
        INSERT INTO whitelist (addTime, deleteStatus, syuser_id, type)
        VALUES (NOW(), 0, %(syuser_id)s, %(type)s)
        """,
        {"syuser_id": syuser_id, "type": wl_type},
    )


def update_whitelist(*, item_id: int, syuser_id: str, wl_type: int) -> None:
    execute(
        """
        UPDATE whitelist
        SET syuser_id = %(syuser_id)s, type = %(type)s
        WHERE id = %(id)s
        """,
        {"id": item_id, "syuser_id": syuser_id, "type": wl_type},
    )


def delete_whitelist(item_id: int) -> int:
    return execute("DELETE FROM whitelist WHERE id = %(id)s", {"id": item_id})


def list_sy_users(keyword: str = "") -> list[dict[str, Any]]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if keyword:
        where += " AND (user_name LIKE %(kw)s OR trueName LIKE %(kw)s)"
        params["kw"] = f"%{keyword}%"
    return fetch_all(
        f"""
        SELECT id, user_name AS userName, trueName
        FROM sy_users
        {where}
        ORDER BY user_name ASC
        LIMIT 100
        """,
        params,
    )
