from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.helpers import staff_id
from apps.admin_service.repositories import apply as apply_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def buyback_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = apply_repo.list_buyback(
        state=str(data.get("state") or "").strip(),
        device_name=(data.get("device_name") or data.get("deviceName") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def buyback_update(request: Request, user=None):
    data = merge_payload(request)
    record_id = data.get("id")
    state = data.get("type") or data.get("state")
    if not record_id or state in (None, ""):
        return Response(ajax_fail("操作失败!"))
    apply_repo.update_buyback(
        record_id=int(record_id),
        state=int(state),
        operator_id=staff_id(user),
    )
    return Response(ajax_ok(res_msg="操作成功"))
