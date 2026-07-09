import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_domain.authentication import ExpJWTAuthentication, TokenUser, decode_access_token
from apps.auth_domain.jwt_tokens import create_access_token, create_refresh_token, decode_token
from apps.auth_domain.services.avatar_upload import save_user_avatar
from apps.auth_domain.services.customer import CustomerUserService
from apps.auth_domain.services import identify as identify_svc
from apps.auth_domain.services.profile import UserProfileService
from qd_common.password_java import verify_password
from qd_common.responses import api_fail, api_ok

logger = logging.getLogger(__name__)


def _issue_tokens(token_data: dict, user_id: str) -> tuple[str, str]:
    return (
        create_access_token(token_data),
        create_refresh_token(
            {"user_id": user_id, "account_kind": token_data.get("account_kind")}
        ),
    )


def get_current_user(request: Request) -> dict | None:
    if hasattr(request, "user") and isinstance(request.user, TokenUser):
        return request.user._payload
    auth = ExpJWTAuthentication()
    result = auth.authenticate(request)
    if result:
        return result[0]._payload
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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request: Request):
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
        payload = CustomerUserService.build_login_payload(user, access, refresh, avatar=avatar)
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
    body = CustomerUserService.build_login_payload(user, access, refresh_tok, avatar=avatar)
    return Response(api_ok(body, message="刷新成功"))


@api_view(["GET"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def me(request: Request):
    current = get_current_user(request)
    if not current:
        return Response(api_fail(401, "未登录"))
    if current.get("account_kind") != "exp_user":
        return Response(api_fail(400, "仅支持 C 端用户"))
    user = CustomerUserService.get_by_id(int(current["user_id"]))
    if not user:
        return Response(api_fail(404, "注册用户不存在！"))
    avatar = UserProfileService.avatar_url(user.photo_id)
    return Response(
        api_ok(
            CustomerUserService.build_identify_payload(user, avatar=avatar),
            message="获取认证数据成功!",
        )
    )


@api_view(["GET"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def basic_info(request: Request):
    current = get_current_user(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    try:
        data = UserProfileService.get_basic_info(int(current["user_id"]))
        return Response(api_ok(data, message="获取用户基本信息成功!"))
    except DatabaseError as exc:
        logger.exception("basic_info db error: %s", exc)
        return Response(api_fail(503, "数据库不可用"))
    except Exception as exc:
        logger.exception("basic_info failed: %s", exc)
        return Response(api_fail(500, f"获取用户基本信息失败：{exc}"))


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@api_view(["GET", "POST"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def update_basic_info(request: Request):
    current = get_current_user(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = UserProfileService.update_basic_info(
        int(current["user_id"]),
        user_name=_param(request, "userName"),
        mobile=_param(request, "mobile"),
        email=_param(request, "email"),
        identity=_param(request, "identity"),
        area_id=_param(request, "area_id"),
        image_id=_param(request, "imageId"),
        is_accept_message=_param(request, "is_accept_message"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@api_view(["GET"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def set_password(request: Request):
    current = get_current_user(request)
    if not current or current.get("account_kind") != "exp_user":
        return Response(api_fail(401, "用户未登录"))
    password = _param(request, "password")
    password1 = _param(request, "password1")
    if not password:
        return Response(api_fail(400, "密码不能为空！"))
    if password != password1:
        return Response(api_fail(400, "两次输入密码不一致！"))
    ok_flag, msg = CustomerUserService.change_password(
        int(current["user_id"]),
        _param(request, "oldPassword"),
        password,
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@api_view(["POST"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def upload_avatar(request: Request):
    current = get_current_user(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    uploaded = request.FILES.get("photo")
    if not uploaded:
        return Response(api_fail(400, "文件为空"))
    ok_flag, msg, data = save_user_avatar(
        data=uploaded.read(),
        content_type=uploaded.content_type or "application/octet-stream",
    )
    if ok_flag:
        return Response(api_ok(data, message=msg))
    return Response(api_fail(400, msg))


@api_view(["GET", "POST"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def update_personal_profile(request: Request):
    current = get_current_user(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = identify_svc.update_personal_profile(
        int(current["user_id"]),
        true_name=_param(request, "trueName"),
        mobile=_param(request, "mobile"),
        email=_param(request, "email"),
        idcard=_param(request, "idcard"),
        company_name=_param(request, "company_name"),
        area_id=_param(request, "area_id"),
        address=_param(request, "addreddInfo"),
        password=_param(request, "password"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@api_view(["GET", "POST"])
@authentication_classes([ExpJWTAuthentication])
@permission_classes([AllowAny])
def update_company_profile(request: Request):
    current = get_current_user(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = identify_svc.update_company_profile(
        int(current["user_id"]),
        company_id=_param(request, "id"),
        name=_param(request, "name"),
        country=_param(request, "country"),
        area_id=_param(request, "areaId"),
        address=_param(request, "address"),
        tax_num=_param(request, "taxNum"),
        bank=_param(request, "bank"),
        bank_card_num=_param(request, "bankCardNum"),
        contract_phone=_param(request, "mobile"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
