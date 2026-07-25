from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import merge_payload
from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from qd_common.responses import api_ok
from qd_common.responses import api_fail
from qd_common.responses import ajax_fail, ajax_ok
from apps.orders.services import actions as order_actions
from apps.orders.services import create_child_page as create_page_svc
from apps.orders.services import purchase as purchase_svc
from apps.orders.services import staff_child_detail as staff_child_detail_svc


def _sale_order_pk(request: Request) -> int:
    data = merge_payload(request)
    raw = (
        request.query_params.get("saleOrderId")
        or request.query_params.get("id")
        or data.get("saleOrderId")
        or data.get("id")
        or ""
    )
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else ""
    text = str(raw).strip()
    return int(text) if text.isdigit() else 0


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_order_page(request: Request):
    """员工创建实验子订单页头 — POST/GET createOrderPage.ajax"""
    body = create_page_svc.create_order_page(sale_order_id=_sale_order_pk(request))
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_order_page_xcx(request: Request):
    """员工创建实验子订单可选产品 — createOrderPagexcx.ajax"""
    body = create_page_svc.create_order_page_xcx(sale_order_id=_sale_order_pk(request))
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def purchase_order_detail(request: Request):
    """员工端子订单详情 — ajax {res,obj}；按 id 加载并富化。"""
    from apps.admin_experiment.helpers import to_int

    data = merge_payload(request)
    order_id = to_int(request.query_params.get("id") or data.get("id") or data.get("ofId")) or 0
    body = staff_child_detail_svc.order_detail_dpt(order_id=order_id)
    if not body.get("of"):
        return Response(ajax_fail("订单不存在"))
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def orders_by_sale_order_id(request: Request):
    """子订单列表 — 客户按归属过滤；员工走 dpt。返回顶层 DataTables。"""
    from apps.auth_support.helpers import get_current_user_from_request, is_exp_customer

    q = request.query_params
    params = parse_ajax_params(request)
    data = merge_payload(request)
    of_id = str(q.get("ofId") or params.get("ofId") or data.get("ofId") or "")
    order_id = str(q.get("order_id") or params.get("order_id") or data.get("order_id") or "")
    start = params["start"]
    length = params["length"]
    draw = params["draw"]

    user = get_current_user_from_request(request)
    if is_exp_customer(user):
        body = purchase_svc.purchase_orders_by_sale(
            user_id=int(user["user_id"]),
            of_id=of_id,
            order_id=order_id,
            start=start,
            length=length,
            draw=draw,
        )
    else:
        body = purchase_svc.purchase_orders_by_sale_dpt(
            of_id=of_id,
            order_id=order_id,
            start=start,
            length=length,
            draw=draw,
        )
    return Response(body)


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
