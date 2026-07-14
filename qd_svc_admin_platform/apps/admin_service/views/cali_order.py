from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.helpers import staff_id
from apps.admin_service.repositories import cali_order as cali_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _list_payload(request: Request) -> Response:
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = cali_repo.list_service_applies(
        cali_type=str(data.get("caliType") or data.get("cali_type") or data.get("order_type") or "").strip(),
        cali_status=str(
            data.get("caliStatus") or data.get("cali_status") or data.get("order_status") or ""
        ).strip(),
        order_id=(data.get("order_id") or data.get("orderId") or "").strip(),
        customer_name=(data.get("customer_name") or data.get("customerName") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def service_apply_list(request: Request, user=None):
    del user
    return _list_payload(request)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def todo_list(request: Request, user=None):
    del user
    return _list_payload(request)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def service_apply_update(request: Request, user=None):
    data = merge_payload(request)
    record_id = data.get("id")
    status = data.get("type") or data.get("caliStatus") or data.get("cali_status") or data.get("state")
    if not record_id or status in (None, ""):
        return Response(ajax_fail("操作失败!"))
    ok = cali_repo.update_service_apply(
        record_id=int(record_id),
        cali_status=int(status),
        operator_id=staff_id(user),
    )
    if not ok:
        return Response(ajax_fail("操作失败!"))
    return Response(ajax_ok(res_msg="操作成功"))
