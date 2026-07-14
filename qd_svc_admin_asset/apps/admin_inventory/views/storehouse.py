from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_inventory.repositories import storehouse as repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _store_payload(data: dict) -> dict:
    return {
        "store_num": (data.get("storeNum") or data.get("store_num") or "").strip(),
        "store_name": (data.get("storeName") or data.get("store_name") or "").strip(),
        "store_userid": str(data.get("storeUserid") or data.get("store_userid") or "").strip() or None,
        "moblie": (data.get("moblie") or data.get("mobile") or "").strip(),
        "address": (data.get("address") or "").strip(),
        "mark": (data.get("mark") or "").strip(),
        "status": _to_int(data.get("status"), 1) or 1,
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def storehouse_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = repo.list_storehouses(
        store_name=(data.get("storeName") or data.get("store_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or data.get("userName") or "").strip(),
        mobile=(data.get("moblie") or data.get("mobile") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def storehouse_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    row = repo.get_storehouse(row_id)
    if not row:
        return Response(ajax_fail("仓库不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def storehouse_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _store_payload(data)
    if not payload["store_name"]:
        return Response(ajax_fail("仓库名称不能为空"))
    row_id = _to_int(data.get("id"))
    if row_id:
        repo.update_storehouse(row_id, payload)
        return Response(ajax_ok(msg="更新成功"))
    new_id = repo.insert_storehouse(payload)
    return Response(ajax_ok(msg="保存成功", obj={"id": new_id}))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def storehouse_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    status = _to_int(data.get("shstatus") or data.get("status"))
    if not row_id or status is None:
        return Response(ajax_fail("参数错误"))
    repo.set_storehouse_status(row_id, status)
    return Response(ajax_ok(msg="状态已更新"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def storehouse_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    repo.soft_delete_storehouse(row_id)
    return Response(ajax_ok(msg="删除成功"))


def _sample_payload(data: dict, store_type: int) -> dict:
    base = _store_payload(data)
    base["type"] = store_type
    return base


def _sample_list(request: Request, store_type: int):
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    st = _to_int(data.get("type"), store_type) or store_type
    rows, total = repo.list_sample_storehouses(
        store_type=st,
        store_name=(data.get("storeName") or data.get("sample_store_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("userName") or "").strip(),
        mobile=(data.get("moblie") or data.get("mobile") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_storehouse_list(request: Request, user=None):
    del user
    return _sample_list(request, 1)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_remain_storehouse_list(request: Request, user=None):
    del user
    return _sample_list(request, 2)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_storehouse_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    row = repo.get_sample_storehouse(row_id)
    if not row:
        return Response(ajax_fail("仓库不存在"))
    return Response(ajax_ok(obj=row))


def _sample_save(request: Request, store_type: int):
    data = merge_payload(request)
    st = _to_int(data.get("type"), store_type) or store_type
    payload = _sample_payload(data, st)
    if not payload["store_name"]:
        return Response(ajax_fail("仓库名称不能为空"))
    row_id = _to_int(data.get("id"))
    if row_id:
        repo.update_sample_storehouse(row_id, payload)
        return Response(ajax_ok(msg="更新成功"))
    new_id = repo.insert_sample_storehouse(payload)
    return Response(ajax_ok(msg="保存成功", obj={"id": new_id}))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_storehouse_save(request: Request, user=None):
    del user
    return _sample_save(request, 1)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_remain_storehouse_save(request: Request, user=None):
    del user
    return _sample_save(request, 2)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_storehouse_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    status = _to_int(data.get("shstatus") or data.get("status"))
    if not row_id or status is None:
        return Response(ajax_fail("参数错误"))
    repo.set_sample_storehouse_status(row_id, status)
    return Response(ajax_ok(msg="状态已更新"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_storehouse_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    repo.soft_delete_sample_storehouse(row_id)
    return Response(ajax_ok(msg="删除成功"))
