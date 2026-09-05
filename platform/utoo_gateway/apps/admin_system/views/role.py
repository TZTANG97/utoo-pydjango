from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import role as role_repo
from apps.admin_system.views.common import merge_payload, split_ids
from apps.core.responses import ajax_fail, ajax_ok


def _role_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "role_name": (data.get("roleName") or data.get("role_name") or "").strip(),
        "role_desc": data.get("roleDesc") or data.get("role_desc"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = role_repo.list_roles(
        role_name=(data.get("roleName") or data.get("role_name") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_id = data.get("id")
    if not role_id:
        return Response(ajax_fail("数据错误"))
    row = role_repo.get_role(str(role_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _role_payload(data)
    if not payload["role_name"]:
        return Response(False)
    role_repo.insert_role(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _role_payload(data)
    if not payload["id"] or not payload["role_name"]:
        return Response(False)
    role_repo.update_role(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_ids = split_ids(data.get("id") or data.get("ids"))
    if not role_ids:
        return Response(False)
    role_repo.delete_roles(role_ids)
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_power_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_id = data.get("id") or data.get("roleId") or data.get("role_id")
    if not role_id:
        return Response(ajax_fail("数据错误"))
    menu_ids = role_repo.get_role_menu_ids(str(role_id))
    return ajax_response(True, obj=menu_ids)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_power_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_id = data.get("id") or data.get("roleId") or data.get("role_id")
    if not role_id:
        return Response(False)
    menu_ids = split_ids(data.get("menuIds") or data.get("menu_ids"))
    role_repo.set_role_menus(str(role_id), menu_ids)
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_users_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_id = data.get("roleId") or data.get("role_id") or data.get("id")
    if not role_id:
        return Response(ajax_fail("数据错误"))
    draw, page, page_size = parse_datatable_params(request)
    rows, total = role_repo.list_role_users(str(role_id), page, page_size)
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_add_users(request: Request, user=None):
    del user
    data = merge_payload(request)
    role_id = data.get("roleId") or data.get("role_id") or data.get("id")
    user_ids = split_ids(data.get("userIds") or data.get("user_ids"))
    if not role_id or not user_ids:
        return Response(False)
    role_repo.add_users_to_role(str(role_id), user_ids)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def role_remove_users(request: Request, user=None):
    del user
    data = merge_payload(request)
    pairs = split_ids(data.get("ids") or data.get("userRoleIds") or data.get("user_role_ids"))
    if not pairs:
        role_id = data.get("roleId") or data.get("role_id")
        user_ids = split_ids(data.get("userIds") or data.get("user_ids"))
        if role_id and user_ids:
            pairs = [f"{role_id}:{uid}" for uid in user_ids]
    if not pairs:
        return Response(False)
    role_repo.remove_users_from_role(pairs)
    return Response(True)
