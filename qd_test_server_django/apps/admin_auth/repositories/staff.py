from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one


def find_sy_user_by_login_name(login_name: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            id, user_name, true_name, user_password, user_status,
            dept_id, type, show_type, user_type_role_id, mobile_phone_number,
            email, is_czqx, account_type, pt_type, utoo_type, utoo_show_type
        FROM sy_users
        WHERE user_name = %(login_name)s
        LIMIT 1
        """,
        {"login_name": login_name},
    )


def find_user_roles(user_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT r.id, r.role_name, r.role_desc
        FROM sy_role r
        INNER JOIN sy_user_role ur ON ur.role_id = r.id
        WHERE ur.user_id = %(user_id)s
        """,
        {"user_id": user_id},
    )


def find_dept_name(dept_id: str | None) -> str | None:
    if not dept_id:
        return None
    row = fetch_one(
        "SELECT dept_name FROM sy_dept WHERE id = %(dept_id)s LIMIT 1",
        {"dept_id": dept_id},
    )
    return row.get("dept_name") if row else None


def update_login_success(user_id: str, login_ip: str) -> None:
    from apps.core.db_utils import execute

    execute(
        """
        UPDATE sy_users
        SET last_login_ip = %(login_ip)s,
            last_login_time = NOW(),
            error_count = 0
        WHERE id = %(user_id)s
        """,
        {"user_id": user_id, "login_ip": login_ip},
    )


def fetch_top_level_menus(user_id: str) -> list[dict[str, Any]]:
    """对齐 Java MenuMapper.findmenuformainnotdev"""
    return fetch_all(
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
            m.menu_sort
        FROM sy_role_menu rm
        INNER JOIN sy_menu m ON rm.menu_id = m.id
        INNER JOIN sy_user_role ur ON ur.role_id = rm.role_id
        INNER JOIN sy_role r ON r.id = ur.role_id
        WHERE ur.user_id = %(user_id)s
          AND m.menu_super_id = '0'
          AND m.menu_status = 1
          AND r.type = 2
          AND m.pt_type LIKE '%%2%%'
        ORDER BY m.menu_sort ASC, m.id ASC
        """,
        {"user_id": user_id},
    )


def fetch_user_menus(user_id: str) -> list[dict[str, Any]]:
    """对齐 Java MenuMapper.findSyMenubyuserid"""
    return fetch_all(
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
            m.menu_sort
        FROM sy_role_menu rm
        INNER JOIN sy_menu m ON rm.menu_id = m.id
        INNER JOIN sy_user_role ur ON ur.role_id = rm.role_id
        INNER JOIN sy_role r ON r.id = ur.role_id
        WHERE ur.user_id = %(user_id)s
          AND m.menu_status = 1
          AND r.type = 2
          AND m.pt_type LIKE '%%2%%'
        ORDER BY m.menu_sort ASC, m.id ASC
        """,
        {"user_id": user_id},
    )


def serialize_sy_user(row: dict[str, Any]) -> dict[str, Any]:
    """对齐 Java /vue/usercenter.ajax 返回的 SyUsers 字段。"""
    return {
        "id": str(row.get("id") or ""),
        "userName": row.get("user_name") or "",
        "trueName": row.get("true_name") or "",
        "email": row.get("email") or "",
        "mobilePhoneNumber": row.get("mobile_phone_number") or "",
        "deptId": str(row.get("dept_id") or ""),
        "type": row.get("type") or "",
        "utooType": row.get("utoo_type") or "",
        "userStatus": row.get("user_status"),
        "accountType": row.get("account_type"),
        "ptType": row.get("pt_type") or "",
    }


def fetch_top_menus(user_id: str) -> list[dict[str, Any]]:
    """Deprecated: use services.menu.select_menus_top"""
    from apps.admin_auth.services import menu as menu_service

    return menu_service.select_menus_top(user_id)
