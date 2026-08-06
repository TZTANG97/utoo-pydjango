from __future__ import annotations

from decimal import Decimal, InvalidOperation

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_member.repositories import member as member_repo
from apps.admin_member.repositories import offline_recharge as recharge_repo
from apps.admin_system.views.common import merge_payload, split_ids
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_accessory_ids(data: dict, request: Request) -> list[int]:
    raw = data.get("accessoryId") or data.get("accessoryIds") or data.get("accessory_id")
    if raw in (None, "") and hasattr(request.data, "getlist"):
        raw = request.data.getlist("accessoryId") or request.data.getlist("accessoryIds")
    ids: list[int] = []
    for part in split_ids(raw):
        aid = _to_int(part)
        if aid:
            ids.append(aid)
    return ids


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def recharge_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = recharge_repo.list_recharges(
        user_id=str(data.get("user_id") or data.get("userId") or "").strip(),
        recharge_num=(data.get("recharge_num") or data.get("rechargeNum") or "").strip(),
        start_time=(
            data.get("startTime")
            or data.get("startime")
            or data.get("order_startime")
            or ""
        ).strip(),
        end_time=(
            data.get("endTime")
            or data.get("endtime")
            or data.get("order_endtime")
            or ""
        ).strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def recharge_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    rid = _to_int(data.get("id"))
    if not rid:
        return Response(ajax_fail("参数错误"))
    row = recharge_repo.get_recharge(rid)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_picker(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = member_repo.list_picker(
        mobile=(data.get("mobile") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def recharge_add(request: Request, user=None):
    data = merge_payload(request)
    user_id = _to_int(data.get("user_id") or data.get("userId"))
    mark = (data.get("mark") or "").strip()
    recharge_type = _to_int(data.get("recharge_type") or data.get("rechargeType"), 0)
    if not user_id:
        return Response(ajax_fail("请选择会员"))
    try:
        money = Decimal(str(data.get("money") or "0"))
    except (InvalidOperation, TypeError, ValueError):
        return Response(ajax_fail("金额格式错误"))
    if money <= 0:
        return Response(ajax_fail("金额必须大于0"))
    member = member_repo.get_member(user_id)
    if not member:
        return Response(ajax_fail("该用户不存在,请重试!!!!"))
    add_user_id = "1"
    if user:
        add_user_id = str(user.get("user_id") or user.get("id") or "1")
    rid = recharge_repo.create_recharge(
        user_id=user_id,
        money=money,
        mark=mark,
        recharge_type=recharge_type if recharge_type in (0, 1) else 0,
        add_user_id=add_user_id,
    )
    accessory_ids = _parse_accessory_ids(data, request)
    if accessory_ids:
        recharge_repo.bind_accessories(recharge_id=rid, accessory_ids=accessory_ids)
    return Response(ajax_ok(obj={"id": rid}, res_msg="充值成功"))
