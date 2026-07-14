from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_ops.repositories import redeem as redeem_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def redeemloglist(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = redeem_repo.list_redeem_logs(
        order_startime=(data.get("order_startime") or "").strip(),
        order_endtime=(data.get("order_endtime") or "").strip(),
        status=data.get("status"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def redeem_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    log_id = _to_int(data.get("id"))
    if not log_id:
        return Response(ajax_fail("参数错误"))
    row = redeem_repo.get_redeem_log(log_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def shipment(request: Request, user=None):
    del user
    data = merge_payload(request)
    log_id = _to_int(data.get("id"))
    mark = (data.get("mark") or "").strip()
    number = (data.get("number") or "").strip()
    if not log_id:
        return Response(ajax_fail("参数错误"))
    if not mark or not number:
        return Response(ajax_fail("请填写快递公司和单号"))
    ok = redeem_repo.ship_redeem_log(log_id=log_id, mark=mark, number=number)
    if not ok:
        return Response(ajax_fail("发货失败"))
    return Response(ajax_ok(res_msg="发货成功"))
