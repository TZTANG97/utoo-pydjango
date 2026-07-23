from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_inventory.repositories import device_booking as booking_repo
from apps.admin_inventory.repositories import income as income_repo
from apps.admin_inventory.repositories import inventory as inv_repo
from apps.admin_inventory.repositories import lab as lab_repo
from apps.admin_inventory.repositories import sample_order as sample_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---- 库存管理 ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_list(request: Request, user=None):
    """默认走 Java 聚合列表；mode=flat 时返回扁平列表。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    mode = str(data.get("mode") or "statis").strip().lower()
    if mode == "flat":
        rows, total = inv_repo.list_inventory(
            goods_name=(data.get("goodsName") or data.get("goods_name") or "").strip(),
            store_name=(data.get("storeName") or data.get("store_name") or "").strip(),
            inventory_id=(data.get("inventoryId") or data.get("inventory_id") or "").strip(),
            serial_number=(data.get("serialNumber") or data.get("serial_number") or "").strip(),
            gi_status=str(data.get("giStatus") or data.get("gi_status") or ""),
            page=page,
            page_size=page_size,
        )
    else:
        rows, total = inv_repo.list_inventory_statis(
            goods_name=(data.get("goodsName") or data.get("goods_name") or "").strip(),
            goods_spec=(data.get("goodsSpec") or data.get("goods_spec") or "").strip(),
            serial_number=(data.get("serialNumber") or data.get("serial_number") or "").strip(),
            expmanage_line_id=str(
                data.get("expmanageLineId") or data.get("expmanage_line_id") or ""
            ).strip(),
            private_lease_type=(
                data.get("privateLeaseType") or data.get("private_lease_type") or ""
            ).strip(),
            list_type=str(data.get("type") or data.get("listType") or "").strip(),
            page=page,
            page_size=page_size,
        )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_children(request: Request, user=None):
    del user
    data = merge_payload(request)
    goods_id = str(data.get("goodsId") or data.get("goods_id") or "").strip()
    if not goods_id:
        return Response(ajax_fail("缺少商品ID"))
    rows = inv_repo.list_inventory_children(
        goods_id=goods_id,
        goods_brand_id=str(data.get("goodsBrandId") or data.get("goods_brand_id") or "").strip(),
        goods_spec=str(data.get("goodsSpec") or data.get("goods_spec") or ""),
        serial_number=(data.get("serialNumber") or data.get("serial_number") or "").strip(),
        private_lease_type=(
            data.get("privateLeaseType") or data.get("private_lease_type") or ""
        ).strip(),
        expmanage_line_id=str(
            data.get("expmanageLineId") or data.get("expmanage_line_id") or ""
        ).strip(),
    )
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_summary(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=inv_repo.inventory_summary()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    row = inv_repo.get_inventory(row_id)
    if not row:
        return Response(ajax_fail("库存不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def inventory_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    produce_time = data.get("produceTime") or data.get("produce_time") or None
    if produce_time == "":
        produce_time = None
    inv_repo.update_inventory(
        row_id,
        {
            "store_id": _to_int(data.get("storeId") or data.get("store_id")),
            "serial_number": (data.get("serialNumber") or data.get("serial_number") or "").strip(),
            "inventory_num": _to_int(data.get("inventoryNum") or data.get("inventory_num"), 0) or 0,
            "gi_status": _to_int(data.get("giStatus") or data.get("gi_status"), 1) or 1,
            "goods_price": data.get("goodsPrice") or data.get("goods_price") or 0,
            "mark": (data.get("mark") or "").strip(),
            "zlckj": data.get("zlckj") if data.get("zlckj") not in (None, "") else None,
            "nbzlj": data.get("nbzlj") if data.get("nbzlj") not in (None, "") else None,
            "produce_time": produce_time,
        },
    )
    return Response(ajax_ok(msg="更新成功"))


# ---- 实验室 ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = lab_repo.list_labs(
        lab_name=(data.get("labName") or data.get("lab_name") or "").strip(),
        lab_num=(data.get("labNum") or data.get("lab_num") or "").strip(),
        lab_userid=str(data.get("labUserid") or data.get("lab_userid") or "").strip(),
        country=str(data.get("country") or "").strip(),
        province=str(data.get("province") or "").strip(),
        city=str(data.get("city") or "").strip(),
        area_id=str(data.get("areaId") or data.get("area_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=lab_repo.list_lab_filter_options()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    row = lab_repo.get_lab(row_id)
    if not row:
        return Response(ajax_fail("实验室不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = {
        "lab_num": (data.get("labNum") or data.get("lab_num") or "").strip(),
        "lab_name": (data.get("labName") or data.get("lab_name") or "").strip(),
        "lab_userid": str(data.get("labUserid") or data.get("lab_userid") or "").strip() or None,
        "country": (data.get("country") or "").strip(),
        "area_id": str(data.get("areaId") or data.get("area_id") or "").strip() or None,
        "address": (data.get("address") or "").strip(),
        "status": _to_int(data.get("status"), 1) or 1,
        "syuser_id": str(data.get("syuserId") or data.get("syuser_id") or "").strip() or None,
    }
    if not payload["lab_name"]:
        return Response(ajax_fail("实验室名称不能为空"))
    row_id = _to_int(data.get("id"))
    if row_id:
        lab_repo.update_lab(row_id, payload)
        return Response(ajax_ok(msg="更新成功"))
    new_id = lab_repo.insert_lab(payload)
    return Response(ajax_ok(msg="保存成功", obj={"id": new_id}))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    # Java: shstatus 1启用 2禁用
    status = _to_int(data.get("status") if data.get("status") is not None else data.get("shstatus"))
    if not row_id or status is None:
        return Response(ajax_fail("参数错误"))
    lab_repo.set_lab_status(row_id, status)
    return Response(ajax_ok(msg="状态已更新"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_del(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    lab_repo.soft_delete_lab(row_id)
    return Response(ajax_ok(msg="删除成功"))


# ---- 样品管理单 ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_order_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = sample_repo.list_sample_orders(
        out_num=(data.get("outNum") or data.get("out_num") or "").strip(),
        order_id=(data.get("orderId") or data.get("order_id") or "").strip(),
        sj_out_time=str(data.get("sjOutTime") or data.get("sj_out_time") or "").strip(),
        store_id=str(data.get("storeId") or data.get("store_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_order_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj={"stores": sample_repo.list_sample_store_options()}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_store_positions(request: Request, user=None):
    """对齐 Java samplestoreHouse/queryListByStoreId.ajax。"""
    del user
    data = merge_payload(request)
    store_id = data.get("store_id") or data.get("storeId") or ""
    type_raw = data.get("type")
    # type=0 空闲；type=1 占用；缺省空闲
    free_only = True
    if type_raw is not None and str(type_raw) != "":
        free_only = str(type_raw) == "0"
    return Response(
        ajax_ok(obj=sample_repo.list_sample_store_positions(store_id=store_id, free_only=free_only))
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_order_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    row_id = _to_int(data.get("id"))
    if not row_id:
        return Response(ajax_fail("参数错误"))
    row = sample_repo.get_sample_order(row_id)
    if not row:
        return Response(ajax_fail("单据不存在"))
    items = sample_repo.list_sample_order_items(row_id)
    return Response(ajax_ok(obj={**row, "items": items}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sample_order_export(request: Request, user=None):
    """导出样品出入库数据（前端再生成 CSV，对齐 Java export.htm）。"""
    del user
    data = merge_payload(request)
    rows = sample_repo.list_sample_export_rows(
        store_id=str(data.get("storeId") or data.get("store_id") or "").strip(),
        start_time=str(data.get("startime") or data.get("startTime") or "").strip(),
        end_time=str(data.get("endtime") or data.get("endTime") or "").strip(),
    )
    if not rows:
        return Response(ajax_fail("数据为空"))
    return Response(ajax_ok(obj={"rows": rows, "total": len(rows)}))


# ---- 设备预约 ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_booking_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = booking_repo.list_device_bookings(
        lab_num=(data.get("labNum") or data.get("lab_num") or "").strip(),
        lab_name=(data.get("labName") or data.get("lab_name") or "").strip(),
        line_num=(data.get("lineNum") or data.get("line_num") or "").strip(),
        class_id=str(data.get("classId") or data.get("class_id") or ""),
        status=str(data.get("status") or ""),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_booking_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    line_id = _to_int(data.get("id") or data.get("lineId") or data.get("line_id"))
    if not line_id:
        return Response(ajax_fail("参数错误"))
    row = booking_repo.get_device_booking(line_id)
    if not row:
        return Response(ajax_fail("产线不存在"))
    draw, page, page_size = parse_datatable_params(request)
    logs, total = booking_repo.list_booking_logs(line_id, page=page, page_size=page_size)
    return Response(ajax_ok(obj={"line": row, "logs": logs, "logTotal": total, "draw": draw}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_booking_options(request: Request, user=None):
    del user, request
    return Response(
        ajax_ok(
            obj={
                "labs": booking_repo.list_lab_options(),
                "classes": booking_repo.list_class_options(),
                "lines": booking_repo.list_line_options(),
            }
        )
    )


# ---- 内部收益 ----
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_overview(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=income_repo.overview_kpis()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = income_repo.list_income(
        income_type=str(data.get("type") or ""),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_ratio(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=income_repo.list_ratio_matrix()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_invest_users(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_type = _to_int(data.get("accountType") or data.get("account_type"), 1) or 1
    return Response(ajax_ok(obj=income_repo.list_invest_users(account_type=account_type)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_user_options(request: Request, user=None):
    del user
    data = merge_payload(request)
    keyword = (data.get("keyword") or data.get("userName") or "").strip()
    return Response(ajax_ok(obj=income_repo.list_all_users(keyword)))


def _income_actor_id(user) -> str:
    if not user:
        return ""
    return str(getattr(user, "id", "") or "")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_submit_invest(request: Request, user=None):
    data = merge_payload(request)
    try:
        amount = float(data.get("logAmount") or data.get("log_amount") or 0)
    except (TypeError, ValueError):
        return Response(ajax_fail("金额错误"))
    log_id, err = income_repo.create_invest(
        user_id=str(data.get("userId") or data.get("tj_userid") or data.get("tjUserId") or "").strip(),
        account_type=_to_int(data.get("accountType") or data.get("account_type"), 1) or 1,
        log_amount=amount,
        deal_time=str(data.get("dealTime") or data.get("deal_time") or "").strip(),
        mark=(data.get("pdLogInfo") or data.get("mark") or data.get("pd_log_info") or "").strip(),
        add_user=_income_actor_id(user),
        project_type=_to_int(data.get("projectType") or data.get("project_type"), 1) or 1,
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_submit_disinvest(request: Request, user=None):
    data = merge_payload(request)
    try:
        amount = float(data.get("logAmount") or data.get("log_amount") or 0)
        th_amount = float(data.get("thAmount") or data.get("th_amount") or 0)
    except (TypeError, ValueError):
        return Response(ajax_fail("金额错误"))
    log_id, err = income_repo.create_disinvest(
        user_id=str(data.get("userId") or data.get("tj_userid") or data.get("tjUserId") or "").strip(),
        account_type=_to_int(data.get("accountType") or data.get("account_type"), 1) or 1,
        log_amount=amount,
        th_amount=th_amount,
        deal_time=str(data.get("dealTime") or data.get("deal_time") or "").strip(),
        mark=(data.get("pdLogInfo") or data.get("mark") or data.get("pd_log_info") or "").strip(),
        add_user=_income_actor_id(user),
        project_type=_to_int(data.get("projectType") or data.get("project_type"), 1) or 1,
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def income_submit_tax(request: Request, user=None):
    data = merge_payload(request)
    try:
        amount = float(data.get("logAmount") or data.get("log_amount") or 0)
    except (TypeError, ValueError):
        return Response(ajax_fail("金额错误"))
    log_id, err = income_repo.create_other_pay(
        account_type=_to_int(data.get("accountType") or data.get("account_type"), 1) or 1,
        log_amount=amount,
        pay_type=_to_int(data.get("payType") or data.get("pay_type"), 5) or 5,
        deal_time=str(data.get("dealTime") or data.get("deal_time") or "").strip(),
        mark=(data.get("pdLogInfo") or data.get("mark") or data.get("pd_log_info") or "").strip(),
        add_user=_income_actor_id(user),
        accessory_id=str(data.get("accessoryId") or data.get("accessory_id") or "").strip() or None,
    )
    if err:
        return Response(ajax_fail(err))
    return Response(ajax_ok(obj={"id": log_id}, res_msg="提交成功"))
