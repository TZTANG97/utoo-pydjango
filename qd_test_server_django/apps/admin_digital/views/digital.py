from __future__ import annotations

from datetime import datetime

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_digital.repositories import performance as perf_repo
from apps.admin_digital.repositories import stats as stats_repo
from apps.admin_digital.repositories import users as user_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok

TEST_TYPES = ["测试人员", "测试主管"]


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
def dept_options(request: Request, user=None):
    del user, request
    return Response(ajax_ok(obj=user_repo.list_depts_flat()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def test_user_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    # 对齐 Java StatisticTestuserPerformanceController#queryUsers + getuserinfoMapSTP：
    # 管理员 utoo_types 为空（不过滤类型）；pt_type like '%2%'；含协助者字段
    sex_raw = data.get("userSex")
    if sex_raw in (None, ""):
        sex_raw = data.get("user_sex")
    rows, total = user_repo.list_staff_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        user_sex=sex_raw,
        utoo_types=None,
        require_pt_type_staff=True,
        include_helpers=True,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sale_user_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    # 对齐 Java getuserinfoMapSTP：user_status=1 且 pt_type like '%2%'，不过滤 utoo_type
    rows, total = user_repo.list_staff_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        utoo_types=None,
        require_pt_type_staff=True,
        include_helpers=True,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def test_target_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("test_user_id") or data.get("testUserId") or "")
    year = str(data.get("year") or "")
    if not uid or not year:
        return Response(ajax_fail("参数错误"))
    row = perf_repo.get_test_target(test_user_id=uid, year=year) or {}
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def test_target_show(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("test_user_id") or data.get("testUserId") or "")
    if not uid:
        return Response(ajax_fail("参数错误"))
    staff = user_repo.get_staff(uid)
    rows = perf_repo.list_test_targets(test_user_id=uid)
    return Response(
        ajax_ok(
            obj={
                "userName": (staff or {}).get("userName"),
                "trueName": (staff or {}).get("trueName"),
                "list": rows,
            }
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def test_target_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("test_user_id") or data.get("testUserId") or "")
    year = str(data.get("year") or "")
    amount = data.get("amount")
    if not uid or not year:
        return Response(ajax_fail("请填写人员和年份"))
    target_id = _to_int(data.get("id"))
    new_id = perf_repo.save_test_target(
        target_id=target_id,
        test_user_id=uid,
        year=year,
        amount=amount or 0,
    )
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sale_target_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("sale_user_id") or data.get("saleUserId") or "")
    month = str(data.get("month") or "")
    if not uid or not month:
        return Response(ajax_fail("参数错误"))
    row = perf_repo.get_sale_target(sale_user_id=uid, month=month) or {}
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sale_target_show(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(
        data.get("sale_user_id")
        or data.get("saleUserId")
        or data.get("test_user_id")
        or data.get("testUserId")
        or ""
    )
    if not uid:
        return Response(ajax_fail("参数错误"))
    staff = user_repo.get_staff(uid)
    rows = perf_repo.list_sale_targets(sale_user_id=uid)
    return Response(
        ajax_ok(
            obj={
                "userName": (staff or {}).get("userName"),
                "trueName": (staff or {}).get("trueName"),
                "list": rows,
            }
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sale_target_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    uid = str(data.get("sale_user_id") or data.get("saleUserId") or "")
    month = str(data.get("month") or "")
    amount = data.get("amount")
    if not uid or not month:
        return Response(ajax_fail("请填写人员和月份"))
    target_id = _to_int(data.get("id"))
    new_id = perf_repo.save_sale_target(
        target_id=target_id,
        sale_user_id=uid,
        month=month,
        amount=amount or 0,
    )
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_test_perf(request: Request, user=None):
    del user
    data = merge_payload(request)
    year = str(data.get("year") or datetime.now().year)
    users = user_repo.list_staff_users_all(utoo_types=TEST_TYPES)
    rows = perf_repo.build_lab_test_rows(users=users, year=year)
    return Response(ajax_ok(obj={"year": year, "resultList": rows}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_sale_users(request: Request, user=None):
    """对齐 Java LabPerformanceSaleuserController#selUsersByDeptId。"""
    del request
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    staff = user_repo.get_staff(uid) if uid else None
    if not staff:
        return Response(ajax_ok(obj=[]))
    utoo = str(staff.get("utooType") or "").strip()
    if utoo == "销售主管":
        dept_ids = user_repo.child_dept_ids(str(staff.get("deptId") or ""))
        rows = (
            user_repo.list_staff_users_all(dept_ids=dept_ids, require_pt_type_staff=True)
            if dept_ids
            else [staff]
        )
    elif utoo in ("系统管理员", "超级管理员") or "管理员" in utoo:
        rows = user_repo.list_staff_users_all(require_pt_type_staff=True)
    else:
        rows = [staff]
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_sale_perf(request: Request, user=None):
    del user
    data = merge_payload(request)
    year = str(data.get("year") or datetime.now().year)
    user_id = str(data.get("user_id") or data.get("userId") or "")
    if not user_id:
        return Response(ajax_fail("请选择销售人员"))
    staff = user_repo.get_staff(user_id) or {}
    payload = perf_repo.build_lab_sale_rows(user_id=user_id, year=year)
    payload["user_id"] = user_id
    payload["trueName"] = staff.get("trueName") or staff.get("userName") or ""
    payload["userName"] = staff.get("userName") or ""
    return Response(ajax_ok(obj=payload))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def lab_sale_order_list(request: Request, user=None):
    """对齐 Java labPerformanceSaleuser/expOrderList.ajax。

    固定走网关本地（不转发 Asset）：UAT Asset 常未同步该路由会 404。
    """
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    month = str(data.get("month") or "").strip()
    sale_user_id = str(data.get("sale_user_id") or data.get("saleUserId") or "").strip()
    type_ = _to_int(data.get("type"), 1) or 1
    if not month or not sale_user_id:
        return Response(datatable_payload(draw=draw, total=0, rows=[]))
    rows, total = perf_repo.list_lab_sale_perf_orders(
        sale_user_id=sale_user_id,
        month=month,
        type_=type_,
        customer_name=(data.get("customer_name") or data.get("customerName") or "").strip(),
        order_id=(data.get("order_id") or data.get("orderId") or "").strip(),
        goods_name=(data.get("goods_name") or data.get("goodsName") or "").strip(),
        supplier_name=str(data.get("supplier_name") or data.get("company_id") or "").strip(),
        sale_manager=str(data.get("sale_Manager") or data.get("sale_manager") or "").strip(),
        order_status=str(data.get("order_status") or data.get("orderStatus") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_overview(request: Request, user=None):
    """兼容旧接口；新看板请用 selDateOverviewByYear / board1。"""
    del user
    data = merge_payload(request)
    year = str(data.get("year") or datetime.now().year)
    dept_id = str(data.get("deptId") or data.get("dept_id") or data.get("test_lab") or "")
    overview = stats_repo.overview(dept_id=dept_id, year=year)
    trend = stats_repo.monthly_finish_trend(dept_id=dept_id, year=year)
    workload = stats_repo.tester_workload(dept_id=dept_id, year=year)
    recent = stats_repo.recent_finished(dept_id=dept_id, limit=20)
    return Response(
        ajax_ok(
            obj={
                "year": year,
                "overview": overview,
                "trend": trend,
                "workload": workload,
                "recent": recent,
            }
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_date_overview(request: Request, user=None):
    """对齐 Java testUserStats/selDateOverviewByYear.ajax。"""
    del user
    data = merge_payload(request)
    now = datetime.now()
    year = str(data.get("year") or now.year)
    month = str(data.get("month") or now.month).zfill(2)
    period_type = str(data.get("type") or "2")
    test_lab = str(data.get("test_lab") or data.get("deptId") or data.get("dept_id") or "")
    user_id = str(data.get("userId") or data.get("user_id") or "")
    week = str(data.get("week") or "")
    quarter = str(data.get("quarter") or "")
    start_date = str(data.get("startdate") or data.get("startDate") or "")
    end_date = str(data.get("enddate") or data.get("endDate") or "")
    obj = stats_repo.dashboard_overview(
        test_lab=test_lab,
        user_id=user_id,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    return Response(ajax_ok(obj=obj))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_board1(request: Request, user=None):
    """对齐 Java testUserStats/board1.ajax。"""
    del user
    data = merge_payload(request)
    now = datetime.now()
    year = str(data.get("year") or now.year)
    month = str(data.get("month") or now.month).zfill(2)
    dept_id = str(data.get("dept_id") or data.get("deptId") or data.get("test_lab") or "")
    obj = stats_repo.board1_monthly(year=year, month=month, dept_id=dept_id)
    return Response(ajax_ok(obj=obj))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_order_manage(request: Request, user=None):
    """对齐 Java testUserStats/selOrderManage.ajax。"""
    del user
    data = merge_payload(request)
    now = datetime.now()
    year = str(data.get("year") or now.year)
    month = str(data.get("month") or now.month).zfill(2)
    period_type = str(data.get("type") or "2")
    test_lab = str(data.get("test_lab") or data.get("deptId") or data.get("dept_id") or "")
    user_id = str(data.get("userId") or data.get("user_id") or "")
    week = str(data.get("week") or "")
    quarter = str(data.get("quarter") or "")
    start_date = str(data.get("startdate") or data.get("startDate") or "")
    end_date = str(data.get("enddate") or data.get("endDate") or "")
    obj = stats_repo.order_manage(
        test_lab=test_lab,
        user_id=user_id,
        period_type=period_type,
        year=year,
        week=week,
        month=month,
        quarter=quarter,
        start_date=start_date,
        end_date=end_date,
    )
    return Response(ajax_ok(obj=obj))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_board(request: Request, user=None):
    """对齐 Java testUserStats/board.ajax：人员年度月度完成量。"""
    del user
    data = merge_payload(request)
    now = datetime.now()
    year = str(data.get("year") or now.year)
    dept_id = str(data.get("dept_id") or data.get("deptId") or data.get("test_lab") or "")
    rows = stats_repo.annual_tester_monthly(year=year, dept_id=dept_id)
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def stats_users_by_dept(request: Request, user=None):
    """筛选栏：按部门拉测试人员。"""
    del user
    data = merge_payload(request)
    dept_id = str(data.get("deptId") or data.get("dept_id") or "")
    rows = stats_repo.list_users_by_dept(dept_id=dept_id)
    return Response(ajax_ok(obj=rows))
