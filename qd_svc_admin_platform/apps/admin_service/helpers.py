from __future__ import annotations

from apps.admin_system.helpers import page_clause

__all__ = ["page_clause", "normalize_row", "staff_id"]


def _snake_to_camel(name: str) -> str:
    if not name or "_" not in name:
        return name
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def normalize_row(row: dict | None) -> dict | None:
    if not row:
        return None
    return {_snake_to_camel(k): v for k, v in row.items()}


def normalize_rows(rows: list[dict]) -> list[dict]:
    return [normalize_row(row) or {} for row in rows]


def staff_id(user: dict | None, *, default: str = "1") -> str:
    if not user:
        return default
    return str(user.get("user_id") or user.get("id") or default)
