"""小程序/后台 list_dpt — 对齐 Java ExperimentOrderController / ExperimentSubOrderController。"""
from __future__ import annotations

from typing import Any

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import (
    datatable_payload,
    merge_payload,
    parse_datatable_params,
    to_int,
)
from apps.admin_experiment.repositories import orders as order_repo
from apps.core.db_utils import fetch_one
from apps.orders.services import child_forms as child_forms_svc
from apps.orders.services import staff_sale_detail as staff_detail_svc
from qd_common.responses import ajax_fail, ajax_ok


def _mp_row(row: dict[str, Any]) -> dict[str, Any]:
    """补齐小程序 order_list 使用的 snake_case 字段。"""
    try:
        total = float(row.get("totalPrice") or 0)
    except (TypeError, ValueError):
        total = 0.0
    try:
        invoice_type = int(row.get("invoiceType") or 0)
    except (TypeError, ValueError):
        invoice_type = 0
    manager = (
        row.get("managerName")
        or row.get("managerTrueName")
        or row.get("saleManager")
        or ""
    )
    sale_user = (
        row.get("saleUserName")
        or row.get("saleUserTrueName")
        or row.get("saleUser")
        or ""
    )
    out = dict(row)
    out.update(
        {
            "id": row.get("id"),
            "order_id": row.get("orderId") or row.get("order_id") or "",
            "orderId": row.get("orderId") or row.get("order_id") or "",
            "order_status": row.get("orderStatus"),
            "order_type": row.get("orderType"),
            "order_time": row.get("orderTime") or "",
            "addTime": row.get("addTime") or "",
            "totalPrice": total,
            "invoiceType": invoice_type,
            "customerName": row.get("customerName") or "",
            "managerName": manager,
            "saleUserName": sale_user,
        }
    )
    return out


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def experiment_order_list_dpt(request: Request):
    """GET /api/experimentOrder/list_dpt.ajax — order_type=6。"""
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = order_repo.list_orders(
        order_type="6",
        order_id=str(data.get("order_id") or data.get("orderId") or "").strip(),
        company_name=str(
            data.get("customer_name") or data.get("companyName") or data.get("company_name") or ""
        ).strip(),
        supplier_name=str(data.get("supplier_name") or data.get("supplierName") or "").strip(),
        sale_manager=str(
            data.get("sale_Manager") or data.get("sale_manager") or data.get("saleManager") or ""
        ).strip(),
        sale_user=str(data.get("sale_user") or data.get("saleUser") or "").strip(),
        order_status=str(data.get("order_status") or data.get("orderStatus") or "").strip(),
        goods_name=str(data.get("goods_name") or data.get("goodsName") or "").strip(),
        order_start=str(
            data.get("order_startime") or data.get("orderStart") or data.get("order_start") or ""
        ).strip(),
        order_end=str(
            data.get("order_endtime") or data.get("orderEnd") or data.get("order_end") or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    return Response(
        datatable_payload(draw=draw, total=total, rows=[_mp_row(r) for r in rows])
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def experiment_sub_order_list_dpt(request: Request):
    """GET /api/experimentSubOrder/list_dpt.ajax — 实验分包订单 order_type=8。"""
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = order_repo.list_orders(
        order_type="8",
        order_id=str(data.get("order_id") or data.get("orderId") or "").strip(),
        company_name=str(
            data.get("stockCompanyName")
            or data.get("customer_name")
            or data.get("customerName")
            or data.get("company_name")
            or ""
        ).strip(),
        supplier_name=str(data.get("supplier_name") or data.get("supplierName") or "").strip(),
        sale_manager=str(
            data.get("sale_Manager") or data.get("sale_manager") or data.get("saleManager") or ""
        ).strip(),
        sale_user=str(data.get("sale_user") or data.get("saleUser") or "").strip(),
        order_status=str(data.get("order_status") or data.get("orderStatus") or "").strip(),
        goods_name=str(data.get("goods_name") or data.get("goodsName") or "").strip(),
        order_start=str(
            data.get("order_startime") or data.get("orderStart") or data.get("order_start") or ""
        ).strip(),
        order_end=str(
            data.get("order_endtime") or data.get("orderEnd") or data.get("order_end") or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    return Response(
        datatable_payload(draw=draw, total=total, rows=[_mp_row(r) for r in rows])
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def experiment_order_detail_dpt_xcx(request: Request):
    """员工端实验订单详情 — /api/experimentOrder/orderdetaildptxcx.ajax"""
    data = merge_payload(request)
    oid = str(request.query_params.get("id") or data.get("id") or "").strip()
    order_id = int(oid) if oid.isdigit() else 0
    body = staff_detail_svc.order_detail_dpt(order_id=order_id)
    if not body.get("of"):
        return Response(ajax_fail("订单不存在"))
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


def _child_forms_dpt_params(request: Request) -> dict:
    data = merge_payload(request)
    return {
        "of_id": str(
            request.query_params.get("ofId")
            or data.get("ofId")
            or data.get("of_id")
            or ""
        ).strip(),
        "order_id": str(
            request.query_params.get("order_id")
            or data.get("order_id")
            or ""
        ).strip(),
        "start": str(request.query_params.get("start") or data.get("start") or "0"),
        "length": str(request.query_params.get("length") or data.get("length") or "10"),
        "draw": str(request.query_params.get("draw") or data.get("draw") or "1"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_child_form_by_id_exp_dpt(request: Request):
    """员工端实验订单产品列表 — getChildFormByIdExp_dpt.ajax（顶层 DataTables）。"""
    params = _child_forms_dpt_params(request)
    return Response(child_forms_svc.child_forms_by_sale_order_dpt(**params))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_child_form_by_id_exp_sub(request: Request):
    """员工端分包订单产品列表 — experimentSubOrder/getChildFormByIdExp.ajax。"""
    params = _child_forms_dpt_params(request)
    return Response(child_forms_svc.child_forms_by_sale_order_dpt(**params))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def experiment_child_order_list_dpt(request: Request):
    """员工端实验子订单全局列表 — /api/experimentChildOrder/list_dpt.ajax（order_type=10）。"""
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = order_repo.list_sub_orders(
        order_type="10",
        order_id=str(data.get("order_id") or data.get("orderId") or "").strip(),
        parent_order_id=str(
            data.get("parent_order_id") or data.get("parentOrderId") or data.get("ofId") or ""
        ).strip(),
        customer_name=str(
            data.get("stockCompanyName")
            or data.get("customer_name")
            or data.get("customerName")
            or ""
        ).strip(),
        sale_manager=str(
            data.get("sale_Manager") or data.get("sale_manager") or data.get("saleManager") or ""
        ).strip(),
        sale_user=str(data.get("sale_user") or data.get("saleUser") or "").strip(),
        order_status=str(data.get("order_status") or data.get("orderStatus") or "").strip(),
        pay_status=str(data.get("pay_status") or data.get("payStatus") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(
        datatable_payload(draw=draw, total=total, rows=[_mp_row(r) for r in rows])
    )


def _resolve_sale_order_pk(data: dict) -> int:
    """解析主单 PK：优先 id/ofId；否则按业务单号 order_id 查。"""
    pk = to_int(data.get("id") or data.get("ofId") or data.get("of_id"))
    if pk:
        return pk
    order_no = str(data.get("order_id") or data.get("orderId") or "").strip()
    if not order_no:
        return 0
    row = fetch_one(
        """
        SELECT id FROM experiment_order
        WHERE order_id = %(oid)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"oid": order_no},
    )
    if row:
        return int(row["id"])
    return to_int(order_no) or 0


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_relevance_order_dpt(request: Request):
    """员工端增加关联订单 — /api/experimentOrder/addRelevanceOrder_dpt.ajax。"""
    data = merge_payload(request)
    order_pk = _resolve_sale_order_pk(data)
    if not order_pk:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.add_related_order(
        order_id=order_pk,
        related_order_no=str(
            data.get("rOrderId")
            or data.get("relatedOrderId")
            or data.get("relatedOrderNo")
            or ""
        ),
        r_select=str(data.get("rSelect") or data.get("relatedType") or data.get("type") or ""),
    )
    return Response(ajax_ok(res_msg=msg) if ok_flag else ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def geranate_yyd_form(request: Request):
    """员工端生成预约单 — /api/experimentOrder/geranateYydForm.ajax。"""
    data = merge_payload(request)
    order_pk = _resolve_sale_order_pk(data)
    if not order_pk:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.generate_appointment(
        order_id=order_pk,
        test_address_id=str(data.get("testAddressId") or data.get("test_address_id") or ""),
    )
    return Response(ajax_ok(res_msg=msg) if ok_flag else ajax_fail(msg))
