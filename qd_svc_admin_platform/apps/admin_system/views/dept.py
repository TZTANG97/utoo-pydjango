from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_system.repositories import dept as dept_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _dept_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "dept_sort": data.get("deptSort") or data.get("dept_sort") or 0,
        "dept_name": (data.get("deptName") or data.get("dept_name") or "").strip(),
        "dept_phone": data.get("deptPhone") or data.get("dept_phone"),
        "dept_fax": data.get("deptFax") or data.get("dept_fax"),
        "dept_address": data.get("deptAddress") or data.get("dept_address"),
        "super_id": data.get("superId") or data.get("super_id") or "0",
        "lead_uid": data.get("leadUid") or data.get("lead_uid"),
        "dept_desc": data.get("deptDesc") or data.get("dept_desc"),
        "lab_ids": data.get("labIds") or data.get("lab_ids"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_tree(_request: Request, user=None):
    del user
    return ajax_response(True, obj=dept_repo.list_all_depts())


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    dept_id = data.get("id")
    if not dept_id:
        return Response(ajax_fail("数据错误"))
    row = dept_repo.get_dept(str(dept_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _dept_payload(data)
    if not payload["dept_name"]:
        return Response(False)
    dept_repo.insert_dept(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _dept_payload(data)
    if not payload["id"] or not payload["dept_name"]:
        return Response(False)
    dept_repo.update_dept(payload)
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    dept_id = data.get("id")
    if not dept_id:
        return Response(False)
    dept_repo.delete_dept(str(dept_id))
    return Response(True)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def dept_options(_request: Request, user=None):
    del user
    return ajax_response(True, obj=dept_repo.list_dept_options())
