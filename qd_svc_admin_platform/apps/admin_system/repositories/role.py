from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_roles(*, role_name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE (type = 2 OR type IS NULL)"
    params: dict[str, Any] = {}
    if role_name:
        where += " AND role_name LIKE %(role_name)s"
        params["role_name"] = f"%{role_name}%"
    total = scalar(f"SELECT COUNT(*) FROM sy_role {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, role_name, role_desc, type
        FROM sy_role
        {where}
        ORDER BY role_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_role(row) for row in rows], int(total)


def get_role(role_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT id, role_name, role_desc, type FROM sy_role WHERE id = %(id)s",
        {"id": role_id},
    )
    if not row:
        return None
    role = _normalize_role(row)
    role["menuIds"] = get_role_menu_ids(role_id)
    return role


def insert_role(data: dict[str, Any]) -> str:
    role_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_role (id, role_name, role_desc, type)
        VALUES (%(id)s, %(role_name)s, %(role_desc)s, 2)
        """,
        {
            "id": role_id,
            "role_name": data.get("role_name") or "",
            "role_desc": data.get("role_desc"),
        },
    )
    return role_id


def update_role(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_role
        SET role_name = %(role_name)s, role_desc = %(role_desc)s
        WHERE id = %(id)s
        """,
        data,
    )


def delete_roles(role_ids: list[str]) -> None:
    for role_id in role_ids:
        execute("DELETE FROM sy_user_role WHERE role_id = %(id)s", {"id": role_id})
        execute("DELETE FROM sy_role_menu WHERE role_id = %(id)s", {"id": role_id})
        execute("DELETE FROM sy_role WHERE id = %(id)s", {"id": role_id})


def get_role_menu_ids(role_id: str) -> list[str]:
    rows = fetch_all(
        "SELECT menu_id FROM sy_role_menu WHERE role_id = %(role_id)s",
        {"role_id": role_id},
    )
    return [str(r["menu_id"]) for r in rows if r.get("menu_id")]


def set_role_menus(role_id: str, menu_ids: list[str]) -> None:
    execute("DELETE FROM sy_role_menu WHERE role_id = %(role_id)s", {"role_id": role_id})
    for menu_id in menu_ids:
        if menu_id:
            execute_insert(
                "INSERT INTO sy_role_menu (role_id, menu_id) VALUES (%(role_id)s, %(menu_id)s)",
                {"role_id": role_id, "menu_id": menu_id},
            )


def list_role_users(role_id: str, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    params = {"role_id": role_id}
    total = scalar(
        """
        SELECT COUNT(*)
        FROM sy_users u
        INNER JOIN sy_user_role ur ON ur.user_id = u.id
        WHERE ur.role_id = %(role_id)s
        """,
        params,
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT u.id, u.user_name, u.true_name, u.dept_id, d.dept_name
        FROM sy_users u
        INNER JOIN sy_user_role ur ON ur.user_id = u.id
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        WHERE ur.role_id = %(role_id)s
        ORDER BY u.user_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [
        {
            "id": r["id"],
            "userName": r.get("user_name"),
            "trueName": r.get("true_name"),
            "deptName": r.get("dept_name"),
        }
        for r in rows
    ], int(total)


def add_users_to_role(role_id: str, user_ids: list[str]) -> None:
    for user_id in user_ids:
        exists = fetch_one(
            """
            SELECT 1 FROM sy_user_role
            WHERE role_id = %(role_id)s AND user_id = %(user_id)s LIMIT 1
            """,
            {"role_id": role_id, "user_id": user_id},
        )
        if not exists:
            execute_insert(
                "INSERT INTO sy_user_role (role_id, user_id) VALUES (%(role_id)s, %(user_id)s)",
                {"role_id": role_id, "user_id": user_id},
            )


def remove_users_from_role(user_role_ids: list[str]) -> None:
    for pair in user_role_ids:
        parts = pair.split(":")
        if len(parts) == 2:
            execute(
                "DELETE FROM sy_user_role WHERE role_id = %(role_id)s AND user_id = %(user_id)s",
                {"role_id": parts[0], "user_id": parts[1]},
            )


def _normalize_role(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "roleName": row.get("role_name"),
        "roleDesc": row.get("role_desc"),
        "type": row.get("type"),
    }
