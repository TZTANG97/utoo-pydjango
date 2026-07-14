from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.repositories import evaluate_order as evaluate_repo
from apps.admin_system.views.common import merge_payload


def _evaluated_list(request: Request, *, order_type: str):
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = evaluate_repo.list_evaluated_orders(
        order_type=order_type,
        order_id=(data.get("order_id") or data.get("order_num") or "").strip(),
        customer_name=(data.get("customer_name") or "").strip(),
        goods_name=(data.get("goods_name") or "").strip(),
        supplier_name=str(data.get("supplier_name") or "").strip(),
        sale_manager=str(data.get("sale_Manager") or data.get("sale_manager") or "").strip(),
        sale_user=str(data.get("sale_user") or "").strip(),
        order_startime=(data.get("order_startime") or "").strip(),
        order_endtime=(data.get("order_endtime") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_list_dpt(request: Request, user=None):
    del user
    return _evaluated_list(request, order_type="6")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sublist_dpt(request: Request, user=None):
    del user
    return _evaluated_list(request, order_type="8")
