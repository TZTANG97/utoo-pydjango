"""小程序资料 / 绑定状态 — Ajax 形态。"""
from __future__ import annotations

import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.models import ExpUser
from apps.auth_pc.services.customer import CustomerUserService
from apps.auth_pc.services.profile import UserProfileService
from apps.auth_pc.views import get_current_user_from_request, is_exp_customer
from apps.core.db_utils import fetch_one
from apps.core.responses import ajax_fail, ajax_ok
from apps.core.services import banner as banner_svc
from apps.orders.services import catalog as catalog_svc
from apps.wx_mp.services import mp_user

logger = logging.getLogger(__name__)


def _require_user(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return None, Response(ajax_fail("用户未登录"))
    return user, None


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_identify_data(request: Request):
    current, err = _require_user(request)
    if err:
        return err
    if not is_exp_customer(current):
        return Response(ajax_fail("注册用户不存在！"))
    try:
        user = CustomerUserService.get_by_id(int(current["user_id"]))
        if not user:
            return Response(ajax_fail("注册用户不存在！"))
        payload = CustomerUserService.build_identify_payload(
            user, avatar=UserProfileService.avatar_url(user.photo_id)
        )
        # 对齐 Java 字段名
        data = {
            "userType": user.userType or 1,
            "company_name": user.company_name or "",
            "trueName": user.trueName or "",
            "mobile": user.mobile or "",
            "email": user.email or "",
            "idcard": user.idcard or "",
            "area_id": user.area_id or "",
            "address": user.address_info or "",
        }
        data.update({k: v for k, v in payload.items() if k not in data})
        return Response(ajax_ok(data, "获取认证数据成功!"))
    except DatabaseError as exc:
        logger.exception("getIdentifyData db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def clear_bind_data(request: Request):
    current, err = _require_user(request)
    if err:
        return err
    if not is_exp_customer(current):
        return Response(ajax_fail("用户未登录"))
    try:
        uid = int(current["user_id"])
        ExpUser.objects.filter(pk=uid).update(
            area_id=None,
            company_name=None,
            trueName=None,
            email=None,
            idcard=None,
            address_info=None,
            is_identify=0,
            userType=1,
            parent_id=None,
        )
        return Response(ajax_ok(None, "清空认证数据成功!"))
    except DatabaseError as exc:
        logger.exception("clearBindData db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def my_info(request: Request):
    current, err = _require_user(request)
    if err:
        return err
    try:
        if is_exp_customer(current):
            user = CustomerUserService.get_by_id(int(current["user_id"]))
            if not user:
                return Response(ajax_fail("用户不存在"))
            return Response(ajax_ok(mp_user.issue_exp_login_obj(user), "获取成功"))
        row = fetch_one(
            """
            SELECT id, user_name, true_name, user_password, mobile_phone_number,
                   type, utoo_type, is_bind_account, dept_id
            FROM sy_users WHERE id = %(id)s LIMIT 1
            """,
            {"id": current["user_id"]},
        )
        if not row:
            return Response(ajax_fail("用户不存在"))
        return Response(ajax_ok(mp_user.issue_sy_login_obj(row), "获取成功"))
    except DatabaseError as exc:
        logger.exception("myInfo db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_bind_status(request: Request):
    current, err = _require_user(request)
    if err:
        return err
    try:
        if is_exp_customer(current):
            row = fetch_one(
                "SELECT is_bind_account FROM exp_user WHERE id = %(id)s LIMIT 1",
                {"id": current["user_id"]},
            )
            is_bind = int(row["is_bind_account"]) if row and row.get("is_bind_account") is not None else 0
        else:
            row = fetch_one(
                "SELECT is_bind_account FROM sy_users WHERE id = %(id)s LIMIT 1",
                {"id": current["user_id"]},
            )
            is_bind = int(row["is_bind_account"]) if row and row.get("is_bind_account") is not None else 0
        return Response(ajax_ok({"is_bind": is_bind}, "查询成功！"))
    except DatabaseError as exc:
        logger.exception("getbindstatus db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def check_login_name(request: Request):
    """简单可用性检查。"""
    name = (request.query_params.get("loginName") or request.query_params.get("userName") or "").strip()
    if not name:
        return Response(ajax_fail("参数错误"))
    exists = ExpUser.objects.filter(userName=name, deleteStatus=0).exists()
    return Response(ajax_ok({"exists": exists}, "ok"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_nick_name(request: Request):
    current, err = _require_user(request)
    if err:
        return err
    if not is_exp_customer(current):
        return Response(ajax_fail("仅支持 C 端用户"))
    body = request.data if isinstance(request.data, dict) else {}
    nick = (
        request.query_params.get("wx_nickname")
        or request.query_params.get("nickName")
        or body.get("wx_nickname")
        or body.get("nickName")
        or ""
    )
    nick = str(nick).strip()
    if not nick:
        return Response(ajax_fail("昵称不能为空"))
    ExpUser.objects.filter(pk=int(current["user_id"])).update(wx_nickname=nick)
    return Response(ajax_ok(None, "修改成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def tuzhe_banner_list(request: Request):
    del request
    data = banner_svc.list_pc_banners()
    if not data:
        return Response(ajax_fail("暂无轮播图"))
    return Response(ajax_ok(data))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def sel_fir_and_sec_class_list_tuzhe(request: Request):
    del request
    data = catalog_svc.sel_fir_and_sec_class_list()
    return Response(ajax_ok(data, "获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def bind_account_stub(request: Request):
    del request
    return Response(ajax_fail("扫码绑定尚未在 Django 网关实现，请暂用账号密码/验证码登录"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def secure_bind_stub(request: Request):
    del request
    return Response(ajax_fail("安全绑定尚未在 Django 网关实现"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_user_info_stub(request: Request):
    """扫码登录一键授权：复杂依赖公众号 ticket，暂返回明确错误。"""
    del request
    return Response(ajax_fail("扫码 getUserInfo 尚未在 Django 网关实现，请使用手机号快捷登录"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def not_implemented(request: Request):
    name = request.path.rsplit("/", 1)[-1]
    return Response(ajax_fail(f"接口暂未实现: {name}"))
