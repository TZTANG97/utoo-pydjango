from __future__ import annotations

from decimal import Decimal

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_settings.repositories import bill_type as bill_repo
from apps.admin_settings.repositories import evaluate as evaluate_repo
from apps.admin_settings.repositories import order_type as order_type_repo
from apps.admin_settings.repositories import paytype as paytype_repo
from apps.admin_settings.repositories import taxes as taxes_repo
from apps.core.responses import ajax_fail, ajax_ok


def _payload(request: Request) -> dict:
    body = request.data if isinstance(request.data, dict) else {}
    q = {k: request.query_params.get(k) for k in request.query_params.keys()}
    return {**q, **body}


def _staff_id(user: dict | None) -> str | None:
    if not user:
        return None
    return str(user.get("user_id") or "")


# ---------- 税率管理 ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_list(request: Request, user=None):
    draw, page, page_size = parse_datatable_params(request)
    rows, total = taxes_repo.list_taxes(page, page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_submit(request: Request, user=None):
    data = _payload(request)
    name = (data.get("name") or "").strip()
    raw_value = (data.get("taxValue") or data.get("tax_value") or "").strip()
    if not name:
        return Response(False)
    if raw_value.endswith("%"):
        raw_value = str(Decimal(raw_value.rstrip("%")) / Decimal("100"))
    tax_value, err = taxes_repo.validate_tax_rate_text(raw_value)
    if err:
        return Response(False)
    if taxes_repo.select_tax_by_name(name):
        return Response(False)
    taxes_repo.insert_tax(name=name, tax_value=tax_value, user_id=_staff_id(user))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_get_by_id(request: Request, user=None):
    data = _payload(request)
    tax_id = data.get("id")
    if not tax_id:
        return Response(ajax_fail("数据错误"))
    row = taxes_repo.get_tax(int(tax_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_update(request: Request, user=None):
    data = _payload(request)
    tax_id = data.get("id")
    name = (data.get("name") or "").strip()
    raw_value = (data.get("taxValue") or data.get("tax_value") or "").strip()
    if not tax_id or not name or not raw_value:
        return Response(ajax_ok(obj="请填写修改字段"))
    tax_value, err = taxes_repo.validate_tax_rate_text(raw_value)
    if err:
        return Response(ajax_ok(obj=err))
    taxes_repo.update_tax(
        tax_id=int(tax_id),
        name=name,
        tax_value=tax_value,
        user_id=_staff_id(user),
    )
    return Response(ajax_ok(obj=""))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_update_status(request: Request, user=None):
    data = _payload(request)
    tax_id = data.get("id")
    status = str(data.get("status") or "")
    if not tax_id or status not in {"1", "2"}:
        return Response(False)
    disabled = status == "2"
    taxes_repo.update_tax_status(
        tax_id=int(tax_id), disabled=disabled, user_id=_staff_id(user)
    )
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_delete(request: Request, user=None):
    data = _payload(request)
    tax_id = data.get("id")
    if not tax_id:
        return Response(False)
    taxes_repo.delete_tax(int(tax_id))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def taxes_get_all(request: Request, user=None):
    rows, _ = taxes_repo.list_taxes(page=1, page_size=1000)
    active = [row for row in rows if not row.get("delStatus")]
    return ajax_response(True, obj=active)


# ---------- 收付款方式 ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def paytype_list(request: Request, user=None):
    draw, page, page_size = parse_datatable_params(request)
    rows, total = paytype_repo.list_paytypes(page, page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def paytype_get_all(request: Request):
    """小程序 consumePaytype/getallptype.ajax — Java getConsumePaytype(2)。"""
    del request
    rows = paytype_repo.list_all_by_pay_type(2)
    return Response(ajax_ok(obj=rows, res_msg="获取成功!"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def paytype_submit(request: Request, user=None):
    data = _payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return Response(False)
    if paytype_repo.find_by_name(name):
        return Response(False)
    pay_type = int(data.get("payType") or data.get("pay_type") or 1)
    nums = int(data.get("nums") or data.get("nums1") or data.get("nums2") or 0)
    scale_val = (data.get("scaleVal") or data.get("scale_val") or "").strip()
    if pay_type == 2:
        scale_val = paytype_repo.build_scale_val(pay_type, nums)
    elif pay_type == 3:
        scale_val = ""
    paytype_repo.insert_paytype(
        {
            "name": name,
            "nums": nums,
            "scale_val": scale_val,
            "pay_type": pay_type,
            "jszq": int(data.get("jszq") or 0),
            "memo": data.get("memo"),
        }
    )
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def paytype_update_status(request: Request, user=None):
    data = _payload(request)
    paytype_id = data.get("id")
    status = str(data.get("status") or "")
    if not paytype_id:
        return Response(ajax_fail("更新失败!"))
    disabled = status == "1"
    paytype_repo.update_paytype_status(paytype_id=int(paytype_id), disabled=disabled)
    return ajax_response(True, res_msg="操作成功")


# ---------- 出项/进项发票 ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def billtype_list(request: Request, user=None):
    data = _payload(request)
    draw, page, page_size = parse_datatable_params(request)
    bill_type = int(data.get("type") or 1)
    rows, total = bill_repo.list_bill_types(
        bill_type=bill_type, page=page, page_size=page_size
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def billtype_all_bill(request: Request):
    """小程序 billtype/allBill.ajax — type 1进项 2出项。"""
    data = _payload(request)
    try:
        bill_type = int(data.get("type") or 1)
    except (TypeError, ValueError):
        bill_type = 1
    rows = bill_repo.list_all_by_type(bill_type)
    return Response(ajax_ok(obj=rows, res_msg="获取成功!"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def billtype_submit(request: Request, user=None):
    data = _payload(request)
    name = (data.get("name") or "").strip()
    bill_type = int(data.get("type") or 1)
    if not name:
        return Response(False)
    if bill_repo.find_by_name_and_type(name=name, bill_type=bill_type):
        return Response(False)
    bill_repo.insert_bill_type(
        name=name, bill_type=bill_type, user_id=_staff_id(user)
    )
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def billtype_get_by_id(request: Request, user=None):
    data = _payload(request)
    bill_id = data.get("id")
    if not bill_id:
        return Response(ajax_fail("数据错误"))
    return Response(ajax_ok(obj=bill_repo.get_bill_type(int(bill_id))))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def billtype_update(request: Request, user=None):
    data = _payload(request)
    bill_id = data.get("id")
    name = (data.get("name") or "").strip()
    if not bill_id or not name:
        return Response(ajax_ok(obj="请填写修改字段"))
    bill_repo.update_bill_type_name(
        bill_id=int(bill_id), name=name, user_id=_staff_id(user)
    )
    return Response(ajax_ok(obj=""))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def billtype_update_status(request: Request, user=None):
    data = _payload(request)
    bill_id = data.get("id")
    status = str(data.get("status") or "")
    if not bill_id or status not in {"1", "2"}:
        return Response(False)
    disabled = status == "2"
    bill_repo.update_bill_type_status(
        bill_id=int(bill_id), disabled=disabled, user_id=_staff_id(user)
    )
    return Response(True)


# ---------- 订单类型 ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_list(request: Request, user=None):
    data = _payload(request)
    draw, page, page_size = parse_datatable_params(request)
    type_name = (data.get("type_name") or "").strip()
    rows, total = order_type_repo.list_order_types(
        type_name=type_name, page=page, page_size=page_size
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_submit(request: Request, user=None):
    data = _payload(request)
    type_name = (data.get("type_name") or "").strip()
    if not type_name:
        return ajax_response(False, res_msg="保存失败,没有数据，请确认!")
    new_id = order_type_repo.insert_order_type(
        {
            "type_sort": int(data.get("type_sort") or 0),
            "type_name": type_name,
            "type_desc": data.get("type_desc") or "",
            "table_id": int(data.get("table_id") or 0),
            "pt_type": "2",
        }
    )
    return ajax_response(True, res_msg=str(new_id))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_update(request: Request, user=None):
    data = _payload(request)
    order_type_id = data.get("id")
    if not order_type_id:
        return ajax_response(False, res_msg="编辑失败,没有数据，请确认!")
    order_type_repo.update_order_type(
        {
            "id": int(order_type_id),
            "type_sort": int(data.get("type_sort") or 0),
            "type_name": (data.get("type_name") or "").strip(),
            "type_desc": data.get("type_desc") or "",
            "table_id": int(data.get("table_id") or 0),
            "pt_type": "2",
        }
    )
    return ajax_response(True, res_msg=str(order_type_id))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_delete(request: Request, user=None):
    data = _payload(request)
    order_type_id = data.get("id")
    if not order_type_id:
        return ajax_response(False, res_msg="操作失败!")
    order_type_repo.soft_delete_order_type(int(order_type_id))
    return ajax_response(True, res_msg="操作成功!")


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_query_all(_request: Request, user=None):
    rows, _ = order_type_repo.list_order_types(type_name="", page=1, page_size=1000)
    return ajax_response(True, obj=rows)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_type_query_tables(_request: Request, user=None):
    return ajax_response(True, obj=order_type_repo.list_order_type_tables())


# ---------- 自动评价设置 ----------


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_setting_get(_request: Request, user=None):
    return ajax_response(True, obj=evaluate_repo.get_evaluate_setting())


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_setting_save(request: Request, user=None):
    data = _payload(request)
    try:
        evaluate_time = int(data.get("evaluate_time") or 0)
        evaluate_time_type = int(data.get("evaluate_time_type") or 0)
    except (TypeError, ValueError):
        return ajax_response(False, res_msg="参数错误")
    if evaluate_time <= 0:
        return ajax_response(False, res_msg="自动评价时间必须大于 0")
    evaluate_repo.save_evaluate_setting(
        evaluate_time=evaluate_time,
        evaluate_time_type=evaluate_time_type,
    )
    return ajax_response(True, res_msg="设置成功")
