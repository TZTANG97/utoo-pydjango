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
SALE_TYPES = ["销售人员", "销售主管", "销售"]


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
    rows, total = user_repo.list_staff_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        utoo_types=TEST_TYPES,
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
    # 销售计划页 Java 不限 utoo_type；这里仍优先销售相关，空结果时前端可放宽
    rows, total = user_repo.list_staff_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        utoo_types=None,
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
    del user, request
    rows = user_repo.list_staff_users_all(utoo_types=None)
    # 优先销售相关，否则返回全部启用用户供选择
    sale_rows = [r for r in rows if str(r.get("utooType") or "") in SALE_TYPES or "销售" in str(r.get("utooType") or "")]
    return Response(ajax_ok(obj=sale_rows or rows))


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
def stats_overview(request: Request, user=None):
    del user
    data = merge_payload(request)
    year = str(data.get("year") or datetime.now().year)
    dept_id = str(data.get("deptId") or data.get("dept_id") or "")
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
