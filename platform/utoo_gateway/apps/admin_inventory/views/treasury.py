from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_inventory.repositories import treasury as repo
from apps.admin_inventory.views import inventory as inv
from apps.admin_system.views.common import merge_payload


def _channel(request: Request) -> str:
    return str(request.headers.get("X-Channel") or "").strip().lower()


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def in_treasury_list(request: Request, user=None):
    """青岛大平台：goods 入库单；愉兔：样品管理单（X-Channel != mall_qd）。"""
    if _channel(request) != "mall_qd":
        return inv.sample_order_list(request, user=user)
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = repo.list_treasury(
        in_out_type=1,
        out_num=(data.get("out_num") or data.get("outNum") or "").strip(),
        order_id=(data.get("order_id") or data.get("orderId") or "").strip(),
        yj_out_time=(data.get("yj_out_time") or data.get("yjOutTime") or "").strip(),
        status=str(data.get("status") or "").strip(),
        store_id=str(data.get("store_id") or data.get("storeId") or "").strip(),
        ftype=str(data.get("ftype") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def out_treasury_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = repo.list_treasury(
        in_out_type=2,
        out_num=(data.get("out_num") or data.get("outNum") or "").strip(),
        order_id=(data.get("order_id") or data.get("orderId") or "").strip(),
        yj_out_time=(data.get("yj_out_time") or data.get("yjOutTime") or "").strip(),
        status=str(data.get("status") or "").strip(),
        store_id=str(data.get("store_id") or data.get("storeId") or "").strip(),
        ftype=str(data.get("ftype") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))
