from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import whitelist as whitelist_repo
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
def whitelist_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = whitelist_repo.list_whitelist(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def whitelist_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    item_id = _to_int(data.get("id"))
    if not item_id:
        return Response(ajax_fail("参数错误"))
    row = whitelist_repo.get_whitelist(item_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def add_whitelist(request: Request, user=None):
    del user
    data = merge_payload(request)
    syuser_id = str(data.get("syuser_id") or data.get("syuserId") or "").strip()
    wl_type = _to_int(data.get("type"), 1)
    if not syuser_id:
        return Response(ajax_fail("请选择用户"))
    if wl_type not in (1, 2):
        return Response(ajax_fail("类型错误"))
    if whitelist_repo.exists_user_type(syuser_id, wl_type):
        return Response(ajax_fail("该用户已存在相同类型白名单"))
    whitelist_repo.insert_whitelist(syuser_id=syuser_id, wl_type=wl_type)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def update_whitelist(request: Request, user=None):
    del user
    data = merge_payload(request)
    item_id = _to_int(data.get("id"))
    syuser_id = str(data.get("syuser_id") or data.get("syuserId") or "").strip()
    wl_type = _to_int(data.get("type"), 1)
    if not item_id or not syuser_id:
        return Response(ajax_fail("参数错误"))
    if wl_type not in (1, 2):
        return Response(ajax_fail("类型错误"))
    if whitelist_repo.exists_user_type(syuser_id, wl_type, exclude_id=item_id):
        return Response(ajax_fail("该用户已存在相同类型白名单"))
    whitelist_repo.update_whitelist(item_id=item_id, syuser_id=syuser_id, wl_type=wl_type)
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def delete_whitelist(request: Request, user=None):
    del user
    data = merge_payload(request)
    item_id = _to_int(data.get("id"))
    if not item_id:
        return Response(ajax_fail("参数错误"))
    affected = whitelist_repo.delete_whitelist(item_id)
    if affected > 0:
        return Response(ajax_ok(res_msg="删除成功"))
    return Response(ajax_fail("删除失败"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sy_user_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    keyword = (data.get("keyword") or data.get("q") or "").strip()
    return Response(ajax_ok(obj=whitelist_repo.list_sy_users(keyword)))
