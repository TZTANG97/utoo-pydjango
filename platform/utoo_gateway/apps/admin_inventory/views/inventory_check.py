from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_inventory.repositories import inventory_check as repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_check_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = repo.list_inventory_checks(
        check_id=(data.get("order_id") or data.get("check_id") or "").strip(),
        order_startime=(data.get("order_startime") or data.get("orderStartime") or "").strip(),
        order_endtime=(data.get("order_endtime") or data.get("orderEndtime") or "").strip(),
        sy_user_id=str(data.get("supplier_name") or data.get("sy_user_id") or "").strip(),
        storehouse_id=str(data.get("sale_Manager") or data.get("storehouse_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_check_create(request: Request, user=None):
    data = merge_payload(request)
    storehouse_id = _to_int(data.get("rSelect") or data.get("storehouse_id"))
    select_time = str(data.get("check_time") or data.get("selectTime") or "").strip()
    if not storehouse_id or not select_time:
        return Response(ajax_fail("请选择仓库与盘点日期"))
    uid = ""
    if user:
        uid = str(
            user.get("id")
            or user.get("userId")
            or getattr(user, "id", "")
            or ""
        )
    new_id = repo.create_inventory_check(
        storehouse_id=storehouse_id,
        select_time=select_time[:10],
        sy_user_id=uid,
    )
    return Response(ajax_ok(obj={"id": new_id}))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_check_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    repo.delete_inventory_check(row_id)
    return Response(ajax_ok())
