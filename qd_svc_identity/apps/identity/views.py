from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.identity.authentication import IdentityJWTAuthentication, TokenUser
from apps.identity.channel import ChannelError, channel_from_request
from apps.identity.repositories import scope as scope_repo
from apps.identity.services import login as login_svc
from apps.identity.services.customer import CustomerUserService
from qd_common.responses import api_fail, api_ok


def _current_user(request: Request) -> dict | None:
    if hasattr(request, "user") and isinstance(request.user, TokenUser):
        return request.user._payload
    return None


def _login_name(data: dict) -> str:
    return (
        data.get("loginName")
        or data.get("user_name")
        or data.get("userName")
        or data.get("name")
        or data.get("username")
        or ""
    ).strip()


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def auth_login(request: Request):
    try:
        ctx = channel_from_request(request)
    except ChannelError as exc:
        return Response(api_fail(400, str(exc)))

    data = request.data or {}
    name = _login_name(data if isinstance(data, dict) else {})
    password = data.get("password") or ""
    login_type = str(data.get("loginType") or "1").strip()
    if not name or not password:
        return Response(api_fail(400, "用户名或密码不能为空"))
    if ctx.account_kind == "exp_user" and login_type != "1":
        return Response(api_fail(400, "当前仅支持客户登录 loginType=1"))

    try:
        payload, err = login_svc.login(name, password, ctx)
    except DatabaseError:
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if err:
        if ctx.channel == "mall_qd":
            return Response({"detail": err}, status=401)
        return Response(api_fail(401, err))
    if ctx.channel == "mall_qd":
        return Response(payload)
    return Response(api_ok(payload, message="登录成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def auth_refresh(request: Request):
    raw = (request.data or {}).get("refresh_token") or ""
    try:
        payload, err = login_svc.refresh_customer(raw)
    except DatabaseError:
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if err:
        return Response(api_fail(401, err))
    return Response(api_ok(payload, message="刷新成功"))


@api_view(["GET"])
@authentication_classes([IdentityJWTAuthentication])
@permission_classes([AllowAny])
def auth_me(request: Request):
    try:
        ctx = channel_from_request(request)
    except ChannelError as exc:
        return Response(api_fail(400, str(exc)))
    user = _current_user(request)
    if not user:
        return Response(api_fail(401, "未登录"))

    if ctx.account_kind == "exp_user" or user.get("account_kind") == "exp_user":
        db_user = CustomerUserService.get_by_id(int(user.get("user_id") or user.get("sub") or 0))
        if not db_user:
            return Response(api_fail(404, "注册用户不存在！"))
        body = CustomerUserService.build_identify_payload(db_user)
        body["channel"] = ctx.channel
        return Response(api_ok(body, message="获取认证数据成功!"))

    user_id = str(user.get("user_id") or user.get("sub") or "")
    platform = ctx.platform or user.get("platform") or "2"
    permissions = scope_repo.build_permissions(user_id, str(platform))
    scope = user.get("scope") or scope_repo.build_data_scope(
        user_id, str(user.get("type") or ""), str(platform)
    )
    me_user = {
        "id": user_id,
        "user_name": user.get("user_name"),
        "true_name": user.get("true_name"),
        "dept_id": user.get("dept_id"),
        "type": user.get("type"),
        "scope": scope,
        "role_ids": permissions["role_ids"],
        "channel": ctx.channel,
        "platform": platform,
        "accountKind": "sy_user",
    }
    if ctx.channel == "mall_qd":
        return Response({"data": me_user, "permissions": permissions["permissions"]})
    return Response(api_ok(me_user))


@api_view(["GET"])
@authentication_classes([IdentityJWTAuthentication])
@permission_classes([AllowAny])
def menus(request: Request):
    try:
        ctx = channel_from_request(request)
    except ChannelError as exc:
        return Response(api_fail(400, str(exc)))
    user = _current_user(request)
    if not user:
        if ctx.channel == "mall_qd":
            return Response({"detail": "未登录"}, status=401)
        return Response(api_fail(401, "未登录"))
    if not ctx.returns_admin_menus:
        empty = {"menus": [], "channel": ctx.channel, "platform": None}
        if ctx.channel in ("pc", "wx"):
            return Response(api_ok(empty))
        return Response({"data": []})
    user_id = str(user.get("user_id") or user.get("sub") or "")
    try:
        tree = login_svc.build_menu_tree(user_id, ctx)
    except DatabaseError:
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if ctx.channel == "mall_qd":
        return Response({"data": tree})
    return Response(api_ok({"menus": tree, "channel": ctx.channel, "platform": ctx.platform}))


@api_view(["GET"])
@authentication_classes([IdentityJWTAuthentication])
@permission_classes([AllowAny])
def permissions(request: Request):
    try:
        ctx = channel_from_request(request)
    except ChannelError as exc:
        return Response(api_fail(400, str(exc)))
    user = _current_user(request)
    if not user:
        return Response({"detail": "未登录"}, status=401)
    if not ctx.platform:
        return Response({"data": {"permissions": []}})
    user_id = str(user.get("user_id") or user.get("sub") or "")
    perms = scope_repo.build_permissions(user_id, ctx.platform)
    if ctx.channel == "mall_qd":
        return Response({"data": {"permissions": perms["permissions"]}})
    return Response(api_ok({"permissions": perms["permissions"]}))
