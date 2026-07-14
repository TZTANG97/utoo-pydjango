from __future__ import annotations

from typing import Any

from apps.admin_auth.repositories import staff as staff_repo


def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java IndexViewController.welcome.htm 的 userType 粗分。"""
    role = (utoo_type or "").strip()
    if not role:
        return 0
    if "系统管理员" in role or role.upper() == "ADMIN":
        return 1
    if "公司" in role:
        return 2
    if "销售主管" in role:
        return 3
    if "销售" in role or "原厂" in role:
        return 4
    if "制单" in role:
        return 5
    if "投资" in role:
        return 6
    if "仓库" in role:
        return 7
    if role.startswith("H") or "H类" in role:
        return 14
    return 0


def build_welcome_payload(user: dict[str, Any]) -> dict[str, Any]:
    user_id = str(user.get("user_id") or "")
    utoo_type = user.get("utoo_type") or user.get("type")
    user_type = _resolve_welcome_user_type(str(utoo_type) if utoo_type else None)
    dept_name = staff_repo.find_dept_name(user.get("dept_id"))
    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": user.get("user_name") or "",
        "userType": user_type,
        "roleName": user.get("type") or user.get("utoo_type") or "",
        "deptName": dept_name or "",
        "email": user.get("email") or "",
        "mobilePhoneNumber": user.get("mobile_phone_number") or "",
        "menuCount": len(staff_repo.fetch_user_menus(user_id)),
    }
