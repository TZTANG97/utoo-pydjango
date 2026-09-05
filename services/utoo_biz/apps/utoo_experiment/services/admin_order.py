"""愉兔实验订单业务层（阶段 A-4：列表 scope + 审核前置）。"""
from __future__ import annotations

from django.http import JsonResponse
from rest_framework.request import Request

from apps.utoo_experiment.auth import get_staff_user, is_sy_staff
from apps.utoo_experiment.clients import order_mid as order_mid_client
from apps.utoo_experiment.repositories import audit_gate, list_scope
from shared.utoo_biz_headers import (
    AUDIT_VALIDATED_HEADER,
    LIST_SCOPE_HEADER,
    encode_list_scope,
)
from shared.utoo_order_proxy import proxy_utoo_order_request

_LIST_SCOPE_SUFFIXES = ("/order/list.ajax", "/order/export.ajax")

_AUDIT_PATHS = {
    "/api/adminExperiment/order/audit.ajax": audit_gate.validate_audit,
    "/api/adminExperiment/order/submitAudit.ajax": audit_gate.validate_submit_audit,
    "/api/adminExperiment/order/withdrawAudit.ajax": audit_gate.validate_withdraw_audit,
}

_STAFF_REQUIRED_PREFIXES = (
    "/api/adminExperiment/order/",
)


def _channel_for_path(path: str) -> str:
    if "/adminExperiment/" in path:
        return "admin"
    return "mall_qd"


def _ajax_fail(msg: str, *, status: int = 200):
    return JsonResponse({"res": 0, "resMsg": msg, "obj": None}, status=status)


def _merge_payload(request: Request) -> dict:
    q = {k: request.query_params.get(k) for k in request.query_params.keys()}
    raw = request.data
    if hasattr(raw, "get") and hasattr(raw, "keys") and not isinstance(raw, dict):
        body = {k: raw.get(k) for k in raw.keys()}
    elif isinstance(raw, dict):
        body = {k: raw.get(k) for k in raw.keys()}
    else:
        body = {}
    return {**q, **body}


def _order_id_from_request(request: Request) -> int | None:
    data = _merge_payload(request)
    for key in ("id", "ofId", "orderId", "order_id"):
        val = data.get(key)
        if val in (None, ""):
            continue
        try:
            return int(val)
        except (TypeError, ValueError):
            continue
    return None


def _order_type_from_request(request: Request) -> str:
    data = _merge_payload(request)
    return str(data.get("orderType") or data.get("order_type") or "6")


def _needs_staff(path: str) -> bool:
    if path in _AUDIT_PATHS:
        return True
    if path.endswith(_LIST_SCOPE_SUFFIXES):
        return True
    return any(path.startswith(prefix) for prefix in _STAFF_REQUIRED_PREFIXES)


def _build_extra_headers(request: Request, path: str, user: dict | None) -> tuple[dict[str, str], JsonResponse | None]:
    extra: dict[str, str] = {}

    if path.endswith(_LIST_SCOPE_SUFFIXES):
        if not is_sy_staff(user):
            return extra, _ajax_fail("用户未登录或登录已失效，请重新登录")
        order_type = _order_type_from_request(request)
        scope = list_scope.build_list_scope_for_order_type(user, order_type)
        extra[LIST_SCOPE_HEADER] = encode_list_scope(scope)

    validator = _AUDIT_PATHS.get(path)
    if validator:
        if not is_sy_staff(user):
            return extra, _ajax_fail("用户未登录或登录已失效，请重新登录")
        order_id = _order_id_from_request(request)
        if not order_id:
            return extra, _ajax_fail("参数错误")
        ok, msg = validator(user, order_id)
        if not ok:
            return extra, _ajax_fail(msg)
        extra[AUDIT_VALIDATED_HEADER] = "1"

    return extra, None


def forward_legacy_ajax(request: Request, path: str):
    user = get_staff_user(request)
    if _needs_staff(path) and not is_sy_staff(user):
        return _ajax_fail("用户未登录或登录已失效，请重新登录")

    extra_headers, err = _build_extra_headers(request, path, user)
    if err is not None:
        return err

    return order_mid_client.forward(
        request,
        path,
        channel=_channel_for_path(path),
        extra_headers=extra_headers or None,
    )


def forward_named_resource(request, resource: str):
    return proxy_utoo_order_request(request, resource)
