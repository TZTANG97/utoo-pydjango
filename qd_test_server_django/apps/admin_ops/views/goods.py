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
