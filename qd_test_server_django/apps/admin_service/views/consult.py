from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.repositories import consult as consult_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _truthy_flag(value) -> int:
    if value in (True, 1, "1", "on", "ON", "true", "True"):
        return 1
    return 0


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def consult_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = consult_repo.list_consults(
        user_name=(data.get("userName") or "").strip(),
        mobile=(data.get("mobile") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def consult_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    consult_id = data.get("id")
    if not consult_id:
        return Response(ajax_fail("数据错误"))
    row = consult_repo.get_consult_detail(int(consult_id))
    if not row:
        return Response(ajax_fail("咨询不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def cancel_consult(request: Request, user=None):
    del user
    data = merge_payload(request)
    consult_id = data.get("id")
    if not consult_id:
        return Response(ajax_fail("取消失败,id为空"))
    consult_repo.cancel_consult(int(consult_id))
    return Response(ajax_ok(res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_get(_request: Request, user=None):
    del user
    return ajax_response(True, obj=consult_repo.get_consult_settings())


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def setting_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    consult_repo.save_consult_settings(
        gzh_user_id=str(data.get("gzh_userId_ut") or data.get("gzh_userId") or "").strip(),
        gzh_issend=_truthy_flag(data.get("gzh_issend_ut") or data.get("gzh_issend")),
        service_mail=str(data.get("service_mail_ut") or data.get("service_mail") or "").strip(),
        mail_issend=_truthy_flag(data.get("mail_issend_ut") or data.get("mail_issend")),
    )
    return ajax_response(True, res_msg="操作成功")


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def isshow_get(_request: Request, user=None):
    del user
    return ajax_response(True, obj=consult_repo.get_is_show())


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def isshow_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    consult_repo.save_is_show(_truthy_flag(data.get("is_show") or data.get("isShow")))
    return ajax_response(True, res_msg="操作成功")
