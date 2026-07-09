from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from apps.core.responses import api_ok
from apps.core.responses import api_fail
from apps.orders.services import actions as order_actions
from apps.orders.services import purchase as purchase_svc


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def purchase_order_detail(request: Request, user=None):
    oid = str(request.query_params.get("id") or "")
    order_id = int(oid) if oid.isdigit() else 0
    data = purchase_svc.purchase_order_detail(
        user_id=int(user["user_id"]),
        order_id=order_id,
    )
    return Response(api_ok(data))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def orders_by_sale_order_id(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    data = purchase_svc.purchase_orders_by_sale(
        user_id=int(user["user_id"]),
        of_id=str(q.get("ofId") or params.get("ofId") or ""),
        order_id=str(q.get("order_id") or params.get("order_id") or ""),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
    )
    return Response(api_ok(data))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def sure_ok(request: Request, user=None):
    cid = str(request.query_params.get("id") or "")
    child_id = int(cid) if cid.isdigit() else 0
    ok_flag, msg = order_actions.confirm_child_complete(
        user_id=int(user["user_id"]),
        child_id=child_id,
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(None, message=msg))
