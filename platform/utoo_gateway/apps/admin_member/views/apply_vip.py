from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_member.repositories import apply_vip as apply_repo
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
def apply_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = apply_repo.list_applies(
        company_name=(data.get("company_name") or data.get("companyName") or "").strip(),
        state=data.get("state"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def apply_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    apply_id = _to_int(data.get("id"))
    if not apply_id:
        return Response(ajax_fail("参数错误"))
    row = apply_repo.get_apply(apply_id)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def apply_update(request: Request, user=None):
    """type=1 转会员 / type=2 拒绝。转会员通常走企业会员保存并带 applyuserId。"""
    data = merge_payload(request)
    apply_id = _to_int(data.get("id"))
    op_type = _to_int(data.get("type"))
    if not apply_id or op_type not in (1, 2):
        return Response(ajax_fail("参数错误"))
    operator_id = None
    if user:
        operator_id = str(user.get("user_id") or user.get("id") or "") or None
    state = 1 if op_type == 1 else 2
    apply_repo.set_state(apply_id, state=state, operator_id=operator_id)
    return Response(ajax_ok(res_msg="操作成功"))
