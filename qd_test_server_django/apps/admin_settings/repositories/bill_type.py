from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return " LIMIT %(limit)s OFFSET %(offset)s", {"limit": page_size, "offset": offset}


def list_bill_types(*, bill_type: int, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar(
        "SELECT COUNT(*) FROM bill_type WHERE type = %(type)s",
        {"type": bill_type},
    )
    clause, params = _page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, name, value, delete_status, type, add_time, update_time
        FROM bill_type
        WHERE type = %(type)s
        ORDER BY add_time DESC
        {clause}
        """,
        {"type": bill_type, **params},
    )
    return [_normalize_bill(row) for row in rows], int(total)


def get_bill_type(bill_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, name, value, delete_status, type, add_time, update_time
        FROM bill_type WHERE id = %(id)s
        """,
        {"id": bill_id},
    )
    return _normalize_bill(row) if row else None


def find_by_name_and_type(*, name: str, bill_type: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id FROM bill_type
        WHERE name = %(name)s AND type = %(type)s
        """,
        {"name": name, "type": bill_type},
    )


def insert_bill_type(*, name: str, bill_type: int, user_id: str | None) -> int:
    return execute_insert(
        """
        INSERT INTO bill_type
            (name, delete_status, type, add_time, add_user_id, update_time)
        VALUES
            (%(name)s, 0, %(type)s, NOW(), %(user_id)s, NOW())
        """,
        {"name": name, "type": bill_type, "user_id": user_id},
    )


def update_bill_type_name(*, bill_id: int, name: str, user_id: str | None) -> None:
    execute(
        """
        UPDATE bill_type
        SET name = %(name)s, update_time = NOW(), update_user_id = %(user_id)s
        WHERE id = %(id)s
        """,
        {"id": bill_id, "name": name, "user_id": user_id},
    )


def update_bill_type_status(*, bill_id: int, disabled: bool, user_id: str | None) -> None:
    execute(
        """
        UPDATE bill_type
        SET delete_status = %(delete_status)s,
            update_time = NOW(),
            update_user_id = %(user_id)s
        WHERE id = %(id)s
        """,
        {"id": bill_id, "delete_status": 1 if disabled else 0, "user_id": user_id},
    )


def _normalize_bill(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "deleteStatus": bool(row.get("delete_status")),
    }
