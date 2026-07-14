from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

PLATFORM_TYPE = 2


def list_user_types(*, type_name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.type = %(platform_type)s"
    params: dict[str, Any] = {"platform_type": PLATFORM_TYPE}
    if type_name:
        where += " AND t.type_name LIKE %(type_name)s"
        params["type_name"] = f"%{type_name}%"
    total = scalar(
        f"SELECT COUNT(*) FROM sy_user_type t {where}",
        params,
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.id, t.type_name, t.type_desc, t.type_sort, t.true_type, t.type,
               t.role_id, t.is_fixed, t.fixed_scale, utr.name AS role_name
        FROM sy_user_type t
        LEFT JOIN user_type_role utr ON utr.id = t.role_id
        {where}
        ORDER BY t.type_sort ASC, t.id ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_user_type(row) for row in rows], int(total)


def get_user_type(type_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT t.id, t.type_name, t.type_desc, t.type_sort, t.true_type, t.type,
               t.role_id, t.is_fixed, t.fixed_scale, utr.name AS role_name
        FROM sy_user_type t
        LEFT JOIN user_type_role utr ON utr.id = t.role_id
        WHERE t.id = %(id)s
        """,
        {"id": type_id},
    )
    return _normalize_user_type(row) if row else None


def insert_user_type(data: dict[str, Any]) -> str:
    type_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_user_type
            (id, type_name, type_desc, type_sort, true_type, type, role_id, is_fixed, fixed_scale)
        VALUES
            (%(id)s, %(type_name)s, %(type_desc)s, %(type_sort)s, %(true_type)s,
             %(type)s, %(role_id)s, %(is_fixed)s, %(fixed_scale)s)
        """,
        {
            "id": type_id,
            "type_name": data.get("type_name") or "",
            "type_desc": data.get("type_desc"),
            "type_sort": data.get("type_sort") or "0",
            "true_type": data.get("true_type"),
            "type": data.get("type") or PLATFORM_TYPE,
            "role_id": data.get("role_id") or data.get("roleId"),
            "is_fixed": int(data.get("is_fixed") or 0),
            "fixed_scale": data.get("fixed_scale"),
        },
    )
    return type_id


def update_user_type(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_user_type
        SET type_name = %(type_name)s,
            type_desc = %(type_desc)s,
            type_sort = %(type_sort)s,
            true_type = %(true_type)s,
            type = %(type)s,
            role_id = %(role_id)s,
            is_fixed = %(is_fixed)s,
            fixed_scale = %(fixed_scale)s
        WHERE id = %(id)s
        """,
        {
            "id": data.get("id"),
            "type_name": data.get("type_name") or "",
            "type_desc": data.get("type_desc"),
            "type_sort": data.get("type_sort") or "0",
            "true_type": data.get("true_type"),
            "type": data.get("type") or PLATFORM_TYPE,
            "role_id": data.get("role_id") or data.get("roleId"),
            "is_fixed": int(data.get("is_fixed") or 0),
            "fixed_scale": data.get("fixed_scale"),
        },
    )


def delete_user_type(type_id: str) -> None:
    execute("DELETE FROM sy_user_type WHERE id = %(id)s", {"id": type_id})


def list_type_role_options() -> list[dict[str, Any]]:
    rows = fetch_all("SELECT id, name FROM user_type_role ORDER BY id ASC")
    return [{"id": r["id"], "name": r.get("name")} for r in rows]


def _normalize_user_type(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "typeName": row.get("type_name"),
        "typeDesc": row.get("type_desc"),
        "typeSort": row.get("type_sort"),
        "trueType": row.get("true_type"),
        "type": row.get("type"),
        "roleId": row.get("role_id"),
        "roleName": row.get("role_name"),
        "isFixed": row.get("is_fixed"),
        "fixedScale": row.get("fixed_scale"),
    }
