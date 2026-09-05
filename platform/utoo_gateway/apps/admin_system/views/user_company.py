from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import user_company as company_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _company_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "name": (data.get("name") or "").strip(),
        "enName": data.get("enName") or data.get("en_name"),
        "country": data.get("country"),
        "areaId": data.get("areaId") or data.get("area_id"),
        "taxNum": data.get("taxNum") or data.get("tax_num"),
        "bank": data.get("bank"),
        "bankCardNum": data.get("bankCardNum") or data.get("bank_card_num"),
        "address": data.get("address"),
        "contractPhone": data.get("contractPhone") or data.get("contract_phone"),
        "contractPeople": data.get("contractPeople") or data.get("contract_people"),
        "depts": data.get("depts"),
        "companyProp": data.get("companyProp") or data.get("company_prop"),
        "type": int(data.get("type") or 3),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = company_repo.list_companies(
        name=(data.get("name") or "").strip(),
        contract_people=(data.get("contractPeople") or data.get("contract_people") or "").strip(),
        contract_phone=(data.get("contractPhone") or data.get("contract_phone") or "").strip(),
        company_prop=str(data.get("company_prop") or data.get("companyProp") or "").strip(),
        country=(data.get("country") or "").strip(),
        province=str(data.get("province") or "").strip(),
        city=str(data.get("city") or "").strip(),
        area_id=str(data.get("areaId") or data.get("area_id") or "").strip(),
        company_type=data.get("type"),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    company_id = data.get("id")
    if not company_id:
        return Response(ajax_fail("参数错误"))
    row = company_repo.get_company(int(company_id), display_names=False)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_get_by_com_id(request: Request, user=None):
    """Java getCompanyByComId.ajax：基本信息 Tab，地区字段为名称。"""
    del user
    data = merge_payload(request)
    company_id = data.get("id")
    if not company_id:
        return Response(ajax_fail("参数错误"))
    row = company_repo.get_company(int(company_id), display_names=True)
    if not row:
        return Response(ajax_fail("数据不存在"))
    return Response(ajax_ok(obj=row, res_msg="操作成功!"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _company_payload(data)
    if not payload["name"]:
        return Response(ajax_fail("请填写公司名称"))
    company_id = data.get("id")
    apply_id = data.get("applyuserId") or data.get("applyid")
    if company_id:
        if company_repo.name_exists(payload["name"], exclude_id=int(company_id)):
            return Response(ajax_fail("公司名称已存在"))
        company_repo.update_company(payload)
        return Response(ajax_ok(res_msg="修改成功"))
    if company_repo.name_exists(payload["name"]):
        return Response(ajax_fail("公司名称已存在"))
    new_id = company_repo.insert_company(payload)
    if apply_id:
        from apps.admin_member.repositories import apply_vip as apply_repo

        apply_repo.set_state(int(apply_id), state=1, operator_id=None)
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_update(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _company_payload(data)
    if not payload.get("id"):
        return Response(ajax_fail("参数错误"))
    if not payload["name"]:
        return Response(ajax_fail("请填写公司名称"))
    if company_repo.name_exists(payload["name"], exclude_id=int(payload["id"])):
        return Response(ajax_fail("公司名称已存在"))
    company_repo.update_company(payload)
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    company_id = data.get("id")
    if not company_id:
        return Response(ajax_fail("参数错误"))
    company_repo.soft_delete_company(int(company_id))
    return Response(ajax_ok(res_msg="删除成功"))


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_update_status(request: Request, user=None):
    """Java updateStatus.ajax：status=1 开启，status=2 禁用。"""
    del user
    data = merge_payload(request)
    company_id = data.get("id")
    status = str(data.get("status") or "").strip()
    if not company_id or status not in {"1", "2"}:
        return Response(ajax_fail("参数错误"))
    cid = int(company_id)
    company_repo.set_company_status(cid, enabled=(status == "1"))
    return Response(ajax_ok(res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def company_valid_name(request: Request, user=None):
    del user
    data = merge_payload(request)
    name = (data.get("name") or "").strip()
    exclude_id = data.get("id")
    if not name:
        return Response(ajax_fail("请填写名称"))
    exists = company_repo.name_exists(name, exclude_id=int(exclude_id) if exclude_id else None)
    return Response(ajax_ok(obj={"valid": not exists}))
