from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import supplier as supplier_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok


def _supplier_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "userName": (data.get("userName") or data.get("user_name") or "").strip(),
        "company_name": (data.get("companyName") or data.get("company_name") or "").strip(),
        "trueName": (data.get("trueName") or data.get("true_name") or "").strip(),
        "mobile": (data.get("mobile") or "").strip(),
        "address": data.get("address"),
        "area_info": data.get("areaInfo") or data.get("area_info"),
        "company_code": (data.get("companyCode") or data.get("company_code") or "").strip(),
        "company_coord": (data.get("companyCoord") or data.get("company_coord") or "").strip(),
        "syuser_id": str(data.get("syuserId") or data.get("syuser_id") or "").strip(),
        "email": data.get("email"),
        "area_id": data.get("areaId") or data.get("area_id"),
        "city": data.get("city"),
        "province": data.get("province"),
        "address_info": data.get("addressInfo") or data.get("addreddInfo"),
        "password": data.get("password"),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def supplier_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = supplier_repo.list_suppliers(
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        company_name=(data.get("company_name") or data.get("companyName") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        mobile=(data.get("mobile") or "").strip(),
        area_id=str(data.get("areaId") or data.get("area_id") or ""),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def supplier_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    supplier_id = data.get("id")
    if not supplier_id:
        return Response(ajax_fail("数据错误"))
    row = supplier_repo.get_supplier(int(supplier_id))
    if not row:
        return Response(ajax_fail("所属公司不存在"))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def supplier_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    payload = _supplier_payload(data)
    supplier_id = payload.get("id")
    if not payload["userName"] or not payload["company_name"]:
        return Response(ajax_fail("用户名和企业名称不能为空"))
    if not payload["trueName"] or not payload["mobile"]:
        return Response(ajax_fail("联系人和联系电话不能为空"))
    if not payload.get("area_info"):
        return Response(ajax_fail("请选择区域"))
    if not payload.get("city"):
        return Response(ajax_fail("请选择市"))
    if not payload.get("address"):
        return Response(ajax_fail("请选择县（区）"))
    if not payload.get("company_code"):
        return Response(ajax_fail("请填写公司代码"))
    if not payload.get("company_coord"):
        return Response(ajax_fail("请填写公司坐标"))
    if not payload.get("syuser_id"):
        return Response(ajax_fail("请选择关联账号"))
    if supplier_id:
        if supplier_repo.find_by_user_name(payload["userName"], exclude_id=int(supplier_id)):
            return Response(ajax_fail("用户名已存在"))
        if supplier_repo.find_by_company_name(payload["company_name"], exclude_id=int(supplier_id)):
            return Response(ajax_fail("企业名称已存在"))
        supplier_repo.update_supplier(int(supplier_id), payload)
        return Response(ajax_ok(res_msg="保存成功"))
    if supplier_repo.find_by_user_name(payload["userName"]):
        return Response(ajax_fail("用户名已存在"))
    if supplier_repo.find_by_company_name(payload["company_name"]):
        return Response(ajax_fail("企业名称已存在"))
    new_id = supplier_repo.insert_supplier(payload)
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def supplier_delete(request: Request, user=None):
    del user
    data = merge_payload(request)
    supplier_id = data.get("id")
    if not supplier_id:
        return Response(ajax_fail("数据错误"))
    supplier_repo.toggle_supplier_status(int(supplier_id))
    return Response(ajax_ok(res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=False)
def supplier_query_all(_request: Request, user=None):
    del user
    rows, _ = supplier_repo.list_suppliers(page=1, page_size=5000)
    return ajax_response(True, obj=rows)
