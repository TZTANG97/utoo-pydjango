"""菜单投影：同角色挂载多平台菜单时，按 platform 硬过滤，防串壳。"""
from __future__ import annotations

from typing import Any


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
