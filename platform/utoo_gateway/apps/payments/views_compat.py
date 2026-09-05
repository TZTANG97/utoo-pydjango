from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.payment_forward import forward_payment_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.payments.services import offline_recharge_detail as offline_svc
from apps.payments.services import redeem as redeem_svc
from apps.payments.services.payment_apply_ops import apply_detail


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def apply_detail_view(request: Request, user=None):
    body = apply_detail(
        user_id=int(user["user_id"]),
        record_id=_param(request, "id"),
        detail_type=_param(request, "type", "0"),
    )
    if body is None:
        return Response(api_fail(404, "记录不存在或无权查看"))
    return Response(api_ok(body))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def recharge_detail_view(request: Request, user=None):
    raw_id = _param(request, "id")
    if not raw_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    body = offline_svc.get_recharge_detail(
        user_id=int(user["user_id"]),
        recharge_id=int(raw_id),
    )
    if body is None:
        return Response(api_fail(404, "充值记录不存在"))
    return Response(api_ok(body))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def user_redeem_log_list_view(request: Request, user=None):
    data = redeem_svc.user_redeem_log_list(
        user_id=int(user["user_id"]),
        start=_param(request, "start", "0"),
        length=_param(request, "length", "10"),
        draw=_param(request, "draw", "1"),
        status=_param(request, "status") or _param(request, "type"),
    )
    return Response(api_ok(data, message="查询成功"))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def redeem_goods_log_detail_view(request: Request, user=None):
    raw_id = _param(request, "id")
    if not raw_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    body = redeem_svc.redeem_goods_log_detail(
        user_id=int(user["user_id"]),
        log_id=int(raw_id),
    )
    if body is None:
        return Response(api_fail(404, "记录不存在"))
    return Response(api_ok(body, message="获取成功"))
