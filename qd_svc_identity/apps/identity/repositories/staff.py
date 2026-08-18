from __future__ import annotations

from typing import Any

from django.db import connection


def _fetchall(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with connection.cursor() as cur:
        cur.execute(sql, params or {})
        cols = [c[0] for c in cur.description] if cur.description else []
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetchone(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = _fetchall(sql, params)
    return rows[0] if rows else None


def find_sy_user_by_login_name(login_name: str) -> dict[str, Any] | None:
    return _fetchone(
        """
        SELECT id, user_name, true_name, user_password, user_status, dept_id,
               email, account_type, pt_type, type, mobile_phone_number,
               error_count, error_time
        FROM sy_users
        WHERE user_name = %(login_name)s
        LIMIT 1
        """,
        {"login_name": login_name},
    )


def find_user_roles(user_id: str, role_type: int) -> list[dict[str, Any]]:
    return _fetchall(
        """
        SELECT r.id, r.role_name, r.type
        FROM sy_role r
        INNER JOIN sy_user_role ur ON ur.role_id = r.id
        WHERE ur.user_id = %(user_id)s
          AND r.type = %(role_type)s
        """,
        {"user_id": user_id, "role_type": role_type},
    )


def fetch_user_menus(user_id: str, role_type: int, platform: str) -> list[dict[str, Any]]:
    """员工菜单：角色 type + 菜单 pt_type 含 platform。"""
    like = f"%{platform}%"
    return _fetchall(
        """
        SELECT DISTINCT
            m.id,
            m.menu_name,
            m.menu_super_id,
            m.menu_icon,
            m.menu_url,
            m.menu_target,
            m.menu_rel,
            m.menu_open,
            m.menu_external,
            m.menu_fresh,
            m.menu_sort,
            m.pt_type
        FROM sy_role_menu rm
        INNER JOIN sy_menu m ON rm.menu_id = m.id
        INNER JOIN sy_role r ON rm.role_id = r.id
        INNER JOIN sy_user_role ur ON ur.role_id = rm.role_id
        WHERE ur.user_id = %(user_id)s
          AND m.menu_status = 1
          AND r.type = %(role_type)s
          AND m.pt_type LIKE %(pt_like)s
        ORDER BY m.menu_sort ASC, m.id ASC
        """,
        {"user_id": user_id, "role_type": role_type, "pt_like": like},
    )


def fetch_top_level_menus(user_id: str, role_type: int, platform: str) -> list[dict[str, Any]]:
    like = f"%{platform}%"
    return _fetchall(
        """
        SELECT DISTINCT
            m.id,
            m.menu_name,
            m.menu_super_id,
            m.menu_icon,
            m.menu_url,
            m.menu_target,
            m.menu_rel,
            m.menu_open,
            m.menu_external,
            m.menu_fresh,
            m.menu_sort,
            m.pt_type
        FROM sy_role_menu rm
        INNER JOIN sy_menu m ON rm.menu_id = m.id
        INNER JOIN sy_role r ON rm.role_id = r.id
        INNER JOIN sy_user_role ur ON ur.role_id = rm.role_id
        WHERE ur.user_id = %(user_id)s
          AND m.menu_super_id = '0'
          AND m.menu_status = 1
          AND r.type = %(role_type)s
          AND m.pt_type LIKE %(pt_like)s
        ORDER BY m.menu_sort ASC, m.id ASC
        """,
        {"user_id": user_id, "role_type": role_type, "pt_like": like},
    )


def find_dept_name(dept_id: str | None) -> str:
    if not dept_id:
        return ""
    row = _fetchone(
        "SELECT dept_name FROM sy_dept WHERE id = %(id)s LIMIT 1",
        {"id": str(dept_id)},
    )
    return (row.get("dept_name") or "") if row else ""


def update_login_success(user_id: str, login_ip: str) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE sy_users
            SET last_login_ip = %(ip)s,
                last_login_time = NOW(),
                error_count = 0,
                error_time = NULL
            WHERE id = %(uid)s
            """,
            {"ip": login_ip or "", "uid": user_id},
        )


def record_login_failure(user_id: str, error_count: int) -> None:
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE sy_users
            SET error_count = %(cnt)s, error_time = NOW()
            WHERE id = %(uid)s
            """,
            {"cnt": error_count, "uid": user_id},
        )
