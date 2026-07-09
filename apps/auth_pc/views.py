import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.authentication import (
    ExpJWTAuthentication,
    TokenUser,
    decode_access_token,
    user_from_request_user,
)
from apps.auth_pc.jwt_tokens import create_access_token, create_refresh_token, decode_token
from apps.auth_pc.services.customer import CustomerUserService
from apps.auth_pc.services.profile import UserProfileService
from apps.core.responses import api_fail, api_ok
from apps.core.svc_proxy import forward_auth, svc_auth_enabled
from qd_common.password_java import verify_password

logger = logging.getLogger(__name__)


def _issue_tokens(token_data: dict, user_id: str) -> tuple[str, str]:
    access = create_access_token(token_data)
    refresh = create_refresh_token(
        {"user_id": user_id, "account_kind": token_data.get("account_kind")}
    )
    return access, refresh


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request: Request):
    if svc_auth_enabled():
        return forward_auth(request, "/api/auth/login")
    data = request.data or {}
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""
    login_type = (data.get("loginType") or "1").strip()

    if not name or not password:
        return Response(api_fail(400, "用户名或密码不能为空"))

    if login_type != "1":
        return Response(api_fail(400, "当前仅支持客户登录 loginType=1"))

    try:
        user = CustomerUserService.find_by_login_name(name)
        if not user:
            return Response(api_fail(401, "账号未注册"))

        ok, scheme = verify_password(password, user.password or "")
        if not ok:
            return Response(api_fail(401, "密码错误"))

        if scheme in ("std_hex_md5", "plaintext"):
            CustomerUserService.rehash_password_if_legacy(user, password)

        token_data = CustomerUserService.exp_user_token_data(user)
        access, refresh = _issue_tokens(token_data, str(user.id))
        avatar = UserProfileService.avatar_url(user.photo_id)
        payload = CustomerUserService.build_login_payload(
            user, access, refresh, avatar=avatar
        )
        return Response(api_ok(payload, message="登录成功"))
    except DatabaseError as exc:
        logger.exception("login db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    except Exception as exc:
        logger.exception("login failed: %s", exc)
        return Response(api_fail(500, f"登录失败：{exc}"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh(request: Request):
    if svc_auth_enabled():
        return forward_auth(request, "/api/auth/refresh")
    raw = (request.data or {}).get("refresh_token") or ""
    payload = decode_token(raw)
    if not payload or payload.get("type") != "refresh":
        return Response(api_fail(401, "刷新令牌无效"))

    user_id = payload.get("user_id")
    if not user_id:
        return Response(api_fail(401, "刷新令牌无效"))

    user = CustomerUserService.get_by_id(int(user_id))
    if not user:
        return Response(api_fail(401, "用户不存在"))

    token_data = CustomerUserService.exp_user_token_data(user)
    access, refresh_tok = _issue_tokens(token_data, str(user.id))
    avatar = UserProfileService.avatar_url(user.photo_id)
    body = CustomerUserService.build_login_payload(
        user, access, refresh_tok, avatar=avatar
    )
    return Response(api_ok(body, message="刷新成功"))


@api_view(["GET"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def me(request: Request):
    if svc_auth_enabled():
        return forward_auth(request, "/api/auth/me")
    current = get_current_user_from_request(request)
    if not current:
        return Response(api_fail(401, "未登录"))

    account_kind = current.get("account_kind", "exp_user")
    user_id = current.get("user_id")

    if account_kind != "exp_user":
        return Response(api_fail(400, "仅支持 C 端用户"))

    user = CustomerUserService.get_by_id(int(user_id))
    if not user:
        return Response(api_fail(404, "注册用户不存在！"))

    avatar = UserProfileService.avatar_url(user.photo_id)
    return Response(
        api_ok(
            CustomerUserService.build_identify_payload(user, avatar=avatar),
            message="获取认证数据成功!",
        )
    )


def get_current_user_from_request(request: Request) -> dict | None:
    if hasattr(request, "user") and isinstance(request.user, TokenUser):
        return request.user._payload
    auth = ExpJWTAuthentication()
    result = auth.authenticate(request)
    if result:
        return user_from_request_user(result[0])
    token = (request.META.get("HTTP_TOKEN") or request.query_params.get("token") or "").strip()
    if not token:
        return None
    try:
        return decode_access_token(token)
    except Exception:
        return None


def is_exp_customer(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("account_kind") == "exp_user":
        return True
    return str(user.get("user_type")) == "1" and user.get("account_kind") != "sy_user"
