from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_member.repositories import integral as integral_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def integral_get(request: Request, user=None):
    del user
    del request
    return Response(ajax_ok(obj=integral_repo.get_integral_setting()))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def expire_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    try:
        days = int(data.get("expireDate") or data.get("expireIntegralDay") or 0)
    except (TypeError, ValueError):
        return Response(ajax_fail("参数错误"))
    if days < 0:
        return Response(ajax_fail("有效期不能为负数"))
    integral_repo.save_expire_days(days)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def ratio_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    try:
        ratio = float(data.get("integral_convert_ratio") or data.get("integralConvertRatio") or 0)
    except (TypeError, ValueError):
        return Response(ajax_fail("参数错误"))
    if ratio < 0:
        return Response(ajax_fail("兑换比例不能为负数"))
    integral_repo.save_convert_ratio(ratio)
    return Response(ajax_ok(res_msg="保存成功"))
