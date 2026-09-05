"""网关扫码：优先转发订单服务；否则本地孪生。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import merge_payload
from apps.core.order_forward import forward_order, svc_order_enabled
from apps.core.responses import ajax_fail, ajax_ok
from apps.orders.services import scan_operate as scan_svc


def _maybe_forward(request: Request):
    if svc_order_enabled():
        return forward_order(request, request.path)
    return None


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def scan_code_operate(request: Request):
    fwd = _maybe_forward(request)
    if fwd is not None:
        return fwd
    data = merge_payload(request)
    ok, msg = scan_svc.scan_code_operate(
        type=data.get("type"),
        child_id=data.get("childId") or data.get("child_id"),
        store_pos_id=data.get("storePosId") or data.get("store_pos_id") or "",
        new_store_pos_id=data.get("newStorePosId") or data.get("new_store_pos_id") or "",
        is_position=data.get("isPosition") if "isPosition" in data else data.get("is_position", "0"),
        line_id=data.get("lineId") or data.get("line_id") or "",
        express_no=str(data.get("expressNo") or data.get("express_no") or ""),
        express_name=str(data.get("expressName") or data.get("express_name") or ""),
        meeting_num=str(data.get("meeting_num") or data.get("meetingNum") or ""),
        setting_time=str(data.get("setting_time") or data.get("settingTime") or ""),
        finish_time=data.get("finish_time") if "finish_time" in data else data.get("finishTime"),
        time_type=data.get("time_type") if "time_type" in data else data.get("timeType"),
        key=data.get("key") or "1",
    )
    return Response(ajax_ok(res_msg=msg or "操作成功!") if ok else ajax_fail(msg or "操作失败"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def is_flag(request: Request):
    fwd = _maybe_forward(request)
    if fwd is not None:
        return fwd
    data = merge_payload(request)
    ok, msg = scan_svc.is_flag(child_id=data.get("childId") or data.get("child_id"))
    return Response(ajax_ok(res_msg=msg or "有确认权限!") if ok else ajax_fail(msg or "无确认权限"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def confirm_save(request: Request):
    """本地兜底；正常走 experimentChildOrder 代理。"""
    fwd = _maybe_forward(request)
    if fwd is not None:
        return fwd
    data = merge_payload(request)
    ok, msg = scan_svc.confirm_save(
        child_id=data.get("childId") or data.get("child_id"),
        mark=str(data.get("mark") or ""),
        accessory_ids=data.get("ids") or data.get("accessoryIds") or data.get("accessoryId") or "",
    )
    return Response(
        ajax_ok(obj=True, res_msg=msg or "确认成功！") if ok else ajax_fail(msg or "确认失败")
    )
