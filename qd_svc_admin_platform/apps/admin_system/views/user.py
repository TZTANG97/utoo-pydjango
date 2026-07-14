from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import user as user_repo
from apps.admin_system.views.common import merge_payload, split_ids
from apps.core.responses import ajax_fail, ajax_ok


def _user_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "user_name": (data.get("userName") or data.get("user_name") or "").strip(),
        "true_name": (data.get("trueName") or data.get("true_name") or "").strip(),
        "user_password": data.get("userPassword") or data.get("user_password"),
        "user_status": int(data.get("userStatus") or data.get("user_status") or 1),
        "dept_id": data.get("deptId") or data.get("dept_id") or "0",
        "mobile_phone_number": data.get("mobilePhoneNumber") or data.get("mobile_phone_number"),
        "email": data.get("email"),
        "type": data.get("type"),
        "show_type": data.get("showType") or data.get("show_type"),
        "user_type_role_id": data.get("userTypeRoleId") or data.get("user_type_role_id"),
        "user_desc": data.get("userDesc") or data.get("user_desc"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = user_repo.list_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = data.get("id")
    if not user_id:
        return Response(ajax_fail("数据错误"))
    row = user_repo.get_user(str(user_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _user_payload(data)
    if not payload["user_name"]:
        return Response(False)
    if user_repo.find_by_login_name(payload["user_name"]):
        return Response(False)
    user_id = user_repo.insert_user(payload)
    role_ids = split_ids(data.get("roleIds") or data.get("role_ids"))
    if role_ids:
        user_repo.set_user_roles(user_id, role_ids)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _user_payload(data)
    if not payload["id"] or not payload["user_name"]:
        return Response(False)
    user_repo.update_user(payload)
    if "roleIds" in data or "role_ids" in data:
        user_repo.set_user_roles(
            str(payload["id"]),
            split_ids(data.get("roleIds") or data.get("role_ids")),
        )
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_disable(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = data.get("id")
    if not user_id:
        return Response(False)
    user_repo.disable_user(str(user_id))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_role_options(_request: Request, user=None):
    del user
    return ajax_response(True, obj=user_repo.list_role_options())
