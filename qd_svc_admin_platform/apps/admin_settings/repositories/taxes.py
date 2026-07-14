from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return " LIMIT %(limit)s OFFSET %(offset)s", {"limit": page_size, "offset": offset}


def list_taxes(page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar("SELECT COUNT(*) FROM qd_taxes_config")
    clause, params = _page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, name, del_status, tax_value, add_time, memo
        FROM qd_taxes_config
        ORDER BY add_time DESC
        {clause}
        """,
        params,
    )
    return [_normalize_tax(row) for row in rows], int(total)


def get_tax(tax_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, name, del_status, tax_value, add_time, memo
        FROM qd_taxes_config WHERE id = %(id)s
        """,
        {"id": tax_id},
    )
    return _normalize_tax(row) if row else None


def select_tax_by_name(name: str) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT id FROM qd_taxes_config WHERE name = %(name)s",
        {"name": name},
    )


def insert_tax(*, name: str, tax_value: Decimal, user_id: str | None) -> int:
    return execute_insert(
        """
        INSERT INTO qd_taxes_config
            (name, del_status, tax_value, add_time, add_user_id, memo)
        VALUES
            (%(name)s, 0, %(tax_value)s, NOW(), %(user_id)s, NULL)
        """,
        {"name": name, "tax_value": tax_value, "user_id": user_id},
    )


def update_tax(*, tax_id: int, name: str, tax_value: Decimal, user_id: str | None) -> None:
    execute(
        """
        UPDATE qd_taxes_config
        SET name = %(name)s,
            tax_value = %(tax_value)s,
            update_time = NOW(),
            update_user_id = %(user_id)s
        WHERE id = %(id)s
        """,
        {"id": tax_id, "name": name, "tax_value": tax_value, "user_id": user_id},
    )


def update_tax_status(*, tax_id: int, disabled: bool, user_id: str | None) -> None:
    execute(
        """
        UPDATE qd_taxes_config
        SET del_status = %(del_status)s,
            update_time = NOW(),
            update_user_id = %(user_id)s
        WHERE id = %(id)s
        """,
        {"id": tax_id, "del_status": 1 if disabled else 0, "user_id": user_id},
    )


def delete_tax(tax_id: int) -> None:
    execute("DELETE FROM qd_taxes_config WHERE id = %(id)s", {"id": tax_id})


def _normalize_tax(row: dict[str, Any]) -> dict[str, Any]:
    tax_value = row.get("tax_value")
    return {
        **row,
        "delStatus": bool(row.get("del_status")),
        "taxValue": float(tax_value) if tax_value is not None else None,
    }


def validate_tax_rate_text(tax_value: str) -> tuple[Decimal | None, str]:
    if not tax_value:
        return None, "请填写税率"
    if not re.fullmatch(r"\d+(\.\d+)?", tax_value.strip()):
        return None, "请填写正确格式的税率"
    val = Decimal(tax_value)
    if val < 0 or val > 1:
        return None, "填写有效税率"
    return val, ""
