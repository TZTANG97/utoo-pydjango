from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.orders.services import accessory_ops as accessory_ops_svc
from apps.orders.services import accessory_upload as accessory_upload_svc
from apps.orders.services import child_forms as child_forms_svc
from apps.orders.services import print_pdf as print_pdf_svc
from apps.orders.services import sale_detail as detail_svc


@forward_order_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def upload_child_data(request: Request, user=None):
    uploaded = request.FILES.get("orderdata")
    if not uploaded:
        return Response(api_fail(400, "文件为空"))
    type_raw = str(request.data.get("type") or request.POST.get("type") or "7")
    id_raw = str(request.data.get("id") or request.POST.get("id") or "")
    acc_type = int(type_raw) if type_raw.isdigit() else 7
    exp_of_id = int(id_raw) if id_raw.isdigit() else None
    ok_flag, msg, obj = accessory_upload_svc.save_order_attachment(
        data=uploaded.read(),
        orig_name=uploaded.name or "upload",
        content_type=uploaded.content_type or "application/octet-stream",
        acc_type=acc_type,
        exp_of_id=exp_of_id,
    )
    if ok_flag:
        return Response(api_ok(obj, message=msg))
    return Response(api_fail(400, msg))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def load_accessory(request: Request, user=None):
    oid = str(request.query_params.get("id") or "")
    if not oid.strip().isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = accessory_ops_svc.can_upload_accessory(order_id=int(oid))
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def print_pdf(request: Request, user=None):
    oid = str(request.query_params.get("id") or "")
    if not oid.strip().isdigit():
        return Response(api_fail(400, "参数错误"))
    body = print_pdf_svc.print_pdf_info(
        user_id=int(user["user_id"]),
        order_id=int(oid),
    )
    if body is None:
        return Response(api_fail(404, "订单不存在或无权查看"))
    return Response(api_ok(body))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def order_detail(request: Request, user=None):
    oid = str(request.query_params.get("id") or "")
    order_id = int(oid) if oid.isdigit() else 0
    data = detail_svc.order_detail(
        user_id=int(user["user_id"]),
        order_id=order_id,
    )
    if not data.get("of"):
        return Response(api_fail(404, "订单不存在或无权查看"))
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_child_form_by_id_exp(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    data = child_forms_svc.child_forms_by_sale_order(
        user_id=int(user["user_id"]),
        of_id=str(q.get("ofId") or params.get("ofId") or ""),
        order_id=str(q.get("order_id") or params.get("order_id") or ""),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
    )
    return Response(api_ok(data))
