from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_auth.repositories import billing as billing_repo
from apps.admin_auth.services import billing as billing_service
from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_response, parse_datatable
from apps.core.responses import ajax_fail, ajax_ok


def _staff_id(user: dict | None) -> str:
    return str((user or {}).get("user_id") or "")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def invoice_list_page(request: Request, user=None):
    params = parse_datatable(request)
    status = str(params.get("status") or "")
    start_time = str(params.get("order_startime") or "")
    end_time = str(params.get("order_endtime") or "")
    total = billing_repo.count_invoice_applies(
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    rows = billing_repo.list_invoice_applies(
        offset=params["offset"],
        limit=params["limit"],
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def invoice_detail(request: Request, user=None):
    apply_id = request.query_params.get("id") or request.data.get("id")
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    row = billing_repo.get_invoice_apply(int(apply_id))
    if not row:
        return Response(ajax_fail("发票申请不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def invoice_reject(request: Request, user=None):
    apply_id = request.data.get("id") or request.query_params.get("id")
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    ok, msg = billing_service.reject_invoice(apply_id=int(apply_id), staff_user_id=_staff_id(user))
    return Response(ajax_ok(res_msg=msg) if ok else ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def pay_log_list(request: Request, user=None):
    params = parse_datatable(request)
    order_num = str(params.get("order_num") or "")
    user_id = str(params.get("user_id") or "")
    pay_type = str(params.get("pay_type") or "")
    pay_way = str(params.get("pay_way") or "")
    total = billing_repo.count_pay_logs(
        order_num=order_num,
        user_id=user_id,
        pay_type=pay_type,
        pay_way=pay_way,
    )
    rows = billing_repo.list_pay_logs(
        offset=params["offset"],
        limit=params["limit"],
        order_num=order_num,
        user_id=user_id,
        pay_type=pay_type,
        pay_way=pay_way,
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def payment_apply_list(request: Request, user=None):
    params = parse_datatable(request)
    status = str(params.get("status") or "")
    start_time = str(params.get("order_startime") or "")
    end_time = str(params.get("order_endtime") or "")
    total = billing_repo.count_payment_applications(
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    rows = billing_repo.list_payment_applications(
        offset=params["offset"],
        limit=params["limit"],
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def payment_apply_detail(request: Request, user=None):
    apply_id = request.query_params.get("id") or request.data.get("id")
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    row = billing_repo.get_payment_application(int(apply_id))
    if not row:
        return Response(ajax_fail("付款申请不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def payment_apply_agree(request: Request, user=None):
    apply_id = request.data.get("id") or request.query_params.get("id")
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    ok, msg = billing_service.agree_payment(apply_id=int(apply_id), staff_user_id=_staff_id(user))
    return Response(ajax_ok(res_msg=msg) if ok else ajax_fail(msg))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def payment_apply_refuse(request: Request, user=None):
    apply_id = request.data.get("id") or request.query_params.get("id")
    mark = request.data.get("mark") or request.query_params.get("mark") or ""
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    ok, msg = billing_service.refuse_payment(
        apply_id=int(apply_id), staff_user_id=_staff_id(user), mark=str(mark)
    )
    return Response(ajax_ok(res_msg=msg) if ok else ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def retest_list(request: Request, user=None):
    params = parse_datatable(request)
    status = str(params.get("status") or "")
    start_time = str(params.get("order_startime") or "")
    end_time = str(params.get("order_endtime") or "")
    total = billing_repo.count_retest_applications(
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    rows = billing_repo.list_retest_applications(
        offset=params["offset"],
        limit=params["limit"],
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def retest_detail(request: Request, user=None):
    apply_id = request.query_params.get("id") or request.data.get("id")
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    row = billing_repo.get_retest_detail(int(apply_id))
    if not row:
        return Response(ajax_fail("复测申请不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def retest_agree(request: Request, user=None):
    apply_id = request.data.get("id") or request.query_params.get("id")
    mark = request.data.get("mark") or request.query_params.get("mark") or ""
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    ok, msg = billing_service.agree_retest(
        apply_id=int(apply_id), staff_user_id=_staff_id(user), mark=str(mark)
    )
    return Response(ajax_ok(res_msg=msg) if ok else ajax_fail(msg))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def retest_refuse(request: Request, user=None):
    apply_id = request.data.get("id") or request.query_params.get("id")
    mark = request.data.get("mark") or request.query_params.get("mark") or ""
    if not apply_id:
        return Response(ajax_fail("缺少 id"))
    ok, msg = billing_service.refuse_retest(
        apply_id=int(apply_id), staff_user_id=_staff_id(user), mark=str(mark)
    )
    return Response(ajax_ok(res_msg=msg) if ok else ajax_fail(msg))
