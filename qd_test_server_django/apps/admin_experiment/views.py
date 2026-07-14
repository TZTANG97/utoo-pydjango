"""后台实验管理 API（主数据 + 订单列表/详情/抢单/审核/导出）。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.admin_ajax import admin_ajax_view, fail, ok
from apps.admin_experiment.helpers import (
    datatable_payload,
    merge_payload,
    parse_datatable_params,
    to_int,
)
from apps.admin_experiment.repositories import master as master_repo
from apps.admin_experiment.repositories import orders as order_repo
from apps.core.responses import ajax_ok


# ---------- health ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_probe(request: Request):
    del request
    return ok(
        {
            "module": "admin_experiment",
            "status": "ready",
            "note": "实验管理后台 API 已就绪",
        }
    )


# ---------- experiment_manage ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    type_ = to_int(data.get("type"), 1) or 1
    rows, total = master_repo.list_manages(
        type_=type_,
        name=(data.get("name") or "").strip(),
        parent_id=str(data.get("parentId") or data.get("parent_id") or "").strip(),
        first_id=str(data.get("firstId") or data.get("first_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    row = master_repo.get_manage(row_id)
    if not row:
        return fail("记录不存在")
    return ok(row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return fail("名称不能为空")
    type_ = to_int(data.get("type"), 1) or 1
    parent_id = to_int(data.get("parentId") or data.get("parent_id"))
    if type_ > 1 and not parent_id:
        return fail("请选择上级类目")
    payload = {
        "name": name,
        "sequence": to_int(data.get("sequence"), 0) or 0,
        "type": type_,
        "parent_id": parent_id,
        "pt_type": to_int(data.get("ptType") or data.get("pt_type"), 0) or 0,
        "intro": (data.get("intro") or "").strip(),
    }
    row_id = to_int(data.get("id"))
    new_id = master_repo.save_manage(payload, row_id=row_id)
    return ok({"id": new_id}, res_msg="保存成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    status = to_int(data.get("status"), 1)
    if not row_id or status is None:
        return fail("参数错误")
    master_repo.set_manage_status(row_id, status)
    return ok(res_msg="操作成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    master_repo.soft_delete_manage(row_id)
    return ok(res_msg="删除成功")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def manage_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_ = to_int(data.get("type"), 1) or 1
    parent_id = str(data.get("parentId") or data.get("parent_id") or "").strip()
    return ok(master_repo.list_manage_options(type_, parent_id))


# ---------- experiment_project ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = master_repo.list_projects(
        name=(data.get("name") or data.get("projectName") or "").strip(),
        first_id=str(data.get("firstId") or data.get("first_id") or "").strip(),
        sec_id=str(data.get("secId") or data.get("sec_id") or "").strip(),
        third_id=str(data.get("thirdId") or data.get("third_id") or data.get("classId") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    row = master_repo.get_project(row_id)
    if not row:
        return fail("记录不存在")
    return ok(row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("projectName") or data.get("project_name") or data.get("name") or "").strip()
    class_id = to_int(data.get("classId") or data.get("class_id") or data.get("thirdId"))
    if not name:
        return fail("项目名称不能为空")
    if not class_id:
        return fail("请选择三级类目")
    row_id = to_int(data.get("id"))
    new_id = master_repo.save_project(
        {"project_name": name, "class_id": class_id},
        row_id=row_id,
    )
    return ok({"id": new_id}, res_msg="保存成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def project_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    master_repo.soft_delete_project(row_id)
    return ok(res_msg="删除成功")


# ---------- experiment_goods ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = master_repo.list_goods(
        name=(data.get("name") or data.get("goodsName") or "").strip(),
        brand_id=str(data.get("brandId") or data.get("brand_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    row = master_repo.get_goods(row_id)
    if not row:
        return fail("记录不存在")
    return ok(row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("goodsName") or data.get("goods_name") or data.get("name") or "").strip()
    if not name:
        return fail("产品名称不能为空")
    brand_id = to_int(data.get("brandId") or data.get("brand_id") or data.get("goods_brand_id"))
    row_id = to_int(data.get("id"))
    new_id = master_repo.save_goods(
        {
            "goods_name": name,
            "goods_brand_id": brand_id,
            "goods_model": (data.get("goodsModel") or data.get("goods_model") or "").strip(),
        },
        row_id=row_id,
    )
    return ok({"id": new_id}, res_msg="保存成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def goods_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    master_repo.soft_delete_goods(row_id)
    return ok(res_msg="删除成功")


# ---------- goodsbrand type=2 ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = master_repo.list_exp_brands(
        name=(data.get("name") or "").strip(),
        add_time=(data.get("addTime") or data.get("add_time") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    row = master_repo.get_exp_brand(row_id)
    if not row:
        return fail("记录不存在")
    return ok(row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    if not name:
        return fail("品牌名称不能为空")
    first_word = (data.get("firstWord") or data.get("first_word") or "").strip()[:1]
    row_id = to_int(data.get("id"))
    new_id = master_repo.save_exp_brand(
        {
            "name": name,
            "first_word": first_word,
            "sequence": to_int(data.get("sequence"), 0) or 0,
            "en_name": (data.get("enName") or data.get("en_name") or "").strip(),
        },
        row_id=row_id,
    )
    return ok({"id": new_id}, res_msg="保存成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    master_repo.soft_delete_exp_brand(row_id)
    return ok(res_msg="删除成功")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def brand_options(request: Request, user=None):
    del user, request
    return ok(master_repo.list_exp_brand_options())


# ---------- sample_attribute_manage ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    type_ = to_int(data.get("type"), 1) or 1
    rows, total = master_repo.list_sample_attrs(
        type_=type_,
        name=(data.get("name") or "").strip(),
        parent_id=str(data.get("parentId") or data.get("parent_id") or "").strip(),
        first_id=str(data.get("firstId") or data.get("first_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    row = master_repo.get_sample_attr(row_id)
    if not row:
        return fail("记录不存在")
    return ok(row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or data.get("sttribute_name") or "").strip()
    if not name:
        return fail("属性名称不能为空")
    type_ = to_int(data.get("type"), 1) or 1
    parent_id = to_int(data.get("parentId") or data.get("parent_id"))
    if type_ > 1 and not parent_id:
        return fail("请选择上级属性")
    row_id = to_int(data.get("id"))
    new_id = master_repo.save_sample_attr(
        {
            "name": name,
            "type": type_,
            "parent_id": parent_id,
            "special_id": to_int(data.get("specialId") or data.get("special_id")),
            "selection": to_int(data.get("selection"), 1) or 1,
        },
        row_id=row_id,
    )
    return ok({"id": new_id}, res_msg="保存成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    status = to_int(data.get("status"), 1)
    if not row_id or status is None:
        return fail("参数错误")
    master_repo.set_sample_attr_status(row_id, status)
    return ok(res_msg="操作成功")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = to_int(data.get("id"))
    if not row_id:
        return fail("参数错误")
    master_repo.soft_delete_sample_attr(row_id)
    return ok(res_msg="删除成功")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_attr_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_ = to_int(data.get("type"), 1) or 1
    parent_id = str(data.get("parentId") or data.get("parent_id") or "").strip()
    return ok(master_repo.list_sample_attr_options(type_, parent_id))


# ---------- orders ----------
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    order_type = str(data.get("orderType") or data.get("order_type") or "6")
    if order_type == "10":
        rows, total = order_repo.list_sub_orders(
            order_id=(data.get("orderId") or data.get("order_id") or "").strip(),
            parent_order_id=(
                data.get("parentOrderId")
                or data.get("parent_order_id")
                or data.get("sourceOrder")
                or ""
            ).strip(),
            customer_name=(
                data.get("customerName")
                or data.get("customer_name")
                or data.get("stockCompanyName")
                or data.get("companyName")
                or ""
            ).strip(),
            sale_manager=(
                data.get("saleManager") or data.get("sale_Manager") or data.get("sale_manager") or ""
            ).strip(),
            sale_user=(data.get("saleUser") or data.get("sale_user") or "").strip(),
            order_status=str(data.get("orderStatus") or data.get("order_status") or "").strip(),
            test_user_id=str(data.get("testUserId") or data.get("test_user_id") or "").strip(),
            is_confirm=str(
                data.get("isConfirm")
                if data.get("isConfirm") is not None
                else data.get("is_confirm") or ""
            ).strip(),
            finish_start=(
                data.get("finishStart") or data.get("order_startime") or data.get("orderStart") or ""
            ).strip(),
            finish_end=(
                data.get("finishEnd") or data.get("order_endtime") or data.get("orderEnd") or ""
            ).strip(),
            page=page,
            page_size=page_size,
        )
    else:
        rows, total = order_repo.list_orders(
            order_type=order_type,
            order_id=(data.get("orderId") or data.get("order_id") or "").strip(),
            company_name=(
                data.get("companyName")
                or data.get("company_name")
                or data.get("customer_name")
                or ""
            ).strip(),
            supplier_name=str(
                data.get("supplierName") or data.get("supplier_name") or ""
            ).strip(),
            sale_manager=(
                data.get("saleManager") or data.get("sale_Manager") or data.get("sale_manager") or ""
            ).strip(),
            sale_user=(data.get("saleUser") or data.get("sale_user") or "").strip(),
            order_status=str(data.get("orderStatus") or data.get("order_status") or "").strip(),
            goods_name=(data.get("goodsName") or data.get("goods_name") or "").strip(),
            order_start=(
                data.get("orderStart") or data.get("order_startime") or data.get("orderStartime") or ""
            ).strip(),
            order_end=(
                data.get("orderEnd") or data.get("order_endtime") or data.get("orderEndtime") or ""
            ).strip(),
            page=page,
            page_size=page_size,
        )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def grab_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = order_repo.list_grab_orders(
        order_id=(data.get("orderId") or data.get("order_id") or "").strip(),
        source_order=(data.get("sourceOrder") or data.get("source_order") or data.get("parent_order_id") or "").strip(),
        company_name=(data.get("companyName") or data.get("company_name") or data.get("stockCompanyName") or "").strip(),
        sale_manager=(data.get("saleManager") or data.get("sale_Manager") or data.get("sale_manager") or "").strip(),
        sale_user=(data.get("saleUser") or data.get("sale_user") or "").strip(),
        order_status=str(data.get("orderStatus") or data.get("order_status") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def grab_order(request: Request, user=None):
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("orderId") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    uid = str((user or {}).get("id") or (user or {}).get("user_id") or "")
    if not uid:
        return fail("用户未登录")
    ok_flag, msg = order_repo.grab_order(order_id=order_id, user_id=uid)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    row = order_repo.get_order(order_id)
    if not row:
        return fail("订单不存在")
    children = order_repo.list_order_children(order_id)
    return ok({**row, "children": children})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_audit(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    pass_raw = data.get("pass")
    if pass_raw is None:
        pass_raw = data.get("auditPass")
    if isinstance(pass_raw, str):
        pass_ = pass_raw.lower() in ("1", "true", "yes", "y")
    else:
        pass_ = bool(pass_raw) if pass_raw is not None else True
    remark = (data.get("remark") or data.get("mark") or "").strip()
    ok_flag, msg = order_repo.audit_order(order_id=order_id, pass_=pass_, remark=remark)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_export(request: Request, user=None):
    """返回可导出的订单行（前端拼 CSV），避免 axios 对 blob 的拦截干扰。"""
    del user
    data = merge_payload(request)
    order_type = str(data.get("orderType") or data.get("order_type") or "6")
    rows = order_repo.list_export_orders(
        order_type=order_type,
        limit=5000,
        order_id=(data.get("orderId") or data.get("order_id") or "").strip(),
        parent_order_id=(
            data.get("parentOrderId")
            or data.get("parent_order_id")
            or data.get("sourceOrder")
            or ""
        ).strip(),
        customer_name=(
            data.get("customerName")
            or data.get("customer_name")
            or data.get("stockCompanyName")
            or data.get("companyName")
            or ""
        ).strip(),
        sale_manager=(
            data.get("saleManager") or data.get("sale_Manager") or data.get("sale_manager") or ""
        ).strip(),
        sale_user=(data.get("saleUser") or data.get("sale_user") or "").strip(),
        order_status=str(data.get("orderStatus") or data.get("order_status") or "").strip(),
        test_user_id=str(data.get("testUserId") or data.get("test_user_id") or "").strip(),
        is_confirm=str(
            data.get("isConfirm") if data.get("isConfirm") is not None else data.get("is_confirm") or ""
        ).strip(),
        finish_start=(
            data.get("finishStart") or data.get("order_startime") or data.get("orderStart") or ""
        ).strip(),
        finish_end=(
            data.get("finishEnd") or data.get("order_endtime") or data.get("orderEnd") or ""
        ).strip(),
    )
    return ok(rows, res_msg="ok")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_status_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    kind = str(data.get("kind") or data.get("orderType") or data.get("order_type") or "").strip()
    if kind in ("10", "sub"):
        return Response(ajax_ok(obj=order_repo.SUB_ORDER_STATUS_FILTER_OPTIONS))
    return Response(ajax_ok(obj=order_repo.ORDER_STATUS_FILTER_OPTIONS))
