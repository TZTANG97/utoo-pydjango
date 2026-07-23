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
from apps.admin_experiment.repositories import sample_flow as sample_flow_repo
from qd_common.responses import ajax_ok


def _order_id_from(data: dict) -> int | None:
    return to_int(data.get("id") or data.get("ofId") or data.get("orderId"))


def _child_ids_from(data: dict):
    return data.get("childIds") or data.get("childids") or data.get("ids") or data.get("childId")


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
    payload: dict = {
        "name": name,
        "type": type_,
        "parent_id": parent_id,
        "special_id": to_int(data.get("specialId") or data.get("special_id")),
    }
    # 选择方式仅二级属性使用；三级不传则不覆盖原值
    if "selection" in data and data.get("selection") not in (None, ""):
        payload["selection"] = to_int(data.get("selection"), 1) or 1
    elif type_ == 2:
        payload["selection"] = to_int(data.get("selection"), 1) or 1
    new_id = master_repo.save_sample_attr(payload, row_id=row_id)
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
    if order_type in ("9", "10"):
        rows, total = order_repo.list_sub_orders(
            order_type=order_type,
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
            pay_status=str(
                data.get("payStatus") if data.get("payStatus") is not None else data.get("pay_status") or ""
            ).strip(),
            test_user_id=str(data.get("testUserId") or data.get("test_user_id") or "").strip(),
            is_confirm=str(data.get("isConfirm") if data.get("isConfirm") is not None else data.get("is_confirm") or "").strip(),
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
    detail = order_repo.get_order_detail_bundle(order_id)
    if not detail:
        return fail("订单不存在")
    return ok(detail)


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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_cancel(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.cancel_order(
        order_id=order_id,
        remark=(data.get("remark") or data.get("mark") or "").strip(),
    )
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_submit_audit(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.submit_audit(order_id=order_id)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_withdraw_audit(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.withdraw_audit(order_id=order_id)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_cost_settle(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.cost_settle_sure(order_id=order_id)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_save_receive_bill(request: Request, user=None):
    """对齐 Java 订单详情录入收款 → saveBillAndAccessory(type=2) + 分钱。"""
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId") or data.get("orderId"))
    if not order_id:
        return fail("参数错误")
    money = data.get("money") or data.get("amount")
    staff_id = ""
    if isinstance(user, dict):
        staff_id = str(user.get("id") or user.get("userId") or "")
    from apps.admin_experiment.services.split_money import save_receive_bill

    ok_flag, msg = save_receive_bill(
        order_id=order_id,
        money=money,
        staff_user_id=staff_id,
        log_info=str(data.get("logInfo") or data.get("remark") or "录入收款"),
        bill_date=str(data.get("billDate") or data.get("bill_date") or ""),
    )
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_share_ratio(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.update_share_ratio(
        order_id=order_id,
        user_scale_info=str(
            data.get("user_scale_info")
            or data.get("userScaleInfo")
            or data.get("scaleInfo")
            or data.get("info")
            or ""
        ),
        salecb_user_scale_info=str(
            data.get("salecb_user_scale_info")
            or data.get("salecbUserScaleInfo")
            or data.get("salecbScaleInfo")
            or ""
        ),
    )
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_add_related(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    ok_flag, msg = order_repo.add_related_order(
        order_id=order_id,
        related_order_no=str(
            data.get("rOrderId")
            or data.get("relatedOrderId")
            or data.get("relatedOrderNo")
            or data.get("orderId")
            or ""
        ),
        r_select=str(data.get("rSelect") or data.get("relatedType") or data.get("type") or ""),
    )
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_del_related(request: Request, user=None):
    del user
    data = merge_payload(request)
    of_id = str(data.get("ofId") or data.get("of_id") or data.get("orderId") or "").strip()
    related_no = str(
        data.get("order_id") or data.get("relatedOrderNo") or data.get("relatedOrderId") or ""
    ).strip()
    if not of_id or not related_no:
        return fail("参数错误")
    ok_flag, msg = order_repo.del_related_order(of_order_no=of_id, related_order_no=related_no)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_save_finish(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    items = data.get("items") or data.get("children") or []
    if not isinstance(items, list):
        return fail("明细格式错误")
    ok_flag, msg = order_repo.save_finish_times(order_id=order_id, items=items)
    if not ok_flag:
        return fail(msg)
    return ok(res_msg=msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_more_info(request: Request, user=None):
    del user
    data = merge_payload(request)
    order_id = to_int(data.get("id") or data.get("ofId"))
    if not order_id:
        return fail("参数错误")
    info = order_repo.build_more_info(order_id)
    if not info:
        return fail("订单不存在")
    return ok(info)


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
        supplier_name=str(data.get("supplierName") or data.get("supplier_name") or "").strip(),
        goods_name=(data.get("goodsName") or data.get("goods_name") or "").strip(),
        sale_manager=(
            data.get("saleManager") or data.get("sale_Manager") or data.get("sale_manager") or ""
        ).strip(),
        sale_user=(data.get("saleUser") or data.get("sale_user") or "").strip(),
        order_status=str(data.get("orderStatus") or data.get("order_status") or "").strip(),
        pay_status=str(
            data.get("payStatus") if data.get("payStatus") is not None else data.get("pay_status") or ""
        ).strip(),
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
        order_start=(
            data.get("orderStart") or data.get("order_startime") or data.get("orderStartime") or ""
        ).strip(),
        order_end=(
            data.get("orderEnd") or data.get("order_endtime") or data.get("orderEndtime") or ""
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
    if kind in ("9", "10", "sub", "sub9"):
        return Response(ajax_ok(obj=order_repo.SUB_ORDER_STATUS_FILTER_OPTIONS))
    if kind in ("pay", "payStatus"):
        return Response(ajax_ok(obj=order_repo.PAY_STATUS_FILTER_OPTIONS))
    return Response(ajax_ok(obj=order_repo.ORDER_STATUS_FILTER_OPTIONS))


# ---------- type=10 样品 / 测试流转 ----------
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sample_arrive(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.sample_arrive(
        order_id=oid,
        child_ids=_child_ids_from(data),
        store_id=str(data.get("storeId") or data.get("store_id") or ""),
        store_position_id=str(
            data.get("storePosId")
            or data.get("storePositionId")
            or data.get("store_position_id")
            or ""
        ),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sample_pick(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.sample_pick(order_id=oid, child_ids=_child_ids_from(data))
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_test_start(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.test_start(
        order_id=oid,
        child_ids=_child_ids_from(data),
        line_id=str(data.get("lineId") or data.get("line_id") or ""),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_test_end(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.test_end(order_id=oid, child_ids=_child_ids_from(data))
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sample_return(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.sample_return(order_id=oid, child_ids=_child_ids_from(data))
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sample_ship(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.sample_ship_back(
        order_id=oid,
        child_ids=_child_ids_from(data),
        express_no=str(data.get("expressNo") or data.get("express_no") or ""),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sample_retain(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    scrap_raw = data.get("scrap")
    if scrap_raw is True or scrap_raw is False:
        scrap = bool(scrap_raw)
    else:
        scrap = str(scrap_raw or data.get("type") or "").strip().lower() in (
            "1",
            "4",
            "true",
            "scrap",
        )
    ok_flag, msg = sample_flow_repo.sample_retain(
        order_id=oid, child_ids=_child_ids_from(data), scrap=scrap
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_add_video(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.add_video_meeting(
        order_id=oid,
        child_ids=_child_ids_from(data),
        meeting_num=str(data.get("meetingNum") or data.get("meeting_num") or ""),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_confirm_done(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.confirm_children(
        order_id=oid,
        child_ids=_child_ids_from(data),
        mark=str(data.get("mark") or data.get("remark") or ""),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_retest(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = sample_flow_repo.retest_apply(order_id=oid, child_ids=_child_ids_from(data))
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_save_invoice_bill(request: Request, user=None):
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    staff = ""
    if isinstance(user, dict):
        staff = str(user.get("id") or user.get("userId") or "")
    ok_flag, msg = order_repo.save_invoice_bill(
        order_id=oid,
        money=data.get("money") or data.get("amount"),
        staff_user_id=staff,
        log_info=str(data.get("logInfo") or data.get("remark") or "录入开票"),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_confirm_customer(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = order_repo.confirm_customer_order(order_id=oid)
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_confirm_pay(request: Request, user=None):
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    staff = ""
    if isinstance(user, dict):
        staff = str(user.get("id") or user.get("userId") or "")
    ok_flag, msg = order_repo.confirm_online_pay(order_id=oid, staff_user_id=staff)
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_generate_appointment(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = order_repo.generate_appointment(
        order_id=oid,
        test_address_id=str(data.get("testAddressId") or data.get("test_address_id") or ""),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_update_basic(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = order_repo.update_order_basic(
        order_id=oid,
        mark=str(data.get("mark") if data.get("mark") is not None else ""),
        ship_user=str(data.get("shipUser") or data.get("ship_user") or ""),
        ship_phone=str(data.get("shipPhone") or data.get("ship_phone") or ""),
        ship_address=str(data.get("shipAddress") or data.get("ship_address") or ""),
        total_price=data.get("totalPrice") if "totalPrice" in data or "total_price" in data else None,
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_create_sub(request: Request, user=None):
    del user
    data = merge_payload(request)
    pid = to_int(data.get("saleOrderId") or data.get("parentId") or data.get("id"))
    if not pid:
        return fail("参数错误")
    ok_flag, msg, new_id = order_repo.create_sub_order_from_parent(
        parent_id=pid,
        child_line_ids=data.get("childIds") or data.get("childids") or data.get("ids"),
        form=data,
    )
    if not ok_flag:
        return fail(msg)
    return ok({"id": new_id}, res_msg=msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_confirm_ordered(request: Request, user=None):
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    ok_flag, msg = order_repo.confirm_ordered(order_id=oid)
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_sub_pay(request: Request, user=None):
    """type=9 付款申请：type 1申请/重提 2通过 3驳回。"""
    del user
    data = merge_payload(request)
    oid = _order_id_from(data) or to_int(data.get("ofId"))
    if not oid:
        return fail("参数错误")
    ok_flag, msg = order_repo.update_sub_pay(
        order_id=oid,
        pay_type=data.get("type") or data.get("payType") or "",
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_upload_sub_pay(request: Request, user=None):
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    staff = ""
    if isinstance(user, dict):
        staff = str(user.get("id") or user.get("userId") or "")
    ok_flag, msg = order_repo.upload_sub_pay_bill(
        order_id=oid,
        money=data.get("money") or data.get("amount"),
        staff_user_id=staff,
        log_info=str(data.get("logInfo") or data.get("remark") or "上传付款信息"),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_upload_sub_invoice(request: Request, user=None):
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    staff = ""
    if isinstance(user, dict):
        staff = str(user.get("id") or user.get("userId") or "")
    ok_flag, msg = order_repo.upload_sub_invoice_bill(
        order_id=oid,
        money=data.get("money") or data.get("amount"),
        staff_user_id=staff,
        log_info=str(data.get("logInfo") or data.get("remark") or "上传发票信息"),
    )
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_upload_file(request: Request, user=None):
    """对齐 Java experimentOrder/uploadChildData.ajax（订单资料 type=3）。"""
    del user
    from apps.orders.services import accessory_upload as accessory_upload_svc

    uploaded = request.FILES.get("orderdata") or request.FILES.get("file")
    if not uploaded:
        return fail("文件为空")
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    type_raw = str(data.get("type") or request.POST.get("type") or "3")
    acc_type = int(type_raw) if type_raw.isdigit() else 3
    ok_flag, msg, obj = accessory_upload_svc.save_order_attachment(
        data=uploaded.read(),
        orig_name=uploaded.name or "upload",
        content_type=uploaded.content_type or "application/octet-stream",
        acc_type=acc_type,
        exp_of_id=oid,
    )
    return ok(obj, res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_delete_file(request: Request, user=None):
    """对齐 Java experimentSubOrder/deleteFile.ajax。"""
    del user
    data = merge_payload(request)
    aid = to_int(data.get("id") or data.get("accessoryId"))
    if not aid:
        return fail("参数错误")
    ok_flag, msg = order_repo.delete_order_file(accessory_id=aid)
    return ok(res_msg=msg) if ok_flag else fail(msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def order_update_msg(request: Request, user=None):
    """对齐 Java msgBlur：保存订单备注。"""
    del user
    data = merge_payload(request)
    oid = _order_id_from(data)
    if not oid:
        return fail("参数错误")
    msg_text = str(data.get("msg") or data.get("mark") or "")
    ok_flag, msg = order_repo.update_order_msg(order_id=oid, msg=msg_text)
    return ok(res_msg=msg) if ok_flag else fail(msg)
