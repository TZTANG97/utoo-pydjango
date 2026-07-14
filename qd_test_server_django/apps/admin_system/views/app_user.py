from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import app_user as app_user_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def app_user_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = app_user_repo.list_app_users(
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        mobile_phone_number=(
            data.get("mobilePhoneNumber") or data.get("mobile_phone_number") or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def app_user_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = data.get("id")
    if not user_id:
        return Response(ajax_fail("数据错误"))
    row = app_user_repo.get_app_user(str(user_id))
    return Response(ajax_ok(obj=row))
