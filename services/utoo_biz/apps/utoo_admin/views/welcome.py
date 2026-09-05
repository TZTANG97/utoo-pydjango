"""UTOO welcome 编排（方案 B：产品逻辑在 utoo_biz）。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.utoo_experiment.auth import get_staff_user, is_sy_staff
from shared.utoo_welcome.service import build_welcome_payload


def _ajax_ok(obj=None, res_msg: str = "操作成功") -> dict:
    return {"res": True, "resMsg": res_msg, "obj": obj}


def _ajax_fail(res_msg: str = "操作失败", obj=None) -> dict:
    return {"res": False, "resMsg": res_msg, "obj": obj}


def _bearer_token(request: Request) -> str:
    auth = (request.META.get("HTTP_AUTHORIZATION") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (
        (request.META.get("HTTP_TOKEN") or "").strip()
        or (request.query_params.get("access_token") or "").strip()
        or (request.query_params.get("token") or "").strip()
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def welcome(request: Request):
    user = get_staff_user(request)
    if not is_sy_staff(user):
        return Response(_ajax_fail("用户未登录或登录已失效，请重新登录"))
    assert user is not None
    body = getattr(request, "data", None) or {}
    chart_year = request.query_params.get("year") or (
        body.get("year") if isinstance(body, dict) else None
    )
    order_type = (
        request.query_params.get("order_type")
        or (body.get("order_type") if isinstance(body, dict) else None)
        or (body.get("orderType") if isinstance(body, dict) else None)
    )
    try:
        cy = int(chart_year) if chart_year not in (None, "") else None
    except (TypeError, ValueError):
        cy = None
    try:
        obj = build_welcome_payload(
            user,
            token=_bearer_token(request),
            chart_year=cy,
            order_type_filter=str(order_type or ""),
        )
    except Exception as exc:
        return Response(_ajax_fail(f"欢迎页加载失败：{exc}"))
    return Response(_ajax_ok(obj=obj))
