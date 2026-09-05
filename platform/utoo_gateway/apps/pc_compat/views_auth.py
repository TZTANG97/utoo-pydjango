import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.services import password_reset as pw_reset_svc
from apps.auth_pc.services import registration as reg_svc
from apps.auth_pc.services import verify_code as verify_svc
from apps.core.identity_forward import forward_identity_first
from apps.core.responses import api_fail, api_ok

logger = logging.getLogger(__name__)


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_identity_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_verify_code(request: Request):
    telephone = _param(request, "telephone")
    try:
        ok_flag, msg = verify_svc.send_register_code(telephone)
    except DatabaseError as exc:
        logger.exception("getVerifyCode db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_identity_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request: Request):
    try:
        ok_flag, msg = reg_svc.register(
            code=_param(request, "code"),
            mobile=_param(request, "mobile"),
            user_name=_param(request, "userName") or _param(request, "nickName"),
            company_name=_param(request, "companyName"),
            password1=_param(request, "password1"),
            password2=_param(request, "password2"),
        )
    except DatabaseError as exc:
        logger.exception("register db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_identity_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_verify_code_find_pw(request: Request):
    try:
        ok_flag, msg = pw_reset_svc.send_find_password_code(_param(request, "telephone"))
    except DatabaseError as exc:
        logger.exception("getVerifyCodeFindPw db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_identity_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def tel_code_verify(request: Request):
    try:
        ok_flag, msg = pw_reset_svc.reset_password_with_sms(
            telephone=_param(request, "telephone"),
            tel_code=_param(request, "tel_code"),
            password=_param(request, "password"),
            password1=_param(request, "password1"),
        )
    except DatabaseError as exc:
        logger.exception("telCodeVerify db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
