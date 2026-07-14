from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_service.repositories import faq as faq_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _problem_fields(data: dict) -> dict:
    return {
        "problem_description": (
            data.get("problemDescription")
            or data.get("problem_description")
            or data.get("name")
            or ""
        ).strip(),
        "keywords": (data.get("keywords") or data.get("enname") or "").strip(),
        "problem_answer": (
            data.get("problemAnswer")
            or data.get("problem_answer")
            or data.get("project_details")
            or ""
        ).strip(),
        "hits": int(
            data.get("hits")
            or data.get("sequence")
            or 0
        ),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def problem_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = faq_repo.list_problems(
        problem_description=(data.get("problem_description") or "").strip(),
        keywords=(data.get("keywords") or "").strip(),
        hits_order=str(data.get("hits") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def submit_problem(request: Request, user=None):
    del user
    data = merge_payload(request)
    fields = _problem_fields(data)
    if not fields["problem_description"]:
        return Response(ajax_fail("保存失败,没有数据，请确认!"))
    faq_repo.insert_problem(**fields)
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def edit_problem(request: Request, user=None):
    del user
    data = merge_payload(request)
    problem_id = data.get("id")
    if not problem_id:
        return Response(ajax_fail("数据错误"))
    fields = _problem_fields(data)
    faq_repo.update_problem(problem_id=int(problem_id), **fields)
    return Response(ajax_ok(res_msg="修改成功！"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def delete_problem(request: Request, user=None):
    del user
    data = merge_payload(request)
    problem_id = data.get("id")
    if not problem_id:
        return Response(ajax_fail("数据错误"))
    affected = faq_repo.delete_problem(int(problem_id))
    if affected > 0:
        return Response(ajax_ok(res_msg="删除成功！"))
    return Response(ajax_fail("删除失败"))
