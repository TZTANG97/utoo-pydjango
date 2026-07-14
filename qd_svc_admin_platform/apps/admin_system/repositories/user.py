from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from qd_common.password_java import encrypt_password_for_storage


def list_users(
    *,
    dept_id: str = "",
    user_name: str = "",
    true_name: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if dept_id and dept_id != "0":
        where += " AND u.dept_id = %(dept_id)s"
        params["dept_id"] = dept_id
    if user_name:
        where += " AND u.user_name LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if true_name:
        where += " AND u.true_name LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    total = scalar(f"SELECT COUNT(*) FROM sy_users u {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT u.id, u.user_name, u.true_name, u.user_status, u.dept_id,
               u.mobile_phone_number, u.email, u.type, u.show_type,
               d.dept_name
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        {where}
        ORDER BY u.user_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_user(row) for row in rows], int(total)


def get_user(user_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, user_name, true_name, user_status, dept_id, mobile_phone_number,
               email, type, show_type, user_type_role_id, user_desc, helper_id
        FROM sy_users WHERE id = %(id)s
        """,
        {"id": user_id},
    )
    if not row:
        return None
    user = _normalize_user(row)
    user["roleIds"] = get_user_role_ids(user_id)
    return user


def find_by_login_name(login_name: str) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, user_name FROM sy_users WHERE user_name = %(name)s LIMIT 1",
        {"name": login_name},
    )


def insert_user(data: dict[str, Any]) -> str:
    user_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_users
            (id, user_name, true_name, user_password, user_status, dept_id,
             mobile_phone_number, email, type, show_type, user_type_role_id,
             user_desc, pt_type, account_type)
        VALUES
            (%(id)s, %(user_name)s, %(true_name)s, %(user_password)s, %(user_status)s,
             %(dept_id)s, %(mobile_phone_number)s, %(email)s, %(type)s, %(show_type)s,
             %(user_type_role_id)s, %(user_desc)s, '2', 0)
        """,
        {
            "id": user_id,
            "user_name": data.get("user_name") or "",
            "true_name": data.get("true_name") or "",
            "user_password": encrypt_password_for_storage(data.get("user_password") or "123456"),
            "user_status": int(data.get("user_status") or 1),
            "dept_id": data.get("dept_id") or "0",
            "mobile_phone_number": data.get("mobile_phone_number"),
            "email": data.get("email"),
            "type": data.get("type"),
            "show_type": data.get("show_type"),
            "user_type_role_id": data.get("user_type_role_id"),
            "user_desc": data.get("user_desc"),
        },
    )
    return user_id


def update_user(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_users
        SET user_name = %(user_name)s,
            true_name = %(true_name)s,
            user_status = %(user_status)s,
            dept_id = %(dept_id)s,
            mobile_phone_number = %(mobile_phone_number)s,
            email = %(email)s,
            type = %(type)s,
            show_type = %(show_type)s,
            user_type_role_id = %(user_type_role_id)s,
            user_desc = %(user_desc)s
        WHERE id = %(id)s
        """,
        data,
    )


def disable_user(user_id: str) -> None:
    execute(
        "UPDATE sy_users SET user_status = 0 WHERE id = %(id)s",
        {"id": user_id},
    )


def get_user_role_ids(user_id: str) -> list[str]:
    rows = fetch_all(
        "SELECT role_id FROM sy_user_role WHERE user_id = %(user_id)s",
        {"user_id": user_id},
    )
    return [str(r["role_id"]) for r in rows if r.get("role_id")]


def set_user_roles(user_id: str, role_ids: list[str]) -> None:
    execute("DELETE FROM sy_user_role WHERE user_id = %(user_id)s", {"user_id": user_id})
    for role_id in role_ids:
        if role_id:
            execute_insert(
                "INSERT INTO sy_user_role (user_id, role_id) VALUES (%(user_id)s, %(role_id)s)",
                {"user_id": user_id, "role_id": role_id},
            )


def list_role_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, role_name, role_desc
        FROM sy_role
        WHERE type = 2 OR type IS NULL
        ORDER BY role_name ASC
        """
    )
    return [
        {"id": r["id"], "roleName": r.get("role_name"), "roleDesc": r.get("role_desc")}
        for r in rows
    ]


def _normalize_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "userName": row.get("user_name"),
        "trueName": row.get("true_name"),
        "userStatus": row.get("user_status"),
        "deptId": row.get("dept_id"),
        "deptName": row.get("dept_name"),
        "mobilePhoneNumber": row.get("mobile_phone_number"),
        "email": row.get("email"),
        "type": row.get("type"),
        "showType": row.get("show_type"),
        "userTypeRoleId": row.get("user_type_role_id"),
        "userDesc": row.get("user_desc"),
        "helperId": row.get("helper_id"),
    }
