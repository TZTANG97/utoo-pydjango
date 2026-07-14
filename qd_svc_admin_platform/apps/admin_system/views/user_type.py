from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import user_type as user_type_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _user_type_payload(data: dict) -> dict:
    role_id = data.get("roleId") or data.get("role_id")
    return {
        "id": data.get("id"),
        "type_name": (data.get("typeName") or data.get("type_name") or "").strip(),
        "type_desc": data.get("typeDesc") or data.get("type_desc"),
        "type_sort": data.get("typeSort") or data.get("type_sort") or "0",
        "true_type": data.get("trueType") or data.get("true_type"),
        "type": data.get("type") or 2,
        "role_id": int(role_id) if role_id not in (None, "") else None,
        "is_fixed": int(data.get("isFixed") or data.get("is_fixed") or 0),
        "fixed_scale": data.get("fixedScale") or data.get("fixed_scale"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_type_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = user_type_repo.list_user_types(
        type_name=(data.get("typeName") or data.get("type_name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_type_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_id = data.get("id")
    if not type_id:
        return Response(ajax_fail("数据错误"))
    row = user_type_repo.get_user_type(str(type_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_type_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _user_type_payload(data)
    if not payload["type_name"]:
        return Response(False)
    user_type_repo.insert_user_type(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_type_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _user_type_payload(data)
    if not payload["id"] or not payload["type_name"]:
        return Response(False)
    user_type_repo.update_user_type(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_type_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    type_id = data.get("id")
    if not type_id:
        return Response(False)
    user_type_repo.delete_user_type(str(type_id))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def type_role_options(_request: Request, user=None):
    del user
    return ajax_response(True, obj=user_type_repo.list_type_role_options())
