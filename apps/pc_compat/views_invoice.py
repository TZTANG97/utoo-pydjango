from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.services.customer import CustomerUserService
from apps.core.invoice_forward import forward_invoice_first
from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.invoices.services import InvoiceService


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_invoice_list(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    inv_type = q.get("type")
    tp = int(inv_type) if inv_type is not None and str(inv_type).isdigit() else 2
    data = InvoiceService.get_invoice_list_page(
        user_id=int(user["user_id"]),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        inv_type=tp,
        order_id=str(q.get("orderId") or params.get("orderId") or ""),
    )
    return Response(api_ok(data))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_invoice_order_list(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    uid = int(user["user_id"])
    user_obj = CustomerUserService.get_by_id(uid)
    mobile = (user_obj.mobile or "") if user_obj else ""
    offset = int(params["start"]) if params["start"].isdigit() else 0
    limit = int(params["length"]) if params["length"].isdigit() else 10
    draw_n = int(params["draw"]) if params["draw"].isdigit() else 1
    total = InvoiceService.count_billable_orders(
        user_id=uid,
        mobile=mobile,
        order_id_kw=str(q.get("orderId") or ""),
        start_time=str(q.get("startTime") or ""),
        end_time=str(q.get("endTime") or ""),
    )
    rows = InvoiceService.list_billable_orders(
        user_id=uid,
        mobile=mobile,
        offset=offset,
        limit=limit,
        order_id_kw=str(q.get("orderId") or ""),
        start_time=str(q.get("startTime") or ""),
        end_time=str(q.get("endTime") or ""),
    )
    return Response(
        api_ok(
            {
                "data": rows,
                "draw": draw_n,
                "recordsTotal": total,
                "recordsFiltered": total,
            }
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def apply_invoice(request: Request, user=None):
    body = request.data if isinstance(request.data, dict) else {}
    ok_flag, msg = InvoiceService.apply_invoice(
        user_id=int(user["user_id"]),
        order_ids=str(body.get("ids") or ""),
        invoice_title=str(body.get("invoiceTitle") or ""),
        inv_type=int(body.get("type") or 2),
        is_pay=int(body.get("isPay") or 0),
        notes=str(body.get("notes") or ""),
        bank_name=str(body.get("bank_name") or ""),
        bank_account=str(body.get("bank_account") or ""),
        reg_address=str(body.get("reg_address") or ""),
        reg_mobile=str(body.get("reg_mobile") or ""),
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_invoice_log_list(request: Request, user=None):
    q = request.query_params
    params = parse_ajax_params(request)
    data = InvoiceService.get_invoice_log_list_page(
        user_id=int(user["user_id"]),
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        order_id_kw=str(q.get("orderId") or params.get("orderId") or ""),
    )
    return Response(api_ok(data))


@forward_invoice_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_invoice_info(request: Request, user=None):
    data = InvoiceService.get_user_invoice_info(int(user["user_id"]))
    return Response(api_ok(data or {}))


@forward_invoice_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def get_invoice_info_list(request: Request, user=None):
    rows = InvoiceService.list_invoice_infos(int(user["user_id"]))
    return Response(api_ok({"invoiceInfs": rows}))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def insert_invoice_info(request: Request, user=None):
    ok_flag, msg = InvoiceService.insert_invoice_info(
        user_id=int(user["user_id"]),
        invoice_title=_param(request, "invoice_title"),
        tax_num=_param(request, "taxNum"),
        bank=_param(request, "bank"),
        bank_card_num=_param(request, "bankCardNum"),
        address=_param(request, "address"),
        mobile=_param(request, "mobile"),
        email=_param(request, "email"),
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def update_invoice_info(request: Request, user=None):
    rid = _param(request, "id")
    if not rid or not rid.isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = InvoiceService.update_invoice_info(
        user_id=int(user["user_id"]),
        record_id=int(rid),
        invoice_title=_param(request, "invoice_title"),
        tax_num=_param(request, "taxNum"),
        bank=_param(request, "bank"),
        bank_card_num=_param(request, "bankCardNum"),
        address=_param(request, "address"),
        mobile=_param(request, "mobile"),
        email=_param(request, "email"),
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def del_invoice_info(request: Request, user=None):
    rid = _param(request, "id")
    op_type = _param(request, "type", "1")
    if not rid or not rid.isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = InvoiceService.delete_or_set_default_invoice(
        user_id=int(user["user_id"]),
        record_id=int(rid),
        op_type=op_type,
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def add_invoice_info_legacy(request: Request, user=None):
    body = request.data if isinstance(request.data, dict) else {}
    q = {k: str(v) for k, v in request.query_params.items()}
    payload = {**q, **body}
    ok_flag, msg = InvoiceService.upsert_legacy_invoice_info(
        user_id=int(user["user_id"]),
        payload=payload,
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_invoice_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def cancel_invoice_info(request: Request, user=None):
    iid = _param(request, "invoiceId")
    if not iid or not str(iid).isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = InvoiceService.cancel_invoice_apply(
        user_id=int(user["user_id"]),
        invoice_id=int(iid),
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))
