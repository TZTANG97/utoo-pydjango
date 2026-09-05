"""UTOO 管理端菜单 BFF：identity 原子读 + 本进程拼装（方案 B）。"""
from __future__ import annotations

from typing import Any

from apps.core.svc_proxy import identity_get
from shared.utoo_menu import build_staff_menu_tree


class UtooMenuBffError(Exception):
    def __init__(self, message: str, *, status: int = 502):
        super().__init__(message)
        self.status = status


def _role_ids_from_user(user: dict | None) -> list[str]:
    u = user or {}
    raw = u.get("role_ids") or u.get("roleIds") or []
    if isinstance(raw, str):
        raw = [x for x in raw.split(",") if x.strip()]
    out: list[str] = []
    for item in raw or []:
        s = str(item or "").strip()
        if s and s != "0":
            out.append(s)
    return out


def _collect_allowed_menu_ids(token: str, role_ids: list[str]) -> set[str]:
    allowed: set[str] = set()
    for role_id in role_ids:
        upstream = identity_get(f"/api/v1/identity/roles/{role_id}", token=token, channel="admin")
        if upstream.status_code >= 500:
            raise UtooMenuBffError("身份中台不可用", status=503)
        if upstream.status_code == 401:
            raise UtooMenuBffError("未登录", status=401)
        body = upstream.data if isinstance(upstream.data, dict) else {}
        data = body.get("data") if isinstance(body.get("data"), dict) else body.get("data")
        if not isinstance(data, dict):
            # 某些包装直接 data=role
            continue
        for mid in data.get("menu_ids") or data.get("menuIds") or []:
            s = str(mid or "").strip()
            if s and s != "0":
                allowed.add(s)
    return allowed


def build_utoo_admin_menu_tree(*, token: str, user: dict | None) -> list[dict[str, Any]]:
    role_ids = _role_ids_from_user(user)
    if not role_ids:
        raise UtooMenuBffError("当前用户无角色，无法拼装菜单", status=400)

    allowed = _collect_allowed_menu_ids(token, role_ids)
    if not allowed:
        return []

    upstream = identity_get("/api/v1/identity/menus/all", token=token, channel="admin")
    if upstream.status_code >= 500:
        raise UtooMenuBffError("身份中台不可用", status=503)
    if upstream.status_code == 401:
        raise UtooMenuBffError("未登录", status=401)
    body = upstream.data if isinstance(upstream.data, dict) else {}
    rows = body.get("data")
    if not isinstance(rows, list):
        raise UtooMenuBffError("menus/all 返回格式错误", status=503)

    return build_staff_menu_tree(
        all_menu_rows=rows,
        allowed_menu_ids=allowed,
        platform="2",
        filter_by_platform=True,
    )
