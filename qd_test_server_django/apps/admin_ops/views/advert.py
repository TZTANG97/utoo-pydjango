from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import advert as advert_repo
from apps.admin_system.views.common import merge_payload, split_ids
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _advert_fields(data: dict) -> dict:
    return {
        "ad_title": (data.get("ad_title") or data.get("adTitle") or "").strip(),
        "ad_ap_id": _to_int(data.get("ad_ap_id") or data.get("adApId")),
        "ad_begin_time": data.get("ad_begin_time") or data.get("adBeginTime") or None,
        "ad_end_time": data.get("ad_end_time") or data.get("adEndTime") or None,
        "ad_url": (data.get("ad_url") or data.get("adUrl") or "").strip() or None,
        "ad_text": (data.get("ad_text") or data.get("adText") or "").strip() or None,
        "ad_slide_sequence": _to_int(data.get("ad_slide_sequence") or data.get("adSlideSequence"), 0) or 0,
        "mark": _to_int(data.get("mark"), 1) or 1,
        "ad_type": (data.get("ad_type") or data.get("adType") or "").strip() or None,
        "ad_type_value": (data.get("ad_type_value") or data.get("adTypeValue") or "").strip() or None,
        "ad_acc_id": _to_int(data.get("ad_acc_id") or data.get("adAccId") or data.get("manage_main_photo_id")),
    }


def _pos_fields(data: dict) -> dict:
    return {
        "ap_title": (data.get("ap_title") or data.get("apTitle") or "").strip(),
        "ap_content": (data.get("ap_content") or data.get("apContent") or "").strip() or None,
        "ap_type": (data.get("ap_type") or data.get("apType") or "img").strip() or "img",
        "ap_status": _to_int(data.get("ap_status") or data.get("apStatus"), 1) or 0,
        "ap_use_status": _to_int(data.get("ap_use_status") or data.get("apUseStatus"), 0) or 0,
        "ap_width": _to_int(data.get("ap_width") or data.get("apWidth"), 0) or 0,
        "ap_height": _to_int(data.get("ap_height") or data.get("apHeight"), 0) or 0,
        "ap_price": _to_int(data.get("ap_price") or data.get("apPrice"), 0) or 0,
        "ap_sys_type": _to_int(data.get("ap_sys_type") or data.get("apSysType"), 1) or 0,
        "ap_show_type": _to_int(data.get("ap_show_type") or data.get("apShowType"), 0) or 0,
        "ap_acc_url": (data.get("ap_acc_url") or data.get("apAccUrl") or "").strip() or None,
        "ap_text": (data.get("ap_text") or data.get("apText") or "").strip() or None,
        "ap_code": (data.get("ap_code") or data.get("apCode") or "").strip() or None,
        "mark": _to_int(data.get("mark"), 1) or 1,
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def advert_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = advert_repo.list_adverts(
        ad_title=(data.get("ad_title") or data.get("adTitle") or "").strip(),
        mark=data.get("mark"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def advert_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    advert_id = _to_int(data.get("id"))
    if not advert_id:
        return Response(ajax_fail("参数错误"))
    row = advert_repo.get_advert(advert_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def advert_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    fields = _advert_fields(data)
    if not fields["ad_title"]:
        return Response(ajax_fail("请填写广告标题"))
    advert_id = _to_int(data.get("id"))
    if advert_id:
        advert_repo.update_advert(advert_id, fields)
        return Response(ajax_ok(res_msg="修改成功"))
    advert_repo.insert_advert(fields)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def advert_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    ids = [_to_int(x) for x in split_ids(data.get("mulitId") or data.get("id")) if _to_int(x)]
    if not ids:
        return Response(ajax_fail("参数错误"))
    advert_repo.delete_adverts(ids)
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def adv_pos_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = advert_repo.list_adv_pos(
        ap_title=(data.get("ap_title") or data.get("apTitle") or "").strip(),
        mark=data.get("mark"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def adv_pos_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    pos_id = _to_int(data.get("id"))
    if not pos_id:
        return Response(ajax_fail("参数错误"))
    row = advert_repo.get_adv_pos(pos_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def adv_pos_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    fields = _pos_fields(data)
    if not fields["ap_title"]:
        return Response(ajax_fail("请填写广告位标题"))
    pos_id = _to_int(data.get("id"))
    if pos_id:
        advert_repo.update_adv_pos(pos_id, fields)
        return Response(ajax_ok(res_msg="修改成功"))
    advert_repo.insert_adv_pos(fields)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def adv_pos_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    ids = [_to_int(x) for x in split_ids(data.get("mulitId") or data.get("id")) if _to_int(x)]
    if not ids:
        return Response(ajax_fail("参数错误"))
    advert_repo.delete_adv_pos(ids)
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def adv_pos_options(request: Request, user=None):
    del user
    del request
    return Response(ajax_ok(obj=advert_repo.list_adv_pos_options()))
