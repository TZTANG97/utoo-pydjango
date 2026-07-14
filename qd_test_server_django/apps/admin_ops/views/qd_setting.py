from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_ops.repositories import qd_setting as setting_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok

TYPE_TO_FIELD = {
    "rent": "rent_device",
    "secondhand": "secondhand_device",
    "deviceservice": "device_service",
    "product": "prodct_test",
    "business": "business_support",
}


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    setting_type = (data.get("settingType") or data.get("setting_type") or "").strip()
    row = setting_repo.get_setting() or {}
    if setting_type and setting_type in TYPE_TO_FIELD:
        col = TYPE_TO_FIELD[setting_type]
        return Response(
            ajax_ok(
                obj={
                    "settingType": setting_type,
                    "imgsrc": row.get(col) or "",
                    "content": row.get(col) or "",
                }
            )
        )
    return Response(
        ajax_ok(
            obj={
                "rentDevice": row.get("rent_device") or "",
                "secondHandDevice": row.get("secondhand_device") or "",
                "deviceService": row.get("device_service") or "",
                "prodctTest": row.get("prodct_test") or "",
                "businessSupport": row.get("business_support") or "",
            }
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    setting_type = (data.get("settingType") or data.get("setting_type") or "").strip()
    content = data.get("imgsrc") if data.get("imgsrc") is not None else data.get("content")
    if content is None:
        content = ""
    if setting_type not in TYPE_TO_FIELD:
        return Response(ajax_fail("参数错误"))
    ok = setting_repo.update_setting_field(setting_type, str(content))
    if not ok:
        return Response(ajax_fail("保存失败"))
    return Response(ajax_ok(res_msg="保存成功"))
