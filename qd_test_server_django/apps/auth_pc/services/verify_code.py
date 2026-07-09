"""验证码 — 对齐 Java getVerifyCode / 找回密码短信"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta

from django.conf import settings

from apps.auth_pc.models import ExpUser
from apps.core.db_utils import execute, execute_insert, fetch_one

logger = logging.getLogger(__name__)

USER_TYPE_REGISTER = "phone_code_new"
USER_TYPE_FIND_PW = "find_pw"


def mobile_registered(mobile: str) -> bool:
    return ExpUser.objects.filter(mobile=mobile, deleteStatus=0).exists()


def _dev_code() -> str:
    return getattr(settings, "DEV_SMS_CODE", "111111")


def _is_dev() -> bool:
    return getattr(settings, "APP_ENV", "development") == "development"


def _insert_code(telephone: str, user_type: str) -> tuple[bool, str]:
    code = _dev_code() if _is_dev() else f"{random.randint(100000, 999999)}"
    now = datetime.now()
    execute_insert(
        """
        INSERT INTO verify_code
            (addTime, deleteStatus, receiver_type, receiver, user_type,
             user_status, deadline, code)
        VALUES
            (%(t)s, 0, 'mobile', %(tel)s, %(ut)s, 0, %(dl)s, %(code)s)
        """,
        {
            "t": now,
            "tel": telephone,
            "ut": user_type,
            "dl": now + timedelta(minutes=10),
            "code": code,
        },
    )
    if _is_dev():
        logger.info("dev sms code [%s] for %s: %s", user_type, telephone, code)
    return True, "发送成功"


def send_register_code(telephone: str) -> tuple[bool, str]:
    if not telephone:
        return False, "手机号不能为空！"
    if mobile_registered(telephone):
        return False, "手机号已注册！"
    return _insert_code(telephone, USER_TYPE_REGISTER)


def verify_register_code(mobile: str, code: str) -> bool:
    if _is_dev() and code == _dev_code():
        return True
    row = fetch_one(
        """
        SELECT code FROM verify_code
        WHERE addTime = (
            SELECT MAX(addTime) FROM verify_code
            WHERE receiver = %(tel)s AND user_type = %(ut)s
        )
        AND receiver = %(tel)s AND user_type = %(ut)s
        LIMIT 1
        """,
        {"tel": mobile, "ut": USER_TYPE_REGISTER},
    )
    return bool(row and row.get("code") == code)


def send_find_password_code(telephone: str) -> tuple[bool, str]:
    return _insert_code(telephone, USER_TYPE_FIND_PW)


def verify_find_password_code(mobile: str, code: str) -> bool:
    if _is_dev() and code == _dev_code():
        return True
    row = fetch_one(
        """
        SELECT code FROM verify_code
        WHERE addTime = (
            SELECT MAX(addTime) FROM verify_code
            WHERE receiver = %(tel)s AND user_type = %(ut)s
        )
        AND receiver = %(tel)s AND user_type = %(ut)s
        LIMIT 1
        """,
        {"tel": mobile, "ut": USER_TYPE_FIND_PW},
    )
    return bool(row and row.get("code") == code)


def clear_find_password_code(telephone: str) -> None:
    execute(
        """
        UPDATE verify_code SET code = ''
        WHERE id = (
            SELECT id FROM (
                SELECT id FROM verify_code
                WHERE receiver = %(tel)s AND user_type = %(ut)s
                ORDER BY addTime DESC LIMIT 1
            ) AS t
        )
        """,
        {"tel": telephone, "ut": USER_TYPE_FIND_PW},
    )
