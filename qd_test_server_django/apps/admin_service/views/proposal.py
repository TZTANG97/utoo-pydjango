from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.helpers import staff_id
from apps.admin_service.repositories import proposal as proposal_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def prove_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = proposal_repo.list_proposals(
        platform=str(data.get("platform") or "").strip(),
        is_confirmed=(
            str(data.get("is_confirmed")).strip()
            if data.get("is_confirmed") not in (None, "")
            else ""
        ),
        order_startime=(data.get("order_startime") or "").strip(),
        order_endtime=(data.get("order_endtime") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def prove_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    proposal_id = data.get("id")
    if not proposal_id:
        return Response(ajax_fail("数据错误"))
    detail = proposal_repo.get_proposal_detail(int(proposal_id))
    if not detail:
        return Response(ajax_fail("提案不存在"))
    return Response(ajax_ok(obj=detail, res_msg="获取成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def update_proposal_improve(request: Request, user=None):
    data = merge_payload(request)
    proposal_id = data.get("id")
    action_type = str(data.get("type") or "")
    if not proposal_id or action_type not in {"1", "2"}:
        return Response(ajax_fail("参数错误"))
    log_info = "确认该提案" if action_type == "1" else "解决该提案"
    proposal_repo.update_proposal(
        proposal_id=int(proposal_id),
        is_confirmed=int(action_type),
        operator_id=staff_id(user),
        log_info=log_info,
    )
    return Response(ajax_ok(res_msg="修改成功!"))
