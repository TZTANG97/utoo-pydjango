from __future__ import annotations

from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_auth.services.menu_filter import is_hidden_utoo_admin_menu


def _build_child_menus(all_menus: list[dict[str, Any]], super_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for row in all_menus:
        if str(row.get("menu_super_id") or "") != super_id:
            continue
        if is_hidden_utoo_admin_menu(row.get("menu_name"), row.get("menu_url")):
            continue
        menu_id = str(row.get("id") or "")
        child = {
            "id": menu_id,
            "name": row.get("menu_name") or "",
            "url": row.get("menu_url") or "",
            "icon": row.get("menu_icon") or "",
            "superId": row.get("menu_super_id") or "",
            "target": row.get("menu_target") or "",
            "rel": row.get("menu_rel") or "",
            "open": row.get("menu_open") or "",
            "external": row.get("menu_external") or "",
            "fresh": row.get("menu_fresh") or "",
            "childrenMenus": _build_child_menus(all_menus, menu_id),
        }
        children.append(child)
    return children


def select_menus_top(user_id: str) -> list[dict[str, Any]]:
    """对齐 Java MainServiceImpl.selectMenusTop + VueController.main.ajax"""
    tops = staff_repo.fetch_top_level_menus(user_id)
    all_menus = staff_repo.fetch_user_menus(user_id)
    result: list[dict[str, Any]] = []
    for row in tops:
        if is_hidden_utoo_admin_menu(row.get("menu_name"), row.get("menu_url")):
            continue
        menu_id = str(row.get("id") or "")
        child_menu = _build_child_menus(all_menus, menu_id)
        result.append(
            {
                "id": menu_id,
                "menuName": row.get("menu_name") or "",
                "menuSuperId": row.get("menu_super_id") or "0",
                "menuIcon": row.get("menu_icon") or "",
                "pid": row.get("menu_super_id") or "0",
                "url": row.get("menu_url") or "",
                "external": row.get("menu_external") or "",
                "fresh": row.get("menu_fresh") or "",
                "icon": row.get("menu_icon") or "",
                "open": row.get("menu_open") or "",
                "rel": row.get("menu_rel") or "",
                "target": row.get("menu_target") or "",
                "childMenu": child_menu,
            }
        )
    return result
