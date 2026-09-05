from __future__ import annotations

from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.auth_pc.jwt_tokens import create_access_token, create_refresh_token
from qd_common.password_java import verify_password


def _resolve_user_type(row: dict[str, Any]) -> int:
    """对齐 Java VueController：0 admin, 1 public, 2 外部公司, 3 内部公司"""
    account_type = row.get("account_type")
    if account_type == 1:
        return 3
    return 0


def build_staff_token_data(row: dict[str, Any]) -> dict[str, Any]:
    roles = staff_repo.find_user_roles(str(row["id"]))
    role_ids = [str(r["id"]) for r in roles if r.get("id") is not None]
    dept_name = staff_repo.find_dept_name(row.get("dept_id"))
    return {
        "user_id": str(row["id"]),
        "user_name": row.get("user_name") or "",
        "true_name": row.get("true_name") or "",
        "user_type": "0",
        "dept_id": str(row.get("dept_id") or ""),
        "dept_name": dept_name or "",
        "role_ids": role_ids,
        "account_kind": "sy_user",
    }


def authenticate_staff(login_name: str, password: str) -> tuple[dict[str, Any] | None, str]:
    row = staff_repo.find_sy_user_by_login_name(login_name)
    if not row:
        return None, "登录失败,请确认是否有此平台登录权限!"

    if int(row.get("user_status") or 0) == 0:
        return None, "用户被限制登录，请联系管理员"

    ok, _scheme = verify_password(password, row.get("user_password") or "")
    if not ok:
        return None, "用户名或密码错误，请重新登录"

    token_data = build_staff_token_data(row)
    access = create_access_token(token_data)
    refresh = create_refresh_token(
        {"user_id": token_data["user_id"], "account_kind": "sy_user"}
    )
    payload = {
        "userType": _resolve_user_type(row),
        "token": access,
        "refreshToken": refresh,
        "userName": row.get("true_name") or row.get("user_name") or "",
        "loginName": row.get("user_name") or "",
    }
    if row.get("type"):
        payload["uRoleName"] = str(row.get("type"))
    return payload, ""
