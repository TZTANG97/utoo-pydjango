from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_addresses(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar("SELECT COUNT(*) FROM test_address WHERE deleteStatus = 0")
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, true_name, mobile, address, addTime, deleteStatus
        FROM test_address
        WHERE deleteStatus = 0
        ORDER BY addTime DESC
        {clause}
        """,
        page_params,
    )
    return [_normalize_address(row) for row in rows], int(total)


def get_address(address_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, true_name, mobile, address, addTime, deleteStatus
        FROM test_address WHERE id = %(id)s
        """,
        {"id": address_id},
    )
    return _normalize_address(row) if row else None


def insert_address(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO test_address (true_name, mobile, address, addTime, deleteStatus)
        VALUES (%(true_name)s, %(mobile)s, %(address)s, NOW(), 0)
        """,
        {
            "true_name": data.get("true_name") or "",
            "mobile": data.get("mobile") or "",
            "address": data.get("address") or "",
        },
    )


def update_address(address_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE test_address
        SET true_name = %(true_name)s, mobile = %(mobile)s, address = %(address)s
        WHERE id = %(id)s
        """,
        {"id": address_id, **data},
    )


def soft_delete_address(address_id: int) -> None:
    execute(
        "UPDATE test_address SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": address_id},
    )


def _normalize_address(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "trueName": row.get("true_name"),
        "mobile": row.get("mobile"),
        "address": row.get("address"),
        "addTime": row.get("addTime"),
        "deleteStatus": bool(row.get("deleteStatus")),
    }
