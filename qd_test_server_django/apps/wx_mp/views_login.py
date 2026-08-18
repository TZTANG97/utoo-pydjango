"""小程序登录相关 — 对齐 Java WxController 登录接口（Ajax res/obj）。"""
from __future__ import annotations

import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.responses import ajax_fail, ajax_ok
from apps.core.svc_proxy import identity_password_login, svc_identity_enabled
from apps.wx_mp.services import mp_user, verify_login, wechat_phone

logger = logging.getLogger(__name__)


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_verify_code_login(request: Request):
    telephone = _param(request, "telephone")
    try:
        ok, msg = verify_login.send_login_code(telephone)
    except DatabaseError as exc:
        logger.exception("getVerifyCodeLogin db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
    if ok:
        return Response(ajax_ok(None, msg))
    return Response(ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def user_login_token(request: Request):
    login_name = _param(request, "loginName")
    password = _param(request, "password")
    if svc_identity_enabled():
        try:
            result = identity_password_login(login_name, password, channel="wx")
        except Exception as exc:
            logger.exception("identity mid login failed: %s", exc)
            return Response(ajax_fail("身份中台不可用"))
        body = result.get("body") or {}
        if body.get("code") == 0:
            data = body.get("data") or {}
            obj = {
                "token": data.get("token"),
                "photo": data.get("photo") or data.get("avatar") or "",
                "wx_nickname": data.get("wx_nickname") or data.get("nickName") or "",
                "mobile": data.get("mobile") or data.get("phone") or "",
                "userType": data.get("userType") or 1,
                "roleName": "",
                "uType": data.get("uType") if data.get("uType") is not None else 0,
                "userId": data.get("userId"),
                "is_bind_account": 0,
            }
            return Response(ajax_ok(obj, body.get("message") or "登录成功"))
        msg = body.get("message") or "登录失败"
        if "未注册" not in msg and "不存在" not in msg:
            return Response(ajax_fail(msg))
    try:
        ok, msg, obj = mp_user.login_by_password(login_name, password)
    except DatabaseError as exc:
        logger.exception("userLoginToken db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
    if ok:
        return Response(ajax_ok(obj, msg))
    return Response(ajax_fail(msg, obj or {}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def phone_code_login(request: Request):
    telephone = _param(request, "telephone")
    code = _param(request, "code")
    if not telephone:
        return Response(ajax_fail("手机号不能为空！"))
    if not code:
        return Response(ajax_fail("验证码不能为空！"))
    try:
        if not verify_login.verify_login_code(telephone, code):
            return Response(ajax_fail("验证码不正确！"))
        ok, msg, obj = mp_user.login_by_mobile(telephone, auto_register=True)
    except DatabaseError as exc:
        logger.exception("phoneCodeLogin db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
    if ok:
        return Response(ajax_ok(obj, msg))
    return Response(ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def phone_one_login(request: Request):
    return _phone_one_login(request, brand="utoo")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def phone_one_login_tz(request: Request):
    return _phone_one_login(request, brand="tz")


def _phone_one_login(request: Request, *, brand: wechat_phone.MpBrand):
    code = _param(request, "code")
    try:
        ok_phone, msg_phone, mobile = wechat_phone.get_phone_number(code, brand=brand)
        if not ok_phone:
            return Response(ajax_fail(msg_phone))
        ok, msg, obj = mp_user.login_by_mobile(mobile, auto_register=True)
    except DatabaseError as exc:
        logger.exception("phoneOneLogin db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
    if ok:
        return Response(ajax_ok(obj, msg))
    return Response(ajax_fail(msg))
