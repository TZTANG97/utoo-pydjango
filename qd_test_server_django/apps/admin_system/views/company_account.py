from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import company_account as account_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _account_payload(data: dict) -> dict:
    return {
        "company_name": (data.get("companyName") or data.get("company_name") or "").strip(),
        "bankCardNum": (data.get("bankCardNum") or data.get("bank_card_num") or "").strip(),
        "bank": (data.get("bank") or "").strip(),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = account_repo.list_accounts(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = data.get("id")
    if not account_id:
        return Response(ajax_fail("数据错误"))
    row = account_repo.get_account(int(account_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_create(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _account_payload(data)
    if not payload["company_name"] or not payload["bankCardNum"]:
        return Response(False)
    if account_repo.find_by_card_num(payload["bankCardNum"]):
        return Response(False)
    account_repo.insert_account(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = data.get("id")
    payload = _account_payload(data)
    if not account_id:
        return Response(False)
    if payload["bankCardNum"] and account_repo.find_by_card_num(
        payload["bankCardNum"], exclude_id=int(account_id)
    ):
        return Response(False)
    account_repo.update_account(int(account_id), payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = data.get("id")
    if not account_id:
        return Response(False)
    row = account_repo.get_account(int(account_id))
    if not row:
        return Response(False)
    if row.get("defaultAccount") == 1:
        return Response(False)
    account_repo.soft_delete_account(int(account_id))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_default_get(_request: Request, user=None):
    del user
    row = account_repo.get_default_account()
    return ajax_response(True, obj=row)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_default_set(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = data.get("id")
    if not account_id:
        return Response(False)
    row = account_repo.get_account(int(account_id))
    if not row:
        return Response(False)
    account_repo.set_default_account(int(account_id))
    return Response(True)
