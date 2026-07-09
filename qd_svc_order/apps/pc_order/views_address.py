from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import pc_ajax_view
from qd_common.responses import api_fail, api_ok
from apps.orders.services import delivery_address as addr_svc


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def user_address(request: Request, user=None):
    addr = addr_svc.get_default_address_text(int(user["user_id"]))
    return Response(api_ok(addr))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_delivery_address(request: Request, user=None):
    data = addr_svc.get_delivery_address_list(int(user["user_id"]))
    return Response(api_ok(data))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def insert_delivery_address(request: Request, user=None):
    ok_flag, msg = addr_svc.insert_delivery_address(
        user_id=int(user["user_id"]),
        delivery_name=_param(request, "delivery_name"),
        delivery_phone=_param(request, "delivery_phone"),
        delivery_address=_param(request, "delivery_address"),
        detail_address=_param(request, "detail_address"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def update_delivery_address(request: Request, user=None):
    rid = _param(request, "id")
    if not rid:
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = addr_svc.update_delivery_address(
        user_id=int(user["user_id"]),
        record_id=int(rid),
        delivery_name=_param(request, "delivery_name"),
        delivery_phone=_param(request, "delivery_phone"),
        delivery_address=_param(request, "delivery_address"),
        detail_address=_param(request, "detail_address"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def del_delivery_address(request: Request, user=None):
    rid = _param(request, "id")
    if not rid:
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = addr_svc.delete_or_set_default_address(
        user_id=int(user["user_id"]),
        record_id=int(rid),
        op_type=_param(request, "type", "1"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
