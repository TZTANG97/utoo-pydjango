from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import area as area_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def area_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = area_repo.list_areas(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def area_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    area_name = (data.get("areaName") or data.get("area_name") or "").strip()
    if not area_name:
        return Response(ajax_fail("请填写区域名称"))
    if area_repo.find_by_name(area_name):
        return Response(ajax_fail("区域名称已存在，请勿重复添加"))
    area_repo.insert_area(area_name)
    return Response(ajax_ok(res_msg="添加成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def area_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    area_id = data.get("id")
    area_name = (data.get("areaName") or data.get("area_name") or "").strip()
    if not area_id or not area_name:
        return Response(ajax_fail("参数错误"))
    if area_repo.find_by_name(area_name, exclude_id=int(area_id)):
        return Response(ajax_fail("区域名称已存在，请更换名称"))
    area_repo.update_area_name(int(area_id), area_name)
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def area_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    area_id = data.get("id")
    if not area_id:
        return Response(ajax_fail("参数错误"))
    area_repo.soft_delete_area(int(area_id))
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def area_options(_request: Request, user=None):
    del user
    return ajax_response(True, obj=area_repo.list_area_options())
