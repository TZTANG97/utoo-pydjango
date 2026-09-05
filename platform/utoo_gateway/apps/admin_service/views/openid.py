from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.repositories import openid as openid_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def openid_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = openid_repo.list_openids(
        openid=(data.get("openid") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def submit_openid(request: Request, user=None):
    del user
    data = merge_payload(request)
    openid = (data.get("openid") or "").strip()
    if not openid:
        return Response(ajax_fail("保存失败,没有数据，请确认!"))
    new_id = openid_repo.insert_openid(openid)
    return Response(ajax_ok(res_msg=str(new_id)))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def openid_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    record_id = data.get("id")
    if not record_id:
        return Response(ajax_fail("操作失败!"))
    openid_repo.soft_delete_openid(int(record_id))
    return Response(ajax_ok(res_msg="操作成功!"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def update_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    record_id = data.get("id")
    status = str(data.get("status") or "")
    if not record_id or not status:
        return Response(False)
    enabled = status == "1"
    ok = openid_repo.update_openid_status(int(record_id), enabled=enabled)
    return Response(ok)
