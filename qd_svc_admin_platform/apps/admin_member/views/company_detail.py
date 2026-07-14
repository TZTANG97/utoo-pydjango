from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_member.repositories import company_detail as detail_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_ok
from apps.core.services import district as district_svc


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def query_pro_city_co(request: Request, user=None):
    """Java member/queryProCityCo.ajax：地区级联。"""
    del user
    data = merge_payload(request)
    super_id = str(data.get("superId") or request.query_params.get("superId") or "")
    rows = district_svc.list_by_super_id(super_id)
    return Response(ajax_ok(obj=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def contact_list_by_company(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    parent_id = data.get("parent_id") or data.get("parentId") or data.get("comId")
    rows, total = detail_repo.list_company_contacts(
        parent_id=parent_id or "",
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def invoice_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    company_id = data.get("company_id") or data.get("companyId")
    rows, total = detail_repo.list_company_invoices(
        company_id=company_id or "",
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def pay_list_0909(request: Request, user=None):
    """付款明细 pay_type=3 / 还款明细 pay_type=2。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    company_id = data.get("company_id") or data.get("companyId")
    pay_type = data.get("pay_type") or data.get("payType")
    rows, total = detail_repo.list_company_pay_logs(
        company_id=company_id or "",
        pay_type=pay_type,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def pay_list_910(request: Request, user=None):
    """余额变更明细。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    company_id = data.get("company_id") or data.get("companyId")
    rows, total = detail_repo.list_company_balance_logs(
        company_id=company_id or "",
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def arrears_list_0909(request: Request, user=None):
    """欠款明细。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    company_id = data.get("company_id") or data.get("companyId")
    rows, total = detail_repo.list_company_arrears(
        company_id=company_id or "",
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


def _resolve_user_mobile(user_id) -> str:
    if not user_id:
        return ""
    try:
        from apps.admin_member.repositories import member as member_repo

        row = member_repo.get_member(int(user_id))
        return str((row or {}).get("mobile") or "")
    except (TypeError, ValueError):
        return ""


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_invoice_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    user_id = data.get("user_id") or data.get("userId")
    mobile = (data.get("mobile") or "").strip() or _resolve_user_mobile(user_id)
    rows, total = detail_repo.list_user_invoices(
        user_id=user_id or "",
        mobile=mobile,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def pay_list_828(request: Request, user=None):
    """个人付款/还款明细。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    user_id = data.get("user_id") or data.get("userId")
    pay_type = data.get("pay_type") or data.get("payType")
    mobile = (data.get("mobile") or "").strip() or _resolve_user_mobile(user_id)
    rows, total = detail_repo.list_user_pay_logs(
        user_id=user_id or "",
        mobile=mobile,
        pay_type=pay_type,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def pay_list(request: Request, user=None):
    """个人余额变更明细。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    user_id = data.get("user_id") or data.get("userId")
    rows, total = detail_repo.list_user_balance_logs(
        user_id=user_id or "",
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def arrears_list(request: Request, user=None):
    """个人欠款明细。"""
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    user_id = data.get("user_id") or data.get("userId")
    mobile = (data.get("mobile") or "").strip() or _resolve_user_mobile(user_id)
    rows, total = detail_repo.list_user_arrears(
        user_id=user_id or "",
        mobile=mobile,
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))
