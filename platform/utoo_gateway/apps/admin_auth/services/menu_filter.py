"""UTOO 管理端菜单剔除：仅 BFF 产品逻辑，不改 identity 中台。"""
from __future__ import annotations

from typing import Any

HIDDEN_MENU_NAMES = frozenset({"微信支付测试"})
HIDDEN_MENU_URL_MARKERS = ("wxPayTest/", "wxPayTest")


def is_hidden_utoo_admin_menu(name: str | None = None, url: str | None = None) -> bool:
    if (name or "").strip() in HIDDEN_MENU_NAMES:
        return True
    url_l = (url or "").lower()
    return any(marker.lower() in url_l for marker in HIDDEN_MENU_URL_MARKERS)


def filter_java_child_menus(children: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for child in children or []:
        if is_hidden_utoo_admin_menu(child.get("name"), child.get("url")):
            continue
        row = dict(child)
        row["childrenMenus"] = filter_java_child_menus(child.get("childrenMenus"))
        out.append(row)
    return out


def filter_java_top_menus(menus: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in menus or []:
        if is_hidden_utoo_admin_menu(row.get("menuName"), row.get("url")):
            continue
        top = dict(row)
        top["childMenu"] = filter_java_child_menus(row.get("childMenu"))
        out.append(top)
    return out
