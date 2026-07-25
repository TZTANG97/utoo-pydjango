from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import test_address as address_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _address_payload(data: dict) -> dict:
    return {
        "true_name": (data.get("trueName") or data.get("true_name") or "").strip(),
        "mobile": (data.get("mobile") or "").strip(),
        "address": (data.get("address") or "").strip(),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def address_list(request: Request, user=None):
    del user
    draw, page, page_size = parse_datatable_params(request)
    rows, total = address_repo.list_addresses(page=page, page_size=page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=False)
def address_list_mp(request: Request, user=None):
    """小程序 addressList.ajax：{res, obj:[{id,true_name,mobile,address},...]}。"""
    del request, user
    rows, _total = address_repo.list_addresses(page=1, page_size=1000)
    obj = [
        {
            "id": row.get("id"),
            "true_name": row.get("trueName") or "",
            "trueName": row.get("trueName") or "",
            "mobile": row.get("mobile") or "",
            "address": row.get("address") or "",
        }
        for row in rows
    ]
    return Response(ajax_ok(obj=obj, res_msg="获取成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def address_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    address_id = data.get("id")
    if not address_id:
        return Response(ajax_fail("数据错误"))
    row = address_repo.get_address(int(address_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def address_create(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _address_payload(data)
    if not payload["true_name"] or not payload["address"]:
        return Response(False)
    address_repo.insert_address(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def address_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    address_id = data.get("id")
    payload = _address_payload(data)
    if not address_id:
        return Response(False)
    address_repo.update_address(int(address_id), payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def address_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    address_id = data.get("id")
    if not address_id:
        return Response(False)
    address_repo.soft_delete_address(int(address_id))
    return Response(True)
