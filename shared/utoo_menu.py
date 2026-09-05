"""对齐 gateway menu_bff.java_menu — Java Console 菜单 JSON（UTOO / 青岛共用）。"""
from __future__ import annotations

from typing import Any


def menu_matches_platform(pt_type: str | None, platform: str) -> bool:
    if not platform:
        return False
    raw = (pt_type or "").strip()
    if not raw:
        return False
    return platform in raw


def _row_val(row: dict[str, Any], *keys: str):
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _menu_id(row: dict[str, Any]) -> str:
    return str(_row_val(row, "id") or "")


def _super_id(row: dict[str, Any]) -> str:
    return str(_row_val(row, "menuSuperId", "menu_super_id") or "")


def build_java_child_menus(all_menus: list[dict[str, Any]], super_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for row in all_menus:
        sid = str(_row_val(row, "menuSuperId", "menu_super_id") or "")
        if sid != (super_id or ""):
            continue
        menu_id = str(_row_val(row, "id") or "")
        if not menu_id or menu_id in {"0", super_id or ""}:
            continue
        children.append(serialize_java_menu_bean(row, all_menus))
    return children


def serialize_java_menu_bean(row: dict[str, Any], all_menus: list[dict[str, Any]]) -> dict[str, Any]:
    menu_id = str(_row_val(row, "id") or "")
    return {
        "id": menu_id,
        "superId": _row_val(row, "menuSuperId", "menu_super_id") or "",
        "name": _row_val(row, "menuName", "menu_name") or "",
        "icon": _row_val(row, "menuIcon", "menu_icon") or "",
        "url": _row_val(row, "menuUrl", "menu_url") or "",
        "target": _row_val(row, "menuTarget", "menu_target"),
        "rel": _row_val(row, "menuRel", "menu_rel"),
        "open": _row_val(row, "menuOpen", "menu_open"),
        "external": _row_val(row, "menuExternal", "menu_external"),
        "fresh": _row_val(row, "menuFresh", "menu_fresh"),
        "childrenMenus": build_java_child_menus(all_menus, menu_id),
    }


def serialize_java_top_menu(row: dict[str, Any], all_menus: list[dict[str, Any]]) -> dict[str, Any]:
    menu_id = str(_row_val(row, "id") or "")
    super_id = _row_val(row, "menuSuperId", "menu_super_id") or "0"
    icon = _row_val(row, "menuIcon", "menu_icon")
    return {
        "id": menu_id,
        "menuName": _row_val(row, "menuName", "menu_name") or "",
        "menuSuperId": super_id,
        "menuIcon": icon,
        "pid": super_id,
        "url": _row_val(row, "menuUrl", "menu_url") or "",
        "external": _row_val(row, "menuExternal", "menu_external"),
        "fresh": _row_val(row, "menuFresh", "menu_fresh"),
        "icon": icon,
        "open": _row_val(row, "menuOpen", "menu_open"),
        "rel": _row_val(row, "menuRel", "menu_rel"),
        "target": _row_val(row, "menuTarget", "menu_target"),
        "childMenu": build_java_child_menus(all_menus, menu_id),
    }


def build_staff_menu_tree(
    *,
    all_menu_rows: list[dict[str, Any]],
    allowed_menu_ids: set[str],
    platform: str = "",
    filter_by_platform: bool = False,
) -> list[dict[str, Any]]:
    """对齐 Java MainServiceImpl.selectMenusTop。

    青岛：filter_by_platform=False（与 gateway menu_bff 一致）。
    UTOO：filter_by_platform=True 且 platform='2'（pt_type 含 2）。
    """
    allowed_rows: list[dict[str, Any]] = []
    for row in all_menu_rows:
        menu_id = _menu_id(row)
        if not menu_id or menu_id == "0":
            continue
        if menu_id not in allowed_menu_ids:
            continue
        if filter_by_platform and not menu_matches_platform(
            str(_row_val(row, "ptType", "pt_type") or ""), platform
        ):
            continue
        raw_status = _row_val(row, "menuStatus", "menu_status")
        status = 1 if raw_status is None else int(raw_status)
        if status != 1:
            continue
        allowed_rows.append(row)

    tops = [row for row in allowed_rows if _super_id(row) in {"", "0"}]
    tops.sort(
        key=lambda row: (
            int(_row_val(row, "menuSort", "menu_sort") or 0),
            _menu_id(row),
        )
    )
    return [serialize_java_top_menu(row, allowed_rows) for row in tops]
