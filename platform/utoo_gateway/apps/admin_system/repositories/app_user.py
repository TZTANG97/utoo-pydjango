from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import fetch_all, fetch_one, scalar


def list_app_users(
    *,
    user_name: str = "",
    mobile_phone_number: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if user_name:
        where += " AND user_name LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if mobile_phone_number:
        where += " AND mobile_phone_number LIKE %(mobile)s"
        params["mobile"] = f"%{mobile_phone_number}%"
    total = scalar(f"SELECT COUNT(*) FROM app_user {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, user_name, true_name, mobile_phone_number, email,
               company_name, register_time, wx_openid, wx_nickname, wx_avatar
        FROM app_user
        {where}
        ORDER BY register_time DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_app_user(row) for row in rows], int(total)


def get_app_user(user_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, user_name, true_name, mobile_phone_number, email,
               company_name, register_time, wx_openid, wx_nickname, wx_avatar,
               wx_unionid, wx_phonenum, user_status
        FROM app_user WHERE id = %(id)s
        """,
        {"id": user_id},
    )
    return _normalize_app_user(row) if row else None


def _normalize_app_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "userName": row.get("user_name"),
        "trueName": row.get("true_name"),
        "mobilePhoneNumber": row.get("mobile_phone_number"),
        "email": row.get("email"),
        "companyName": row.get("company_name"),
        "registerTime": row.get("register_time"),
        "wxOpenid": row.get("wx_openid"),
        "wxNickname": row.get("wx_nickname"),
        "wxAvatar": row.get("wx_avatar"),
        "wxUnionid": row.get("wx_unionid"),
        "wxPhonenum": row.get("wx_phonenum"),
        "userStatus": row.get("user_status"),
    }
