"""菜单投影：同角色挂载多平台菜单时，按 platform 硬过滤，防串壳。

青岛 mall_qd 出参对齐 Java Console：
- 登录菜单 = MainServiceImpl.selectMenusTop（顶层 HashMap + childMenu / Menu 对象）
- 菜单管理 = MenuServiceImpl.queryMenus（扁平 SyMenu 字段，前端丢掉 id=0）
"""
from __future__ import annotations

from typing import Any

MENU_WRITE_JAVA_TO_SNAKE = {
    "menuSuperId": "menu_super_id",
    "menuStatus": "menu_status",
    "menuSort": "menu_sort",
    "menuName": "menu_name",
    "menuIcon": "menu_icon",
    "menuUrl": "menu_url",
    "menuTarget": "menu_target",
    "menuRel": "menu_rel",
    "menuOpen": "menu_open",
    "menuExternal": "menu_external",
    "menuFresh": "menu_fresh",
}


def normalize_menu_write(data: dict[str, Any]) -> dict[str, Any]:
    """写入同时接受 Java camelCase 与 snake_case。"""
    return {MENU_WRITE_JAVA_TO_SNAKE.get(key, key): value for key, value in data.items()}


def serialize_sy_menu_map(row: dict[str, Any] | Any) -> dict[str, Any]:
    """对齐 MenuMapper.selectByMenuSort / SyMenu JSON。"""

    def field(name):
        return row.get(name) if isinstance(row, dict) else getattr(row, name, None)

    return {
        "id": field("id"),
        "menuSuperId": field("menu_super_id"),
        "menuStatus": field("menu_status"),
        "menuSort": field("menu_sort"),
        "menuName": field("menu_name"),
        "menuIcon": field("menu_icon"),
        "menuUrl": field("menu_url"),
        "menuTarget": field("menu_target"),
        "menuRel": field("menu_rel"),
        "menuOpen": field("menu_open"),
        "menuExternal": field("menu_external"),
        "menuFresh": field("menu_fresh"),
    }


def serialize_java_menu_bean(row: dict[str, Any], all_menus: list[dict[str, Any]]) -> dict[str, Any]:
    """对齐 com.mall.sys.model.Menu JSON（子节点 childrenMenus）。"""
    menu_id = str(row.get("id") or "")
    return {
        "id": menu_id,
        "superId": row.get("menu_super_id") or "",
        "name": row.get("menu_name") or "",
        "icon": row.get("menu_icon") or "",
        "url": row.get("menu_url") or "",
        "target": row.get("menu_target"),
        "rel": row.get("menu_rel"),
        "open": row.get("menu_open"),
        "external": row.get("menu_external"),
        "fresh": row.get("menu_fresh"),
        "childrenMenus": build_java_child_menus(all_menus, menu_id),
    }


def build_java_child_menus(all_menus: list[dict[str, Any]], super_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for row in all_menus:
        if str(row.get("menu_super_id") or "") != (super_id or ""):
            continue
        menu_id = str(row.get("id") or "")
        if not menu_id or menu_id in {"0", super_id or ""}:
            continue
        children.append(serialize_java_menu_bean(row, all_menus))
    return children


def serialize_java_top_menu(row: dict[str, Any], all_menus: list[dict[str, Any]]) -> dict[str, Any]:
    """对齐 findmenuformainnotdev HashMap + childMenu。"""
    menu_id = str(row.get("id") or "")
    super_id = row.get("menu_super_id") or "0"
    icon = row.get("menu_icon")
    return {
        "id": menu_id,
        "menuName": row.get("menu_name") or "",
        "menuSuperId": super_id,
        "menuIcon": icon,
        "pid": super_id,
        "url": row.get("menu_url") or "",
        "external": row.get("menu_external"),
        "fresh": row.get("menu_fresh"),
        "icon": icon,
        "open": row.get("menu_open"),
        "rel": row.get("menu_rel"),
        "target": row.get("menu_target"),
        "childMenu": build_java_child_menus(all_menus, menu_id),
    }


def menu_matches_platform(pt_type: str | None, platform: str) -> bool:
    """pt_type 可为 '1' / '1,2' / '2' 等；要求包含平台码。"""
    if not platform:
        return False
    raw = (pt_type or "").strip()
    if not raw:
        return False
    return platform in raw


def filter_menus_by_platform(
    menus: list[dict[str, Any]],
    platform: str,
    *,
    pt_type_key: str = "pt_type",
) -> list[dict[str, Any]]:
    return [m for m in menus if menu_matches_platform(m.get(pt_type_key), platform)]


def filter_roles_by_type(
    roles: list[dict[str, Any]],
    role_type: int | str,
    *,
    type_key: str = "type",
) -> list[dict[str, Any]]:
    want = int(role_type)
    out: list[dict[str, Any]] = []
    for r in roles:
        try:
            if int(r.get(type_key)) == want:
                out.append(r)
        except (TypeError, ValueError):
            continue
    return out
