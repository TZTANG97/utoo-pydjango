from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import entry as entry_repo
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
def entry_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = entry_repo.list_entries(
        is_audit=data.get("isAudit") or data.get("is_audit"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def entry_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    entry_id = _to_int(data.get("id"))
    if not entry_id:
        return Response(ajax_fail("参数错误"))
    row = entry_repo.get_entry(entry_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def audit_entry(request: Request, user=None):
    del user
    data = merge_payload(request)
    entry_id = _to_int(data.get("id"))
    if not entry_id:
        return Response(ajax_fail("参数错误"))
    next_val = entry_repo.toggle_entry_audit(entry_id)
    if next_val is None:
        return Response(ajax_fail("帖子不存在"))
    return Response(ajax_ok(obj={"isAudit": next_val}, res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def comment_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = entry_repo.list_comments(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def comment_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    comment_id = _to_int(data.get("id"))
    if not comment_id:
        return Response(ajax_fail("参数错误"))
    row = entry_repo.get_comment(comment_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def audit_comment(request: Request, user=None):
    del user
    data = merge_payload(request)
    comment_id = _to_int(data.get("id"))
    if not comment_id:
        return Response(ajax_fail("参数错误"))
    ok, msg = entry_repo.audit_comment(comment_id)
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(res_msg=msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def delete_comment(request: Request, user=None):
    del user
    data = merge_payload(request)
    comment_id = _to_int(data.get("id"))
    if not comment_id:
        return Response(ajax_fail("参数错误"))
    affected = entry_repo.delete_comment(comment_id)
    if affected > 0:
        return Response(ajax_ok(res_msg="删除成功"))
    return Response(ajax_fail("删除失败"))
