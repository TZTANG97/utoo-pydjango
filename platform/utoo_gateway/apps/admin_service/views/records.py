from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.repositories import records as records_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def records_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = records_repo.list_records(
        user_id=str(data.get("trueName") or data.get("userId") or data.get("user_id") or "").strip(),
        keywords=(data.get("keywords") or "").strip(),
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
def records_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    record_id = data.get("id")
    if not record_id:
        return Response(ajax_fail("数据错误"))
    row = records_repo.get_record(int(record_id))
    if not row:
        return Response(ajax_fail("记录不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def records_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    record_id = data.get("id")
    if not record_id:
        return Response(ajax_fail("数据错误"))
    affected = records_repo.delete_record(int(record_id))
    if affected > 0:
        return Response(ajax_ok(res_msg="删除成功！"))
    return Response(ajax_fail("删除失败"))
