"""员工 data-scope / permissions（对齐青岛 identity auth.py，按 platform 硬过滤）。"""
from __future__ import annotations

from typing import Any

from django.db import connection

ADMIN_ROLE_NAME = "系统管理员"
PUBLIC_ROLE_NAME = "公共账号"
EXTERNAL_COOPERATION_ROLE_NAME = "外部合作公司"


def _fetchall(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with connection.cursor() as cur:
        cur.execute(sql, params or {})
        cols = [c[0] for c in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetchone(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = _fetchall(sql, params)
    return rows[0] if rows else None


def list_platform_role_ids(user_id: str, role_type: int) -> list[str]:
    rows = _fetchall(
        """
        SELECT r.id
        FROM sy_role r
        INNER JOIN sy_user_role ur ON ur.role_id = r.id
        WHERE ur.user_id = %(uid)s AND r.type = %(rtype)s
        """,
        {"uid": user_id, "rtype": role_type},
    )
    return [str(r["id"]) for r in rows]


def list_menu_ids_for_roles(role_ids: list[str], platform: str) -> list[str]:
    if not role_ids:
        return []
    placeholders = ", ".join(["%s"] * len(role_ids))
    like = f"%{platform}%"
    sql = f"""
        SELECT DISTINCT m.id
        FROM sy_role_menu rm
        INNER JOIN sy_menu m ON m.id = rm.menu_id
        WHERE rm.role_id IN ({placeholders})
          AND m.menu_status = 1
          AND m.pt_type LIKE %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, [*role_ids, like])
        return [str(r[0]) for r in cur.fetchall()]


def list_permission_urls(menu_ids: list[str], role_ids: list[str], platform: str) -> list[str]:
    urls: set[str] = set()
    if menu_ids:
        ph = ", ".join(["%s"] * len(menu_ids))
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT menu_url FROM sy_menu
                WHERE id IN ({ph}) AND menu_status = 1
                  AND menu_url IS NOT NULL AND menu_url <> ''
                """,
                menu_ids,
            )
            for (url,) in cur.fetchall():
                if url:
                    urls.add(str(url).strip())
    if role_ids:
        like = f"%{platform}%"
        ph = ", ".join(["%s"] * len(role_ids))
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT a.action_url
                FROM sy_role_action ra
                INNER JOIN sy_action a ON a.id = ra.action_id
                INNER JOIN sy_menu m ON m.id = a.menu_id
                WHERE ra.role_id IN ({ph})
                  AND m.pt_type LIKE %s
                  AND a.action_url IS NOT NULL AND a.action_url <> ''
                """,
                [*role_ids, like],
            )
            for (action_url,) in cur.fetchall():
                for part in str(action_url or "").split(","):
                    part = part.strip()
                    if part:
                        urls.add(part)
    return sorted(urls)


def _type_role_name(user_type: str | None) -> str:
    if not user_type:
        return "销售人员"
    row = _fetchone(
        """
        SELECT ut.type_name, utr.name AS role_name
        FROM sy_user_type ut
        LEFT JOIN user_type_role utr ON utr.id = ut.role_id
        WHERE ut.type_sort = %(ts)s
        LIMIT 1
        """,
        {"ts": user_type},
    )
    if not row:
        return str(user_type)
    return (row.get("role_name") or row.get("type_name") or user_type) or "销售人员"


def resolve_filter_list(role_name: str, has_linked_external: bool) -> int:
    if role_name == ADMIN_ROLE_NAME:
        return 2
    if role_name == PUBLIC_ROLE_NAME:
        return 0
    if has_linked_external:
        return 4
    if role_name == EXTERNAL_COOPERATION_ROLE_NAME:
        return 1
    return 3


def build_data_scope(user_id: str, user_type: str | None, platform: str) -> dict[str, Any]:
    role_name = _type_role_name(user_type)
    like = f"%{platform}%"
    company_ids = [
        str(r["company_id"])
        for r in _fetchall(
            """
            SELECT company_id FROM sy_user_company
            WHERE user_id = %(uid)s AND deleteStatus = 0 AND pt_type LIKE %(like)s
            """,
            {"uid": user_id, "like": like},
        )
    ]
    sale_ids = [
        str(r["saleuser_id"])
        for r in _fetchall(
            """
            SELECT saleuser_id FROM sy_user_saleuser
            WHERE user_id = %(uid)s AND deleteStatus = 0 AND pt_type LIKE %(like)s
            """,
            {"uid": user_id, "like": like},
        )
    ]
    if user_id not in sale_ids:
        sale_ids.append(user_id)
    order_type_ids = [
        str(r["type_id"])
        for r in _fetchall(
            """
            SELECT type_id FROM sy_user_ordertype
            WHERE user_id = %(uid)s AND deleteStatus = 0 AND pt_type LIKE %(like)s
            """,
            {"uid": user_id, "like": like},
        )
    ]
    linked = _fetchone(
        "SELECT id FROM user WHERE syuser_id = %(uid)s LIMIT 1",
        {"uid": user_id},
    )
    return {
        "filter_list": resolve_filter_list(role_name, bool(linked)),
        "role_name": role_name,
        "visible_sales_ids": sale_ids,
        "company_ids": company_ids,
        "order_type_ids": order_type_ids,
    }


def build_permissions(user_id: str, platform: str) -> dict[str, Any]:
    role_type = int(platform)
    role_ids = list_platform_role_ids(user_id, role_type)
    menu_ids = list_menu_ids_for_roles(role_ids, platform)
    return {
        "role_ids": role_ids,
        "menu_ids": menu_ids,
        "permissions": list_permission_urls(menu_ids, role_ids, platform),
    }
