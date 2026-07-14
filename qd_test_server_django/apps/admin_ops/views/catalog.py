from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import catalog as catalog_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_int_list(value) -> list[int]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value).split(",")
    out: list[int] = []
    for item in raw:
        n = _to_int(item)
        if n is not None:
            out.append(n)
    return out


# ---------- Spec ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def spec_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_specs(
        name=(data.get("name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def spec_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    spec_id = _to_int(data.get("id"))
    if not spec_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_spec(spec_id)
    if not row:
        return Response(ajax_fail("规格不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def spec_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return Response(ajax_fail("规格名称不能为空"))
    props = data.get("properties") or data.get("propertyValues") or []
    if isinstance(props, str):
        props = [{"value": x.strip(), "sequence": i} for i, x in enumerate(props.split(",")) if x.strip()]
    sid = catalog_repo.save_spec(
        spec_id=_to_int(data.get("id")),
        name=name,
        sequence=_to_int(data.get("sequence"), 0) or 0,
        type_=(data.get("type") or "text").strip() or "text",
        is_show=_to_int(data.get("is_show") or data.get("isShow"), 1) or 0,
        properties=props if isinstance(props, list) else [],
    )
    return Response(ajax_ok(obj={"id": sid}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def spec_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    spec_id = _to_int(data.get("id") or data.get("mulitId"))
    if not spec_id:
        return Response(ajax_fail("缺少ID"))
    catalog_repo.delete_spec(spec_id)
    return Response(ajax_ok(res_msg="删除成功"))


# ---------- Brand ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_brands(
        name=(data.get("name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    brand_id = _to_int(data.get("id"))
    if not brand_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_brand(brand_id)
    if not row:
        return Response(ajax_fail("品牌不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return Response(ajax_fail("品牌名称不能为空"))
    bid = catalog_repo.save_brand(
        brand_id=_to_int(data.get("id")),
        name=name,
        first_word=(data.get("first_word") or data.get("firstWord") or "").strip()[:1].upper(),
        sequence=_to_int(data.get("sequence"), 0) or 0,
        en_name=(data.get("en_name") or data.get("enName") or "").strip(),
    )
    return Response(ajax_ok(obj={"id": bid}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    brand_id = _to_int(data.get("id") or data.get("mulitId"))
    if not brand_id:
        return Response(ajax_fail("缺少ID"))
    err = catalog_repo.delete_brand(brand_id)
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(res_msg="删除成功"))


# ---------- Type ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_types(
        name=(data.get("name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_id = _to_int(data.get("id"))
    if not type_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_type(type_id)
    if not row:
        return Response(ajax_fail("类型不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return Response(ajax_fail("类型名称不能为空"))
    tid = catalog_repo.save_type(
        type_id=_to_int(data.get("id")),
        name=name,
        sequence=_to_int(data.get("sequence"), 0) or 0,
        spec_ids=_to_int_list(data.get("spec_ids") or data.get("specIds")),
        brand_ids=_to_int_list(data.get("brand_ids") or data.get("brandIds")),
    )
    return Response(ajax_ok(obj={"id": tid}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_id = _to_int(data.get("id") or data.get("mulitId"))
    if not type_id:
        return Response(ajax_fail("缺少ID"))
    catalog_repo.delete_type(type_id)
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_options(request: Request, user=None):
    del request, user
    return Response(
        ajax_ok(
            obj={
                "specs": catalog_repo.list_spec_options(),
                "brands": catalog_repo.list_brand_options_all(),
                "types": catalog_repo.list_type_options(),
            }
        )
    )


# ---------- Class ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def class_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    rows = catalog_repo.list_classes(parent_id=data.get("parent_id") or data.get("parentId"))
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def class_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    class_id = _to_int(data.get("id"))
    if not class_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_class(class_id)
    if not row:
        return Response(ajax_fail("分类不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def class_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    class_name = (data.get("className") or data.get("class_name") or "").strip()
    if not class_name:
        return Response(ajax_fail("分类名称不能为空"))
    cid = catalog_repo.save_class(
        class_id=_to_int(data.get("id")),
        class_name=class_name,
        parent_id=_to_int(data.get("parent_id") or data.get("parentId") or data.get("pid")),
        goods_type_id=_to_int(data.get("goodsType_id") or data.get("goodsTypeId") or data.get("goods_type_id")),
        sequence=_to_int(data.get("sequence"), 0) or 0,
        display=_to_int(data.get("display"), 1) if data.get("display") not in (None, "") else 1,
        is_consum_material=_to_int(data.get("is_consumMaterial") or data.get("isConsumMaterial"), 0) or 0,
    )
    return Response(ajax_ok(obj={"id": cid}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def class_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    class_id = _to_int(data.get("id") or data.get("mulitId"))
    if not class_id:
        return Response(ajax_fail("缺少ID"))
    catalog_repo.delete_class(class_id)
    return Response(ajax_ok(res_msg="删除成功"))


# ---------- Album ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_albums(
        name=(data.get("name") or data.get("album_name") or data.get("albumName") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    album_id = _to_int(data.get("id"))
    if not album_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_album(album_id)
    if not row:
        return Response(ajax_fail("相册不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("album_name") or data.get("albumName") or "").strip()
    if not name:
        return Response(ajax_fail("相册名称不能为空"))
    aid = catalog_repo.save_album(
        album_id=_to_int(data.get("id")),
        album_name=name,
        album_sequence=_to_int(data.get("album_sequence") or data.get("albumSequence"), 0) or 0,
    )
    return Response(ajax_ok(obj={"id": aid}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    album_id = _to_int(data.get("id") or data.get("mulitId"))
    if not album_id:
        return Response(ajax_fail("缺少ID"))
    err = catalog_repo.delete_album(album_id)
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_images(request: Request, user=None):
    del user
    data = merge_payload(request)
    album_id = _to_int(data.get("id") or data.get("album_id") or data.get("albumId"))
    if not album_id:
        return Response(ajax_fail("缺少相册ID"))
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_album_images(album_id, page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_image_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    image_id = _to_int(data.get("id") or data.get("image_id"))
    if not image_id:
        return Response(ajax_fail("缺少图片ID"))
    catalog_repo.delete_album_image(image_id)
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def album_cover(request: Request, user=None):
    del user
    data = merge_payload(request)
    album_id = _to_int(data.get("album_id") or data.get("albumId") or data.get("id"))
    image_id = _to_int(data.get("image_id") or data.get("imageId") or data.get("cover_id"))
    if not album_id or not image_id:
        return Response(ajax_fail("缺少参数"))
    catalog_repo.set_album_cover(album_id, image_id)
    return Response(ajax_ok(res_msg="设置成功"))


# ---------- Evaluate ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = catalog_repo.list_evaluates(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    evaluate_id = _to_int(data.get("id"))
    if not evaluate_id:
        return Response(ajax_fail("缺少ID"))
    row = catalog_repo.get_evaluate(evaluate_id)
    if not row:
        return Response(ajax_fail("评价不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def evaluate_check(request: Request, user=None):
    del user
    data = merge_payload(request)
    evaluate_id = _to_int(data.get("id"))
    if not evaluate_id:
        return Response(ajax_fail("缺少ID"))
    # Java: type 控制显示/不显示
    typ = data.get("type")
    status = None
    if typ not in (None, ""):
        status = _to_int(typ)
    next_val = catalog_repo.toggle_evaluate_status(evaluate_id, status)
    if next_val is None:
        return Response(ajax_fail("评价不存在"))
    return Response(ajax_ok(obj={"evaluateStatus": next_val}, res_msg="操作成功"))


# ---------- Consult config ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def consult_config_get(request: Request, user=None):
    del request, user
    return Response(ajax_ok(obj=catalog_repo.get_consult_config()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def consult_config_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    cfg_id = catalog_repo.save_consult_config(
        {
            "id": _to_int(data.get("id")),
            "qd_name": (data.get("qdName") or data.get("qd_name") or "").strip(),
            "service_mobile": (data.get("serviceMobile") or data.get("service_mobile") or "").strip(),
            "qd_fax": (data.get("qdFax") or data.get("qd_fax") or "").strip(),
            "qd_address": (data.get("qdAddress") or data.get("qd_address") or "").strip(),
            "qd_email": (data.get("qdEmail") or data.get("qd_email") or "").strip(),
        }
    )
    return Response(ajax_ok(obj={"id": cfg_id}, res_msg="咨询方式设置成功"))
