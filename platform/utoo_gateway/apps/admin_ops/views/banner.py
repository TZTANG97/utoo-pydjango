from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import banner as banner_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _banner_fields(data: dict, *, banner_type: int | None = None) -> dict:
    bt = _to_int(data.get("banner_type") or data.get("bannerType"), banner_type)
    return {
        "banner_id": _to_int(data.get("manage_main_photo_id") or data.get("banner_id") or data.get("bannerId")),
        "sort": _to_int(data.get("sort"), 0) or 0,
        "is_show": _to_int(data.get("is_show") or data.get("isShow"), 1) or 0,
        "title": (data.get("title") or "").strip(),
        "badescribe": (data.get("badescribe") or "").strip(),
        "subheading": (data.get("subheading") or "").strip(),
        "titlesize": (data.get("titlesize") or "").strip() or None,
        "titlecolor": (data.get("titlecolor") or "").strip() or None,
        "badescribesize": (data.get("badescribesize") or "").strip() or None,
        "badescribecolor": (data.get("badescribecolor") or "").strip() or None,
        "subheadingsize": (data.get("subheadingsize") or "").strip() or None,
        "subheadingcolor": (data.get("subheadingcolor") or "").strip() or None,
        "project_class": (data.get("project_class") or data.get("projectClass") or "").strip() or None,
        "website": (data.get("website") or "").strip() or None,
        "banner_type": bt if bt is not None else 0,
        "platform_type": _to_int(data.get("platformType") or data.get("platform_type"), 1) or 1,
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def photolist(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    banner_type = _to_int(data.get("banner_type") or data.get("bannerType"), 0)
    rows, total = banner_repo.list_banners(banner_type=banner_type, page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def xcxfmlist(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = banner_repo.list_banners(banner_type=2, page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def banner_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    bid = _to_int(data.get("bid") or data.get("id"))
    if not bid:
        return Response(ajax_fail("参数错误"))
    row = banner_repo.get_banner(bid)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def slidecreate(request: Request, user=None):
    del user
    data = merge_payload(request)
    fields = _banner_fields(data, banner_type=_to_int(data.get("banner_type"), 0))
    if not fields["banner_id"]:
        return Response(ajax_fail("请选择图片"))
    banner_repo.insert_banner(fields)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def slideupdate(request: Request, user=None):
    del user
    data = merge_payload(request)
    bid = _to_int(data.get("bid") or data.get("id"))
    if not bid:
        return Response(ajax_fail("参数错误"))
    fields = _banner_fields(data)
    if not fields["banner_id"]:
        return Response(ajax_fail("请选择图片"))
    banner_repo.update_banner(bid, fields)
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def xcxfmslidecreate(request: Request, user=None):
    del user
    data = merge_payload(request)
    fields = _banner_fields(data, banner_type=2)
    fields["banner_type"] = 2
    if not fields["banner_id"]:
        return Response(ajax_fail("请选择图片"))
    banner_repo.insert_banner(fields)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def xcxfmslideupdate(request: Request, user=None):
    del user
    data = merge_payload(request)
    bid = _to_int(data.get("bid") or data.get("id"))
    if not bid:
        return Response(ajax_fail("参数错误"))
    fields = _banner_fields(data, banner_type=2)
    fields["banner_type"] = 2
    if not fields["banner_id"]:
        return Response(ajax_fail("请选择图片"))
    banner_repo.update_banner(bid, fields)
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def del_banner(request: Request, user=None):
    del user
    data = merge_payload(request)
    bid = _to_int(data.get("id") or data.get("bid"))
    if not bid:
        return Response(ajax_fail("参数错误"))
    affected = banner_repo.delete_banner(bid)
    if affected > 0:
        return Response(ajax_ok(res_msg="删除成功"))
    return Response(ajax_fail("删除失败"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def updateisshow(request: Request, user=None):
    del user
    data = merge_payload(request)
    bid = _to_int(data.get("id") or data.get("bid"))
    if not bid:
        return Response(ajax_fail("参数错误"))
    row = banner_repo.get_banner(bid)
    if not row:
        return Response(ajax_fail("数据不存在"))
    current = int(row.get("isShow") or 0)
    next_val = 0 if current == 1 else 1
    banner_repo.update_isshow(bid, next_val)
    return Response(ajax_ok(obj={"isShow": next_val}, res_msg="操作成功"))
