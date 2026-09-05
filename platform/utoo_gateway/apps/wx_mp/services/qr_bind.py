"""PC 扫码后小程序补资料 — getUserInfo / userInfoAdd / ticketIsExist。

过渡 twin：启用 utoo_biz 时路由已指向 payment :18084（与扫码 ticket Redis 同进程）。
未开 biz 时网关仍可本地承接；请勿再扩展本文件写库逻辑。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import unquote

from apps.auth_pc.authentication import decode_access_token
from apps.auth_pc.models import ExpUser
from apps.auth_pc.services.customer import CustomerUserService
from apps.core import redis_client
from apps.core.db_utils import execute, execute_insert
from apps.wx.repositories import wx_openid_info as temp_repo
from apps.wx_mp.services import mp_user, wechat_phone
from qd_common.password_java import encrypt_password_for_storage

logger = logging.getLogger(__name__)


def _decode_ticket(ticket: str) -> str:
    if not ticket:
        return ""
    try:
        return unquote(ticket)
    except Exception:
        return ticket


def ticket_is_exist(ticket: str) -> tuple[bool, str]:
    t = _decode_ticket(ticket)
    if not t:
        return False, "ticket 不能为空"
    if redis_client.key_exists(t):
        return True, "ok"
    return False, "二维码已过期"


def get_user_info(
    *,
    code: str,
    openid: str,
    ticket: str,
) -> tuple[bool, str, dict | None]:
    t = _decode_ticket(ticket)
    if not t or not redis_client.key_exists(t):
        return False, "二维码已过期", None
    ok_phone, msg_phone, mobile = wechat_phone.get_phone_number(code, brand="utoo")
    if not ok_phone or not mobile:
        return False, msg_phone or "获取的电话为空", None

    user = mp_user.find_exp_by_mobile(mobile)
    if user:
        return True, "ok", mp_user.issue_exp_login_obj(user)

    sy = mp_user.find_sy_by_mobile(mobile)
    if sy:
        return True, "ok", mp_user.issue_sy_login_obj(sy)

    # 注册新 C 端用户（对齐 Java MD5("123456") + wx_nickname）
    user = mp_user.create_exp_user(mobile)
    if not user:
        return False, "注册失败", None
    return True, "ok", mp_user.issue_exp_login_obj(user)


def _user_from_token(token: str) -> ExpUser | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    if not payload or payload.get("account_kind") == "sy_user":
        return None
    uid = payload.get("user_id")
    if not uid:
        return None
    try:
        return CustomerUserService.get_by_id(int(uid))
    except (TypeError, ValueError):
        return None


def _update_exp_profile(
    user_id: int,
    *,
    name: str,
    work: str,
    openid: str,
    mobile: str | None = None,
    unionid: str = "",
) -> None:
    sets = [
        "trueName = %(name)s",
        "job = %(work)s",
        "wx_openid = %(openid)s",
        "is_bind_account = 1",
    ]
    params: dict[str, Any] = {
        "id": user_id,
        "name": name,
        "work": work,
        "openid": openid,
    }
    if mobile:
        sets.append("mobile = %(mobile)s")
        params["mobile"] = mobile
    if unionid:
        sets.append("wx_unionid = %(unionid)s")
        params["unionid"] = unionid
    sql = f"UPDATE exp_user SET {', '.join(sets)} WHERE id = %(id)s"
    execute(sql, params)


def user_info_add(
    *,
    openid: str,
    name: str,
    work: str,
    mobile: str,
    ticket: str,
    token: str = "",
) -> tuple[bool, str]:
    t = _decode_ticket(ticket)
    if not t or not redis_client.key_exists(t):
        return False, "二维码已过期"

    openid = (openid or "").strip()
    name = (name or "").strip()
    work = (work or "").strip()
    mobile = (mobile or "").strip()
    unionid = temp_repo.get_unionid_by_gzh_openid(openid) or ""

    if mobile:
        if token:
            user = _user_from_token(token)
            if user is None:
                return False, "token非法"
            _update_exp_profile(
                int(user.id),
                name=name,
                work=work,
                openid=openid,
                unionid=unionid,
            )
            redis_client.set_string(openid, user.mobile or mobile, ex=180)
            return True, "ok"

        existing = mp_user.find_exp_by_mobile(mobile)
        if existing:
            _update_exp_profile(
                int(existing.id),
                name=name,
                work=work,
                openid=openid,
                mobile=mobile,
                unionid=unionid,
            )
            redis_client.set_string(openid, mobile, ex=180)
            return True, "ok"

        # 新建完整用户
        pwd = encrypt_password_for_storage("123456")
        nick = mp_user._random_nick()  # noqa: SLF001
        new_id = execute_insert(
            """
            INSERT INTO exp_user
                (addTime, deleteStatus, password, mobile, userType, wx_nickname,
                 trueName, job, wx_openid, wx_unionid, is_bind_account, is_identify)
            VALUES
                (%(t)s, 0, %(pwd)s, %(mobile)s, 1, %(nick)s,
                 %(name)s, %(work)s, %(openid)s, %(unionid)s, 1, 0)
            """,
            {
                "t": datetime.now(),
                "pwd": pwd,
                "mobile": mobile,
                "nick": nick,
                "name": name,
                "work": work,
                "openid": openid,
                "unionid": unionid or None,
            },
        )
        if not new_id:
            return False, "保存失败"
        redis_client.set_string(openid, mobile, ex=180)
        return True, "ok"

    # mobile 为空：仅凭 token 补资料
    if not token:
        return False, "mobile 或 token 不能为空"
    user = _user_from_token(token)
    if user is None:
        return False, "token非法"
    _update_exp_profile(
        int(user.id),
        name=name,
        work=work,
        openid=openid,
        unionid=unionid,
    )
    if user.mobile:
        redis_client.set_string(openid, user.mobile, ex=180)
    return True, "ok"
