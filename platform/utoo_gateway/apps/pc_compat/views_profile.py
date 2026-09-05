from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.services.avatar_upload import save_user_avatar
from apps.auth_pc.services.customer import CustomerUserService
from apps.auth_pc.services import identify as identify_svc
from apps.auth_pc.services.profile import UserProfileService
from apps.auth_pc.views import get_current_user_from_request, is_exp_customer
from apps.core.identity_forward import forward_identity_first
from apps.core.responses import api_fail, api_ok


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_identity_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_user_basic_info(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = UserProfileService.update_basic_info(
        int(user["user_id"]),
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


@forward_identity_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def set_password(request: Request):
    user = get_current_user_from_request(request)
    if not user or user.get("account_kind") != "exp_user":
        return Response(api_fail(401, "用户未登录"))
    password = _param(request, "password")
    password1 = _param(request, "password1")
    if not password:
        return Response(api_fail(400, "密码不能为空！"))
    if password != password1:
        return Response(api_fail(400, "两次输入密码不一致！"))
    ok_flag, msg = CustomerUserService.change_password(
        int(user["user_id"]),
        _param(request, "oldPassword"),
        password,
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_identity_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_phone_avatar(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
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


@forward_identity_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_or_update_user_data(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = identify_svc.update_personal_profile(
        int(user["user_id"]),
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


@forward_identity_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_or_update_user_company_data(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
        return Response(api_fail(401, "用户未登录"))
    ok_flag, msg = identify_svc.update_company_profile(
        int(user["user_id"]),
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
