"""小程序用户登录载荷 — 对齐 Java WxController AjaxRes.obj。"""
from __future__ import annotations

import random
import string
from datetime import datetime
from typing import Any

from apps.admin_auth.repositories import staff as staff_repo
from apps.auth_pc.jwt_tokens import create_access_token, create_refresh_token
from apps.auth_pc.models import ExpUser
from apps.auth_pc.services.customer import CustomerUserService
from apps.auth_pc.services.profile import UserProfileService
from apps.core.db_utils import execute_insert, fetch_one
from qd_common.password_java import encrypt_password_for_storage, verify_password


def _random_nick(n: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "wx_" + "".join(random.choice(chars) for _ in range(n))


def find_exp_by_mobile(mobile: str) -> ExpUser | None:
    return ExpUser.objects.filter(mobile=mobile, deleteStatus=0).first()


def find_sy_by_mobile(mobile: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, user_name, true_name, user_password, mobile_phone_number,
               type, utoo_type, is_bind_account
        FROM sy_users
        WHERE mobile_phone_number = %(m)s
        LIMIT 1
        """,
        {"m": mobile},
    )


def find_sy_by_login(login_name: str) -> dict[str, Any] | None:
    return staff_repo.find_sy_user_by_login_name(login_name)


def create_exp_user(mobile: str) -> ExpUser:
    nick = _random_nick()
    pwd = encrypt_password_for_storage("123456")
    # 部分环境 ORM create 缺 addTime 列映射，用 SQL 插入
    new_id = execute_insert(
        """
        INSERT INTO exp_user
            (addTime, deleteStatus, password, mobile, userType, wx_nickname, is_identify)
        VALUES
            (%(t)s, 0, %(pwd)s, %(mobile)s, 1, %(nick)s, 0)
        """,
        {"t": datetime.now(), "pwd": pwd, "mobile": mobile, "nick": nick},
    )
    user = ExpUser.objects.filter(pk=new_id).first()
    if user:
        return user
    return find_exp_by_mobile(mobile)  # type: ignore[return-value]


def _is_bind(user: ExpUser) -> int:
    row = fetch_one(
        "SELECT is_bind_account FROM exp_user WHERE id = %(id)s LIMIT 1",
        {"id": user.id},
    )
    if not row:
        return 0
    v = row.get("is_bind_account")
    return int(v) if v is not None else 0


def issue_exp_login_obj(user: ExpUser) -> dict[str, Any]:
    token_data = CustomerUserService.exp_user_token_data(user)
    access = create_access_token(token_data)
    create_refresh_token({"user_id": str(user.id), "account_kind": "exp_user"})
    photo = UserProfileService.avatar_url(user.photo_id)
    return {
        "token": access,
        "photo": photo,
        "wx_nickname": user.wx_nickname or user.userName or "",
        "mobile": user.mobile or "",
        "userType": user.userType or 1,
        "roleName": "",
        "uType": 0,
        "userId": user.id,
        "is_bind_account": _is_bind(user),
    }


def issue_sy_login_obj(row: dict[str, Any]) -> dict[str, Any]:
    uid = str(row["id"])
    token_data = {
        "user_id": uid,
        "user_name": row.get("user_name") or "",
        "true_name": row.get("true_name") or row.get("user_name") or "",
        "user_type": "0",
        "dept_id": str(row.get("dept_id") or ""),
        "dept_name": "",
        "role_ids": [],
        "account_kind": "sy_user",
    }
    access = create_access_token(token_data)
    create_refresh_token({"user_id": uid, "account_kind": "sy_user"})
    return {
        "token": access,
        "photo": "",
        "wx_nickname": row.get("user_name") or "",
        "mobile": row.get("mobile_phone_number") or "",
        "userType": row.get("type"),
        "roleName": "",
        "uType": 1,
        "userId": row["id"],
        "is_bind_account": int(row.get("is_bind_account") or 0),
    }


def login_by_password(login_name: str, password: str) -> tuple[bool, str, dict | None]:
    if not login_name or not password:
        return False, "用户名或密码不能为空", None

    user = CustomerUserService.find_by_login_name(login_name)
    if user:
        ok, scheme = verify_password(password, user.password or "")
        if not ok:
            return False, "密码错误", None
        if scheme in ("std_hex_md5", "plaintext"):
            CustomerUserService.rehash_password_if_legacy(user, password)
        return True, "登录成功", issue_exp_login_obj(user)

    sy = find_sy_by_login(login_name)
    if sy:
        ok, _ = verify_password(password, sy.get("user_password") or "")
        if not ok:
            return False, "密码错误", None
        return True, "登录成功", issue_sy_login_obj(sy)

    return False, "用户不存在", None


def login_by_mobile(mobile: str, *, auto_register: bool = True) -> tuple[bool, str, dict | None]:
    if not mobile:
        return False, "手机号不能为空！", None
    user = find_exp_by_mobile(mobile)
    if user:
        return True, "登录成功", issue_exp_login_obj(user)
    sy = find_sy_by_mobile(mobile)
    if sy:
        return True, "登录成功", issue_sy_login_obj(sy)
    if not auto_register:
        return False, "用户不存在", None
    user = create_exp_user(mobile)
    if not user:
        return False, "注册失败", None
    return True, "登录成功", issue_exp_login_obj(user)
