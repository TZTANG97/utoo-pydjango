"""C 端注册 — 对齐 register.ajax"""
from __future__ import annotations

from datetime import datetime

from apps.auth_pc.models import ExpUser
from apps.auth_pc.services import verify_code as verify_svc
from qd_common.password_java import encrypt_password_for_storage


def register(
    *,
    code: str,
    mobile: str,
    user_name: str,
    company_name: str,
    password1: str,
    password2: str,
) -> tuple[bool, str]:
    if not code:
        return False, "验证码不能为空"
    if not mobile:
        return False, "手机号不能为空"
    if not user_name:
        return False, "用户名不能为空"
    if not password1 or not password2:
        return False, "密码不能为空"
    if password1 != password2:
        return False, "两次输入密码不一致"
    if not company_name:
        return False, "公司名称不能为空"

    if ExpUser.objects.filter(userName=user_name, deleteStatus=0).exists():
        return False, "用户名已存在"
    if ExpUser.objects.filter(mobile=mobile, deleteStatus=0).exists():
        return False, "手机号已注册"
    if not verify_svc.verify_register_code(mobile, code):
        return False, "短信验证码错误"

    ExpUser.objects.create(
        addTime=datetime.now(),
        deleteStatus=0,
        userName=user_name,
        company_name=company_name,
        password=encrypt_password_for_storage(password1),
        mobile=mobile,
        userType=1,
        wx_nickname=user_name,
        is_identify=0,
    )
    return True, "注册成功"
