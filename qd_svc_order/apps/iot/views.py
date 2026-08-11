"""IOT API 视图。"""
from __future__ import annotations

import json
import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.admin_ajax import admin_ajax_view, fail, ok
from apps.admin_experiment.helpers import merge_payload, to_int
from apps.auth_support.helpers import get_current_user_from_request
from apps.iot import hmac_auth, services
from apps.iot.hmac_auth import HmacAuthError
from apps.iot.services import ServiceError
from qd_common.responses import ajax_fail, ajax_ok

logger = logging.getLogger(__name__)


def _callback_error(code: str, message: str, http_status: int) -> JsonResponse:
    return JsonResponse(
        {"ok": False, "code": code, "message": message},
        status=http_status,
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def auth_login(request: Request, user=None):
    data = merge_payload(request)
    try:
        result = services.auth_iot_login(
            username=str(data.get("username") or data.get("userName") or ""),
            password=str(data.get("password") or ""),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": exc.code})


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def auth_status(request: Request, user=None):
    return ok(obj=services.auth_iot_status(user=user))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def auth_logout(request: Request, user=None):
    return ok(obj=services.auth_iot_logout(user=user))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_list(request: Request, user=None):
    data = merge_payload(request)
    try:
        result = services.list_devices(
            q=str(data.get("q") or data.get("keyword") or ""),
            limit=to_int(data.get("limit")) or 200,
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": exc.code})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_bind(request: Request, user=None):
    """兼容旧绑定接口：忽略 deviceId，改为创建试验任务。"""
    data = merge_payload(request)
    try:
        result = services.bind_device(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_id=to_int(data.get("childId") or data.get("child_id")),
            device_id=str(data.get("deviceId") or data.get("device_id") or ""),
            remark=str(data.get("remark") or ""),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def create_task(request: Request, user=None):
    data = merge_payload(request)
    try:
        # 兼容：传 childIds 数组则走批量
        raw_ids = data.get("childIds") or data.get("child_ids")
        if isinstance(raw_ids, list) and raw_ids:
            ids = [to_int(x) for x in raw_ids if to_int(x)]
            result = services.create_tasks_batch(
                order_id=str(data.get("orderId") or data.get("order_id") or ""),
                child_ids=ids,
                remark=str(data.get("remark") or ""),
                user=user,
            )
            return ok(obj=result)
        # all=1 且无 childId：整单批量
        if str(data.get("all") or "").strip() in ("1", "true", "True", "yes") and not to_int(
            data.get("childId") or data.get("child_id")
        ):
            result = services.create_tasks_batch(
                order_id=str(data.get("orderId") or data.get("order_id") or ""),
                child_ids=None,
                remark=str(data.get("remark") or ""),
                user=user,
            )
            return ok(obj=result)
        result = services.create_task(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_id=to_int(data.get("childId") or data.get("child_id")),
            remark=str(data.get("remark") or ""),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def create_tasks_batch(request: Request, user=None):
    data = merge_payload(request)
    raw_ids = data.get("childIds") or data.get("child_ids")
    ids = None
    if isinstance(raw_ids, list):
        ids = [to_int(x) for x in raw_ids if to_int(x)]
    try:
        result = services.create_tasks_batch(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_ids=ids,
            remark=str(data.get("remark") or ""),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def sso_jump(request: Request, user=None):
    data = merge_payload(request)
    try:
        result = services.build_sso_jump(
            user=user,
            task_id=str(data.get("taskId") or data.get("iotTaskId") or ""),
            redirect=str(data.get("redirect") or ""),
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_unbind(request: Request, user=None):
    data = merge_payload(request)
    try:
        result = services.unbind_device(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_id=to_int(data.get("childId") or data.get("child_id")),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_binding(request: Request, user=None):
    data = merge_payload(request)
    order_id = str(data.get("orderId") or data.get("order_id") or "").strip()
    child_id = to_int(data.get("childId") or data.get("child_id"))
    # 仅 orderId：返回整单总览
    if order_id and not child_id:
        try:
            result = services.list_order_task_overview(order_id=order_id)
            return ok(obj=result)
        except ServiceError as exc:
            return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})
    if not child_id:
        return fail("参数错误：childId 或 orderId 必填")
    result = services.get_binding(
        order_id=order_id,
        child_id=child_id,
    )
    if not result:
        return fail("未找到绑定", obj={"code": "BIND_NOT_FOUND"})
    return ok(obj=result)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def task_overview(request: Request, user=None):
    data = merge_payload(request)
    try:
        result = services.list_order_task_overview(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def device_resync(request: Request, user=None):
    data = merge_payload(request)
    raw_ids = data.get("childIds") or data.get("child_ids")
    try:
        if isinstance(raw_ids, list) and raw_ids:
            ids = [to_int(x) for x in raw_ids if to_int(x)]
            result = services.resync_tasks_batch(
                order_id=str(data.get("orderId") or data.get("order_id") or ""),
                child_ids=ids,
                user=user,
            )
            return ok(obj=result)
        if str(data.get("all") or "").strip() in ("1", "true", "True", "yes") and not to_int(
            data.get("childId") or data.get("child_id")
        ):
            result = services.resync_tasks_batch(
                order_id=str(data.get("orderId") or data.get("order_id") or ""),
                child_ids=None,
                user=user,
            )
            return ok(obj=result)
        result = services.resync_device(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_id=to_int(data.get("childId") or data.get("child_id")),
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def resync_tasks_batch(request: Request, user=None):
    data = merge_payload(request)
    raw_ids = data.get("childIds") or data.get("child_ids")
    ids = None
    if isinstance(raw_ids, list):
        ids = [to_int(x) for x in raw_ids if to_int(x)]
    try:
        result = services.resync_tasks_batch(
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_ids=ids,
            user=user,
        )
        return ok(obj=result)
    except ServiceError as exc:
        return fail(exc.message, obj={"code": getattr(exc, "code", None) or "FAIL"})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def callback_experiment_event(request: Request):
    raw = request.body or b""
    try:
        hmac_auth.verify_iot_hmac(request, raw)
    except HmacAuthError as exc:
        status = 401
        return _callback_error(exc.code, exc.message, status)

    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = request.data if isinstance(request.data, dict) else {}
    if not isinstance(payload, dict):
        return _callback_error("FAIL", "请求体无效", 400)

    try:
        result = services.handle_experiment_event(payload)
        http_status = int(result.pop("http_status", 200))
        return JsonResponse(result, status=http_status)
    except ServiceError as exc:
        return _callback_error(exc.code, exc.message, exc.http_status)
    except Exception as exc:
        logger.exception("IOT callback failed: %s", exc)
        return _callback_error("INTERNAL", "内部错误", 500)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def experiment_data(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return Response(ajax_fail("用户未登录或登录已失效，请重新登录"))
    data = merge_payload(request)
    include = str(data.get("includeSeries") or data.get("include_series") or "0").strip() in (
        "1",
        "true",
        "True",
        "yes",
    )
    try:
        result = services.get_experiment_data(
            user=user,
            order_id=str(data.get("orderId") or data.get("order_id") or ""),
            child_id=to_int(data.get("childId") or data.get("child_id")),
            include_series=include,
        )
        return Response(ajax_ok(obj=result))
    except ServiceError as exc:
        return Response(ajax_fail(exc.message, obj={"code": exc.code}))
    except Exception as exc:
        logger.exception("experiment_data failed: %s", exc)
        return Response(ajax_fail(f"获取试验数据失败: {exc}"))
