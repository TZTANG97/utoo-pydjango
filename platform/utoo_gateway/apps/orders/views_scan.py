"""小程序扫码 HTTP — /api/wx/scanCodeOperate.ajax、isFlag.ajax。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import merge_payload
from apps.orders.services import scan_operate as scan_svc
from qd_common.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def scan_code_operate(request: Request):
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
    if ok:
        return Response(ajax_ok(res_msg=msg or "操作成功!"))
    return Response(ajax_fail(msg or "操作失败"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def is_flag(request: Request):
    data = merge_payload(request)
    ok, msg = scan_svc.is_flag(child_id=data.get("childId") or data.get("child_id"))
    if ok:
        return Response(ajax_ok(res_msg=msg or "有确认权限!"))
    return Response(ajax_fail(msg or "无确认权限"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def confirm_save(request: Request):
    data = merge_payload(request)
    ok, msg = scan_svc.confirm_save(
        child_id=data.get("childId") or data.get("child_id"),
        mark=str(data.get("mark") or ""),
        accessory_ids=data.get("ids") or data.get("accessoryIds") or data.get("accessoryId") or "",
    )
    if ok:
        return Response(ajax_ok(obj=True, res_msg=msg or "确认成功！"))
    return Response(ajax_fail(msg or "确认失败"))
