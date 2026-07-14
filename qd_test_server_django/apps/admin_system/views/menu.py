from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_system.repositories import menu as menu_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _menu_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "menu_super_id": data.get("menuSuperId") or data.get("menu_super_id") or "0",
        "menu_status": int(data.get("menuStatus") or data.get("menu_status") or 1),
        "menu_sort": int(data.get("menuSort") or data.get("menu_sort") or 0),
        "menu_name": (data.get("menuName") or data.get("menu_name") or "").strip(),
        "menu_icon": data.get("menuIcon") or data.get("menu_icon"),
        "menu_url": data.get("menuUrl") or data.get("menu_url"),
        "menu_target": data.get("menuTarget") or data.get("menu_target") or "navTab",
        "menu_rel": data.get("menuRel") or data.get("menu_rel"),
        "menu_open": data.get("menuOpen") or data.get("menu_open") or "false",
        "menu_external": data.get("menuExternal") or data.get("menu_external") or "false",
        "menu_fresh": data.get("menuFresh") or data.get("menu_fresh") or "true",
        "pt_type": data.get("ptType") or data.get("pt_type") or "2",
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def menu_tree(_request: Request, user=None):
    del user
    return ajax_response(True, obj=menu_repo.list_menu_tree())


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def menu_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    menu_id = data.get("id")
    if not menu_id:
        return Response(ajax_fail("数据错误"))
    row = menu_repo.get_menu(str(menu_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def menu_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _menu_payload(data)
    if not payload["menu_name"]:
        return Response(False)
    menu_repo.insert_menu(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def menu_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _menu_payload(data)
    if not payload["id"] or not payload["menu_name"]:
        return Response(False)
    menu_repo.update_menu(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def menu_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    menu_id = data.get("id")
    if not menu_id:
        return Response(False)
    menu_repo.delete_menu(str(menu_id))
    return Response(True)
