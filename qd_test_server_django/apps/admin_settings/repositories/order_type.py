from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return " LIMIT %(limit)s OFFSET %(offset)s", {"limit": page_size, "offset": offset}


def list_order_types(*, type_name: str, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "deleteStatus = 0 AND pt_type LIKE '%%2%%'"
    params: dict[str, Any] = {}
    if type_name:
        where += " AND type_name LIKE %(type_name)s"
        params["type_name"] = f"%{type_name}%"
    total = scalar(f"SELECT COUNT(*) FROM order_type WHERE {where}", params)
    clause, page_params = _page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, addTime, deleteStatus, type_sort, type_name, type_desc, table_id, pt_type
        FROM order_type
        WHERE {where}
        ORDER BY addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, int(total)


def get_order_type(order_type_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, addTime, deleteStatus, type_sort, type_name, type_desc, table_id, pt_type
        FROM order_type WHERE id = %(id)s
        """,
        {"id": order_type_id},
    )


def insert_order_type(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO order_type
            (addTime, deleteStatus, type_sort, type_name, type_desc, table_id, pt_type)
        VALUES
            (NOW(), 0, %(type_sort)s, %(type_name)s, %(type_desc)s, %(table_id)s, %(pt_type)s)
        """,
        data,
    )


def update_order_type(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE order_type
        SET type_sort = %(type_sort)s,
            type_name = %(type_name)s,
            type_desc = %(type_desc)s,
            table_id = %(table_id)s,
            pt_type = %(pt_type)s
        WHERE id = %(id)s
        """,
        data,
    )


def soft_delete_order_type(order_type_id: int) -> None:
    execute(
        "UPDATE order_type SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": order_type_id},
    )


def list_order_type_tables() -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM order_type_table WHERE deleteStatus = 0 ORDER BY id ASC"
    )
