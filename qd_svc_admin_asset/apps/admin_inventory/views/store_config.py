from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_inventory.repositories import store_config as cfg
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _truthy(value) -> bool:
    if value in (True, 1, "1", "true", "True", "on", "yes"):
        return True
    return False


def _block_list(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    store_id = _to_int(data.get("store_id") or data.get("storeId"))
    if not store_id:
        return Response(ajax_fail("参数错误"))
    rows, total = cfg.list_blocks(kind=kind, store_id=store_id, page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


def _block_options(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    store_id = _to_int(data.get("store_id") or data.get("storeId"))
    if not store_id:
        return Response(ajax_fail("参数错误,请重试"))
    return Response(ajax_ok(obj=cfg.list_block_options(kind=kind, store_id=store_id)))


def _add_block(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    store_id = _to_int(data.get("store_id") or data.get("storeId"))
    block = str(data.get("block") or "").strip()
    if not store_id:
        return Response(ajax_fail("参数错误"))
    ok, msg = cfg.add_block(kind=kind, store_id=store_id, block=block)
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(msg="添加成功"))


def _position_list(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    store_id = _to_int(data.get("store_id") or data.get("storeId"))
    if not store_id:
        return Response(ajax_fail("参数错误"))
    rows, total = cfg.list_positions(
        kind=kind,
        store_id=store_id,
        block_pos=str(data.get("block_pos") or data.get("blockPos") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


def _add_position(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    store_id = _to_int(data.get("store_id") or data.get("storeId"))
    block_id = _to_int(data.get("block") or data.get("block_id") or data.get("blockId"))
    if not store_id or not block_id:
        return Response(ajax_fail("请选择地块名!"))
    ok, msg = cfg.add_positions(
        kind=kind,
        store_id=store_id,
        block_id=block_id,
        number=str(data.get("number") or "").strip(),
        batch=_truthy(data.get("all")),
        start_number=str(data.get("startnumber") or data.get("startNumber") or "").strip(),
        end_number=str(data.get("endnumber") or data.get("endNumber") or "").strip(),
        char_number=str(data.get("charnumber") or data.get("charNumber") or "").strip(),
    )
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(msg="添加成功"))


def _del_position(request: Request, kind: cfg.Kind):
    data = merge_payload(request)
    pos_id = _to_int(data.get("id"))
    if not pos_id:
        return Response(ajax_fail("参数错误"))
    ok, msg = cfg.soft_delete_position(kind=kind, pos_id=pos_id)
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(msg=msg))


def _qr_payload(request: Request, kind: cfg.Kind, retain: bool = False):
    data = merge_payload(request)
    pos_id = _to_int(data.get("id"))
    if not pos_id:
        return Response(ajax_fail("参数错误"))
    ok, text = cfg.get_qr_payload(kind=kind, pos_id=pos_id, retain=retain)
    if not ok:
        return Response(ajax_fail(text))
    return Response(ajax_ok(obj={"text": text}))


# ---- 普通仓库 /storeHouse ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_store_block_list(request: Request, user=None):
    del user
    return _block_list(request, "goods")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_query_store_block(request: Request, user=None):
    del user
    return _block_options(request, "goods")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_add_store_block(request: Request, user=None):
    del user
    return _add_block(request, "goods")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_store_position_list(request: Request, user=None):
    del user
    return _position_list(request, "goods")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_add_store_pos(request: Request, user=None):
    del user
    return _add_position(request, "goods")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_del_store_pos(request: Request, user=None):
    del user
    return _del_position(request, "goods")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_gen_qrcode(request: Request, user=None):
    del user
    return _qr_payload(request, "goods", retain=False)


# ---- 样品仓库 /samplestoreHouse ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_store_block_list(request: Request, user=None):
    del user
    return _block_list(request, "sample")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_query_store_block(request: Request, user=None):
    del user
    return _block_options(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_add_store_block(request: Request, user=None):
    del user
    return _add_block(request, "sample")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_store_position_list(request: Request, user=None):
    del user
    return _position_list(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_add_store_pos(request: Request, user=None):
    del user
    return _add_position(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_del_store_pos(request: Request, user=None):
    del user
    return _del_position(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_del_sample_goods(request: Request, user=None):
    del user
    data = merge_payload(request)
    pos_id = _to_int(data.get("id"))
    if not pos_id:
        return Response(ajax_fail("参数错误"))
    ok, msg = cfg.clear_sample_goods(pos_id=pos_id)
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(msg=msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_gen_qrcode(request: Request, user=None):
    del user
    return _qr_payload(request, "sample", retain=False)


# ---- 样品留存仓库 /sampleremainstoreHouse（同表，QR 前缀不同）----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_store_block_list(request: Request, user=None):
    del user
    return _block_list(request, "sample")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_query_store_block(request: Request, user=None):
    del user
    return _block_options(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_add_store_block(request: Request, user=None):
    del user
    return _add_block(request, "sample")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_store_position_list(request: Request, user=None):
    del user
    return _position_list(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_add_store_pos(request: Request, user=None):
    del user
    return _add_position(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_del_store_pos(request: Request, user=None):
    del user
    return _del_position(request, "sample")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_del_sample_goods(request: Request, user=None):
    del user
    data = merge_payload(request)
    pos_id = _to_int(data.get("id"))
    if not pos_id:
        return Response(ajax_fail("参数错误"))
    ok, msg = cfg.clear_sample_goods(pos_id=pos_id)
    if not ok:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(msg=msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def remain_gen_qrcode(request: Request, user=None):
    del user
    return _qr_payload(request, "sample", retain=True)
