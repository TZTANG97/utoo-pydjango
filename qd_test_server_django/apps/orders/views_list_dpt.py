"""小程序/后台 list_dpt — 对齐 Java（网关本地孪生，未配 SVC_ORDER_URL 时使用）。"""
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
)
from apps.admin_experiment.repositories import orders as order_repo


def _mp_row(row: dict[str, Any]) -> dict[str, Any]:
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
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = order_repo.list_sub_orders(
        order_type="10",
        order_id=str(data.get("order_id") or data.get("orderId") or "").strip(),
        parent_order_id=str(
            data.get("parent_order_id") or data.get("parentOrderId") or ""
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
