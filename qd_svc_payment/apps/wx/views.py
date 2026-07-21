import logging
from urllib.parse import unquote

from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_support.helpers import get_current_user_from_request, is_exp_customer
from apps.wx.services import feedback as feedback_svc
from apps.wx.services import qr_login as qr_svc
from apps.wx.services import reservation_detail as reservation_svc
from qd_common.responses import api_fail, api_ok

logger = logging.getLogger(__name__)


def _legacy_ajax(res: bool, res_msg: str, obj) -> dict:
    return {
        "res": res,
        "resMsg": res_msg,
        "obj": obj,
        "code": 0 if res else 1,
        "message": res_msg,
        "data": obj,
    }


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def wechat_qr_generator(request: Request):
    del request
    if not qr_svc.wechat_configured():
        return Response(api_fail(501, "微信扫码登录未配置 WEIXIN_GZH_APPID / WEIXIN_GZH_SECRET"))
    ok_flag, msg, data = qr_svc.generate_qrcode_url()
    if not ok_flag:
        return Response(api_fail(501, msg))
    return JsonResponse(data)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def qr_scan_status_check(request: Request):
    ticket = unquote(str(request.query_params.get("ticket") or ""))
    res, res_msg, obj = qr_svc.check_qr_scan_status(ticket)
    return Response(_legacy_ajax(res, res_msg, obj))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def reservation_detail(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
        return Response(api_fail(401, "用户未登录"))
    cid = str(request.query_params.get("id") or "")
    if not cid.strip().isdigit():
        return Response(api_fail(400, "参数错误"))
    body = reservation_svc.get_reservation_detail(
        user_id=int(user["user_id"]),
        consult_id=int(cid),
    )
    if body is None:
        return Response(api_fail(404, "预约不存在"))
    return Response(api_ok(body, message="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_feedback(request: Request):
    user = get_current_user_from_request(request)
    if not is_exp_customer(user):
        return Response(api_fail(401, "请登录后再进行意见反馈！"))
    content = str(
        request.query_params.get("content")
        or (request.data.get("content") if isinstance(request.data, dict) else "")
        or ""
    )
    ok_flag, msg = feedback_svc.add_feedback(
        user_id=int(user["user_id"]),
        content=content,
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
