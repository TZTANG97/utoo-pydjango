from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import build_tree, new_id
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one


def list_menu_tree() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, menu_super_id, menu_status, menu_sort, menu_name, menu_icon,
               menu_url, menu_target, menu_rel, menu_open, menu_external,
               menu_fresh, pt_type
        FROM sy_menu
        WHERE menu_status = 1
        ORDER BY menu_sort ASC, menu_name ASC
        """
    )
    normalized = [_normalize_menu(row) for row in rows]
    return build_tree(normalized, parent_key="menuSuperId")


def list_all_menus_flat() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, menu_super_id, menu_status, menu_sort, menu_name, menu_icon,
               menu_url, menu_target, menu_rel, menu_open, menu_external,
               menu_fresh, pt_type
        FROM sy_menu
        ORDER BY menu_sort ASC
        """
    )
    return [_normalize_menu(row) for row in rows]


def get_menu(menu_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, menu_super_id, menu_status, menu_sort, menu_name, menu_icon,
               menu_url, menu_target, menu_rel, menu_open, menu_external,
               menu_fresh, pt_type
        FROM sy_menu WHERE id = %(id)s
        """,
        {"id": menu_id},
    )
    return _normalize_menu(row) if row else None


def insert_menu(data: dict[str, Any]) -> str:
    menu_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_menu
            (id, menu_super_id, menu_status, menu_sort, menu_name, menu_icon,
             menu_url, menu_target, menu_rel, menu_open, menu_external,
             menu_fresh, pt_type)
        VALUES
            (%(id)s, %(menu_super_id)s, %(menu_status)s, %(menu_sort)s, %(menu_name)s,
             %(menu_icon)s, %(menu_url)s, %(menu_target)s, %(menu_rel)s,
             %(menu_open)s, %(menu_external)s, %(menu_fresh)s, %(pt_type)s)
        """,
        {
            "id": menu_id,
            "menu_super_id": data.get("menu_super_id") or "0",
            "menu_status": int(data.get("menu_status") or 1),
            "menu_sort": int(data.get("menu_sort") or 0),
            "menu_name": data.get("menu_name") or "",
            "menu_icon": data.get("menu_icon"),
            "menu_url": data.get("menu_url"),
            "menu_target": data.get("menu_target") or "navTab",
            "menu_rel": data.get("menu_rel"),
            "menu_open": data.get("menu_open") or "false",
            "menu_external": data.get("menu_external") or "false",
            "menu_fresh": data.get("menu_fresh") or "true",
            "pt_type": data.get("pt_type") or "2",
        },
    )
    return menu_id


def update_menu(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_menu
        SET menu_super_id = %(menu_super_id)s,
            menu_status = %(menu_status)s,
            menu_sort = %(menu_sort)s,
            menu_name = %(menu_name)s,
            menu_icon = %(menu_icon)s,
            menu_url = %(menu_url)s,
            menu_target = %(menu_target)s,
            menu_rel = %(menu_rel)s,
            menu_open = %(menu_open)s,
            menu_external = %(menu_external)s,
            menu_fresh = %(menu_fresh)s,
            pt_type = %(pt_type)s
        WHERE id = %(id)s
        """,
        data,
    )


def delete_menu(menu_id: str) -> None:
    execute("DELETE FROM sy_role_menu WHERE menu_id = %(id)s", {"id": menu_id})
    execute("DELETE FROM sy_menu WHERE id = %(id)s", {"id": menu_id})


def _normalize_menu(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "menuSuperId": row.get("menu_super_id"),
        "menuStatus": row.get("menu_status"),
        "menuSort": row.get("menu_sort"),
        "menuName": row.get("menu_name"),
        "menuIcon": row.get("menu_icon"),
        "menuUrl": row.get("menu_url"),
        "menuTarget": row.get("menu_target"),
        "menuRel": row.get("menu_rel"),
        "menuOpen": row.get("menu_open"),
        "menuExternal": row.get("menu_external"),
        "menuFresh": row.get("menu_fresh"),
        "ptType": row.get("pt_type"),
    }
