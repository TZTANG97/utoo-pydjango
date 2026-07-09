from django.http import HttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core import redis_client
from apps.core.payment_forward import forward_payment_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.payments.repositories import pay_info as pay_repo
from apps.payments.services.balance_pay import BalancePayService
from apps.payments.services.pay_notify import (
    KIND_ORDER,
    KIND_RECHARGE,
    dispatch_pay_notify,
)
from apps.payments.services.payment_apply_ops import add_cash, save_accessory
from apps.payments.services.recharge_apply import add_recharge
from apps.payments.services.recharge_list import (
    sel_default_account,
    sel_recharge_list_for_user,
    sel_recharge_status,
)
from apps.payments.services.wechat_prepay import WechatPrepayService
from apps.payments.services.wx_native_client import parse_notify, query_by_transaction_id
from apps.payments.services.wx_settings import wx_pay_configured


def _pay_form_params(request: Request) -> dict[str, str]:
    if request.method.upper() == "POST" and isinstance(request.data, dict):
        return {k: str(v) for k, v in request.data.items()}
    return {k: str(v) for k, v in request.query_params.items()}


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def amount_pay(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg, _ = BalancePayService.pay_orders(
        user_id=int(user["user_id"]),
        of_ids=params.get("ofId", ""),
        use_integral=params.get("useIntegral", "0"),
        pay_way=params.get("pay_way", ""),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def pre_pay(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg, data = WechatPrepayService.pre_pay(
        user_id=int(user["user_id"]),
        of_id=params.get("ofId", ""),
        use_integral=params.get("useIntegral", "0"),
    )
    if ok_flag:
        return Response(api_ok(data or {}))
    if not wx_pay_configured():
        return Response(api_fail(501, msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def pre_amount_pay(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg, data = WechatPrepayService.pre_amount_pay(
        user_id=int(user["user_id"]),
        of_id=params.get("ofId", ""),
        use_integral=params.get("useIntegral", "0"),
    )
    if ok_flag:
        return Response(api_ok(data or {}))
    if not wx_pay_configured():
        return Response(api_fail(501, msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def recharge_pre_pay(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg, data = WechatPrepayService.recharge_pre_pay(
        user_id=int(user["user_id"]),
        money=params.get("money", ""),
    )
    if ok_flag:
        return Response(api_ok(data or {}))
    if not wx_pay_configured():
        return Response(api_fail(501, msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def recharge_continue_pay(request: Request, user=None):
    params = _pay_form_params(request)
    pay_log_id = (params.get("id") or "").strip()
    if not pay_log_id.isdigit():
        return Response(api_fail(400, "缺少支付单 id"))
    ok_flag, msg, data = WechatPrepayService.continue_recharge_pay(
        user_id=int(user["user_id"]),
        pay_log_id=int(pay_log_id),
    )
    if ok_flag:
        return Response(api_ok(data or {}))
    if not wx_pay_configured():
        return Response(api_fail(501, msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def sel_recharge_status_view(request: Request, user=None):
    pending = sel_recharge_status(int(user["user_id"]))
    return Response({"res": pending})


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def sel_recharge_list_view(request: Request, user=None):
    params = _pay_form_params(request)
    data = sel_recharge_list_for_user(
        int(user["user_id"]),
        start=params.get("start", "0"),
        length=params.get("length", "10"),
        draw=params.get("draw", "1"),
        start_time=params.get("startTime", ""),
        end_time=params.get("endTime", ""),
        type_raw=params.get("type", "0"),
    )
    return Response(api_ok(data))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sel_default_account_view(request: Request, user=None):
    del user
    data = sel_default_account()
    return Response(api_ok(data or {}))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def add_cash_view(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg = add_cash(
        user_id=int(user["user_id"]),
        money=params.get("money", ""),
        bank_num=params.get("bankNum", ""),
        account_name=params.get("accountName", ""),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def save_accessory_view(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg = save_accessory(
        user_id=int(user["user_id"]),
        order_ids=params.get("id", ""),
        file_id=params.get("file_id", ""),
        order_type=params.get("type", "2"),
        pay_way=params.get("pay_way", "3"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def add_recharge_view(request: Request, user=None):
    params = _pay_form_params(request)
    ok_flag, msg = add_recharge(
        user_id=int(user["user_id"]),
        money=params.get("money", ""),
        file_id=params.get("file_id", ""),
        pay_way=params.get("pay_way", "3"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def query_pay_status(request: Request):
    out_no = str(request.query_params.get("outTradeNo") or "")
    status = redis_client.get_string(out_no)
    if status == "true":
        return Response(api_ok("支付成功", message="支付成功"))
    return Response(api_ok("未支付", message="未支付"))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def query_pay_status_by_order(request: Request):
    out_no = str(request.query_params.get("outTradeNo") or "")
    if not out_no:
        return Response(api_fail(400, "未支付！"))
    epo = pay_repo.find_pay_order_by_out_trade_no(out_no)
    if not epo or not epo.get("transaction_id"):
        return Response(api_fail(400, "未支付！"))
    ok_flag, state = query_by_transaction_id(str(epo["transaction_id"]))
    if ok_flag:
        return Response(api_ok(state))
    return Response(api_fail(400, "未支付！"))


def _wechat_notify_response(request: Request, kind: str) -> HttpResponse:
    headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_")}
    # normalize Wechatpay-* headers
    norm = {}
    for k, v in request.headers.items():
        norm[k] = v
    body = request.body
    resource = parse_notify(norm, body)
    if not resource:
        return HttpResponse(status=500)
    try:
        dispatch_pay_notify(kind, resource)
    except Exception:
        return HttpResponse(status=500)
    return HttpResponse(
        content='{"code":"SUCCESS","message":"成功"}',
        content_type="application/json",
    )


@forward_payment_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def wechat_pay_notify(request: Request):
    return _wechat_notify_response(request, KIND_ORDER)


@forward_payment_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def wechat_recharge_notify(request: Request):
    return _wechat_notify_response(request, KIND_RECHARGE)


@forward_payment_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def wechat_amount_pay_back(request: Request):
    return _wechat_notify_response(request, KIND_ORDER)
