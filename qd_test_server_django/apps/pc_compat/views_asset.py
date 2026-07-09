from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.payment_forward import forward_payment_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_ok
from apps.core.services.sysconfig import get_config_row, integral_convert_ratio
from apps.core.pc_ajax import parse_ajax_params
from apps.payments.services.asset import AssetService
from apps.payments.services.integral_list import get_integral_list_page


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_integral(request: Request, user=None):
    body = AssetService.get_integral_summary(int(user["user_id"]))
    return Response(api_ok(body))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_account(request: Request, user=None):
    data = AssetService.get_account(int(user["user_id"]))
    return Response(api_ok(data))


@forward_payment_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_login=True)
def get_integral_convert_ratio(request: Request, user=None):
    config = get_config_row()
    ratio = integral_convert_ratio(config)
    return Response(api_ok({"integral_convert_ratio": ratio}))


@forward_payment_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_integral_list(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    log_type = str(q.get("type") or params.get("type") or "")
    data = get_integral_list_page(
        user_id=int(user["user_id"]),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        log_type=log_type,
    )
    return Response(api_ok(data))
