"""找回密码 — getVerifyCodeFindPw / telCodeVerify"""
from __future__ import annotations

from apps.auth_pc.models import ExpUser
from apps.auth_pc.services import verify_code as verify_svc
from apps.auth_pc.services.customer import CustomerUserService
from qd_common.password_java import encrypt_password_for_storage


def send_find_password_code(telephone: str) -> tuple[bool, str]:
    if not telephone:
        return False, "手机号不能为空！"
    if not verify_svc.mobile_registered(telephone):
        return False, "注册用户不存在！"
    return verify_svc.send_find_password_code(telephone)


def reset_password_with_sms(
    *,
    telephone: str,
    tel_code: str,
    password: str,
    password1: str,
) -> tuple[bool, str]:
    if not telephone:
        return False, "手机号不能为空！"
    if not password:
        return False, "密码不能为空！"
    if password != password1:
        return False, "两次输入密码不一致！"
    if not tel_code:
        return False, "短信验证码不能为空！"

    user = CustomerUserService.find_by_login_name(telephone)
    if not user:
        return False, "注册用户不存在！"
    if not verify_svc.verify_find_password_code(telephone, tel_code):
        return False, "短信验证码错误！"

    verify_svc.clear_find_password_code(telephone)
    ExpUser.objects.filter(pk=user.pk).update(
        password=encrypt_password_for_storage(password)
    )
    return True, "密码重置成功!"
