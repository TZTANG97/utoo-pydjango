from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from qd_common.responses import api_fail, api_ok
from apps.orders.services import center_order_data as center_svc
from apps.orders.services import sale_list as sale_list_svc
from apps.orders.services import test_or_sure as test_or_sure_svc


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def my_experiment_order_list(request: Request, user=None):
    params = parse_ajax_params(request)
    data = sale_list_svc.my_experiment_order_list(
        user_id=int(user["user_id"]),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        tab_type=params["type"],
        keywords=params["keywords"],
        order_id=params["order_id"],
    )
    return Response(api_ok(data))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def center_get_order_data(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    uid = int(user["user_id"])
    user_id_param = str(q.get("userId") or "")
    if user_id_param.isdigit():
        uid = int(user_id_param)
    tab_type = int(q.get("type") or "0") if str(q.get("type") or "0").isdigit() else 0
    data = center_svc.get_center_order_data(
        user_id=uid,
        tab_type=tab_type,
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
    )
    return Response(api_ok(data))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def experiment_order_list(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    data = sale_list_svc.experiment_order_list(
        user_id=int(user["user_id"]),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        tab_type=str(q.get("type") or params.get("type") or ""),
        keywords=params["keywords"],
        order_id=params["order_id"],
        order_status=str(q.get("order_status") or ""),
    )
    return Response(api_ok(data))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def sel_test_or_sure(request: Request, user=None):
    oid = _param(request, "id")
    if not oid or not oid.strip().isdigit():
        return Response(api_fail(400, "参数不能为空！"))
    data = test_or_sure_svc.list_test_or_sure_children(
        user_id=int(user["user_id"]),
        order_id=int(oid),
        action_type=_param(request, "type", "1"),
    )
    return Response(api_ok(data))
