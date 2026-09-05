from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import goods as goods_repo
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
def goods_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = goods_repo.list_goods(
        goods_name=(
            data.get("q_goods_name")
            or data.get("goods_name")
            or data.get("goodsName")
            or ""
        ).strip(),
        gc_id=data.get("q_goods.gc.id") or data.get("gc_id") or data.get("gcId"),
        goods_brand_id=(
            data.get("q_goods.goods_brand.id")
            or data.get("goods_brand_id")
            or data.get("goodsBrandId")
        ),
        goods_recommend=data.get("q_goods_recommend") or data.get("goods_recommend"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_brand_options(request: Request, user=None):
    del request, user
    return Response(ajax_ok(obj=goods_repo.list_brand_options()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_class_options(request: Request, user=None):
    del request, user
    return Response(ajax_ok(obj=goods_repo.list_class_options()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def update_recommend(request: Request, user=None):
    del user
    data = merge_payload(request)
    goods_id = _to_int(data.get("id"))
    if not goods_id:
        return Response(ajax_fail("缺少商品ID"))
    next_val = goods_repo.toggle_recommend(goods_id)
    if next_val is None:
        return Response(ajax_fail("商品不存在"))
    return Response(ajax_ok(obj={"goodsRecommend": next_val}, res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_sale(request: Request, user=None):
    del user
    data = merge_payload(request)
    goods_id = _to_int(data.get("id") or data.get("mulitId"))
    if not goods_id:
        return Response(ajax_fail("缺少商品ID"))
    next_val = goods_repo.toggle_sale(goods_id)
    if next_val is None:
        return Response(ajax_fail("商品不存在"))
    return Response(ajax_ok(obj={"goodsStatus": next_val}, res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    goods_id = _to_int(data.get("id"))
    if not goods_id:
        return Response(ajax_fail("缺少商品ID"))
    row = goods_repo.get_goods(goods_id)
    if not row:
        return Response(ajax_fail("商品不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_options(request: Request, user=None):
    """关联配件搜索。"""
    del user
    data = merge_payload(request)
    keyword = (data.get("keyword") or data.get("q") or data.get("goods_name") or "").strip()
    rows = goods_repo.search_goods_options(keyword=keyword)
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_save(request: Request, user=None):
    data = merge_payload(request)
    goods_name = (data.get("goods_name") or data.get("goodsName") or "").strip()
    if not goods_name:
        return Response(ajax_fail("请填写商品名称"))
    gc_id = _to_int(data.get("gc_id") or data.get("gcId") or data.get("goods_class_id"))
    brand_id = _to_int(
        data.get("goods_brand_id") or data.get("goodsBrandId") or data.get("goods_brand")
    )
    if not gc_id:
        return Response(ajax_fail("请选择分类"))
    if not brand_id:
        return Response(ajax_fail("请选择品牌"))

    add_user_id = None
    if isinstance(user, dict):
        add_user_id = _to_int(user.get("id") or user.get("user_id"))

    form_mode = str(data.get("formMode") or data.get("form_mode") or "full").strip().lower()
    try:
        new_id = goods_repo.save_goods(
            goods_id=_to_int(data.get("id")),
            edit_type=str(data.get("editType") or data.get("edit_type") or ""),
            form_mode=form_mode,
            goods_name=goods_name,
            en_name=(data.get("en_name") or data.get("enName") or "").strip(),
            goods_details=data.get("goods_details") or data.get("goodsDetails") or "",
            goods_price=data.get("goods_price") if "goods_price" in data else data.get("goodsPrice"),
            store_price=data.get("store_price") if "store_price" in data else data.get("storePrice"),
            local_price=data.get("local_price") if "local_price" in data else data.get("localPrice"),
            goods_inventory=data.get("goods_inventory")
            if "goods_inventory" in data
            else data.get("goodsInventory"),
            goods_serial=(data.get("goods_serial") or data.get("goodsSerial") or "").strip(),
            goods_status=data.get("goods_status") if "goods_status" in data else data.get("goodsStatus"),
            goods_recommend=data.get("goods_recommend")
            if "goods_recommend" in data
            else data.get("goodsRecommend"),
            inventory_type=(data.get("inventory_type") or data.get("inventoryType") or "all"),
            goods_spec=(data.get("goods_spec") or data.get("goodsSpec") or "").strip(),
            gc_id=gc_id,
            goods_brand_id=brand_id,
            goods_main_photo_id=_to_int(
                data.get("goods_main_photo_id") or data.get("goodsMainPhotoId")
            ),
            is_calibration=data.get("is_calibration")
            if "is_calibration" in data
            else data.get("isCalibration"),
            is_maintenance=data.get("is_maintenance")
            if "is_maintenance" in data
            else data.get("isMaintenance"),
            is_install=data.get("is_install") if "is_install" in data else data.get("isInstall"),
            is_secondhand=data.get("is_secondhand")
            if "is_secondhand" in data
            else data.get("isSecondhand"),
            is_lease=data.get("is_lease") if "is_lease" in data else data.get("isLease"),
            zdqzr=data.get("zdqzr"),
            relation_goods=str(data.get("relation_goods") or data.get("relationGoods") or ""),
            head_user_id=str(data.get("head_user_id") or data.get("headUserId") or ""),
            local_type=str(data.get("local_type") or data.get("localType") or "4"),
            goods_time=data.get("goods_time") if "goods_time" in data else data.get("goodsTime"),
            goods_choice_type=data.get("goods_choice_type")
            if "goods_choice_type" in data
            else data.get("goodsChoiceType"),
            skus=data.get("skus"),
            add_user_id=add_user_id,
        )
    except Exception as exc:  # noqa: BLE001
        return Response(ajax_fail(f"保存失败：{exc}"))
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))
