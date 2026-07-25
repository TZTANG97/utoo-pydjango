from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_member.repositories import member as member_repo
from apps.admin_system.repositories import user_company as company_repo
from apps.admin_system.views.common import merge_payload
from apps.core.responses import ajax_fail, ajax_ok
from qd_common.password_java import encrypt_password_for_storage


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
def member_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = member_repo.list_members(
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        company_name=(data.get("company_name") or data.get("companyName") or "").strip(),
        mobile=(data.get("mobile") or "").strip(),
        province=str(data.get("province") or "").strip(),
        city=str(data.get("city") or "").strip(),
        area_id=str(data.get("areaId") or data.get("area_id") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def member_detail(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = _to_int(data.get("id") or data.get("userId"))
    if not user_id:
        return Response(ajax_fail("参数错误"))
    row = member_repo.get_member(user_id, display_names=True)
    if not row:
        return Response(ajax_fail("用户不存在"))
    mobile = str(row.get("mobile") or "")
    row["companyList"] = member_repo.companies_by_phone(mobile)
    return Response(ajax_ok(obj=row, res_msg="操作成功!"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def member_add(request: Request, user=None):
    del user
    data = merge_payload(request)
    true_name = (data.get("trueName") or "").strip()
    mobile = (data.get("mobile") or "").strip()
    company_name = (data.get("company_name") or data.get("companyName") or "").strip()
    if not true_name or not mobile:
        return Response(ajax_fail("请填写姓名和手机号"))
    if member_repo.mobile_exists(mobile):
        return Response(ajax_fail("手机号已存在"))
    password = (data.get("password") or "123456").strip()
    parent_id = _to_int(data.get("parent_id") or data.get("parentId") or data.get("comId"))
    # 企业联系人带 parent_id；个人会员仅保存 company_name 文本（与 Java 一致，不自动建企业）
    if parent_id and not company_name:
        company = company_repo.get_company(parent_id)
        if company:
            company_name = str(company.get("name") or "")
    user_name = (data.get("userName") or mobile).strip()
    if member_repo.username_exists(user_name):
        user_name = f"{mobile}_{true_name}"
    user_type = _to_int(data.get("userType"), 1 if not parent_id else 2) or (1 if not parent_id else 2)
    new_id = member_repo.insert_member(
        {
            "userName": user_name,
            "password": encrypt_password_for_storage(password),
            "trueName": true_name,
            "mobile": mobile,
            "email": (data.get("email") or "").strip() or None,
            "idcard": (data.get("idcard") or "").strip() or None,
            "company_name": company_name or None,
            "userType": user_type,
            "parent_id": parent_id,
            "area_id": data.get("area_id") or data.get("areaId"),
            "addreddInfo": data.get("addreddInfo") or data.get("addressInfo"),
            "is_accept_message": _to_int(data.get("is_accept_message") or data.get("isAcceptMessage"), 0) or 0,
            "dept": (data.get("dept") or "").strip() or None,
            "job": (data.get("job") or "").strip() or None,
            "telephone": (data.get("telephone") or "").strip() or None,
            "extension": (data.get("extension") or "").strip() or None,
            "zipCode": (data.get("zipCode") or data.get("zip_code") or "").strip() or None,
        }
    )
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def member_edit(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = _to_int(data.get("id"))
    if not user_id:
        return Response(ajax_fail("参数错误"))
    mobile = (data.get("mobile") or "").strip()
    if mobile and member_repo.mobile_exists(mobile, exclude_id=user_id):
        return Response(ajax_fail("手机号已存在"))
    member_repo.update_member(
        user_id,
        {
            "trueName": (data.get("trueName") or "").strip(),
            "mobile": mobile,
            "email": (data.get("email") or "").strip() or None,
            "idcard": (data.get("idcard") or "").strip() or None,
            "company_name": (data.get("company_name") or data.get("companyName") or "").strip() or None,
            "area_id": data.get("area_id") or data.get("areaId"),
            "addreddInfo": data.get("addreddInfo") or data.get("addressInfo"),
            "is_accept_message": _to_int(data.get("is_accept_message") or data.get("isAcceptMessage"), 0) or 0,
            "dept": (data.get("dept") or "").strip() or None,
            "job": (data.get("job") or "").strip() or None,
            "telephone": (data.get("telephone") or "").strip() or None,
            "extension": (data.get("extension") or "").strip() or None,
            "zipCode": (data.get("zipCode") or data.get("zip_code") or "").strip() or None,
            "parent_id": _to_int(data.get("parent_id") or data.get("parentId") or data.get("comId")),
            "userType": _to_int(data.get("userType")),
        },
    )
    return Response(ajax_ok(res_msg="修改成功"))


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def member_update_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = _to_int(data.get("id"))
    if not user_id:
        return Response(ajax_fail("参数错误"))
    member_repo.unbind_member(user_id)
    return Response(ajax_ok(res_msg="解绑成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def member_bind(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = _to_int(data.get("id") or data.get("userId"))
    parent_id = _to_int(data.get("parent_id") or data.get("parentId") or data.get("companyId"))
    if not user_id or not parent_id:
        return Response(ajax_fail("参数错误"))
    company = company_repo.get_company(parent_id)
    if not company:
        return Response(ajax_fail("公司不存在"))
    member_repo.bind_member(
        user_id=user_id,
        parent_id=parent_id,
        company_name=str(company.get("name") or ""),
    )
    return Response(ajax_ok(res_msg="绑定成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def valid_mobile(request: Request, user=None):
    del user
    data = merge_payload(request)
    mobile = (data.get("mobile") or "").strip()
    exclude_id = _to_int(data.get("id"))
    if not mobile:
        return Response(ajax_fail("请填写手机号"))
    exists = member_repo.mobile_exists(mobile, exclude_id=exclude_id)
    return Response(ajax_ok(obj={"valid": not exists}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=False)
def load_customer_names(request: Request, user=None):
    """小程序客户名称下拉 — /member/loadCustomerNames.ajax（type=1 企业）。"""
    del user, request
    from apps.core.db_utils import fetch_all

    rows = fetch_all(
        """
        SELECT id, name
        FROM qd_user_company
        WHERE delete_status = 0 AND type = 1
        ORDER BY id DESC
        LIMIT 5000
        """
    )
    return Response(ajax_ok(obj=rows or [], res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=False)
def query_all_company_kh(request: Request, user=None):
    """小程序客户账号下拉 — /member/queryAllCompanykh.ajax（返回 id/mobile）。"""
    del user
    data = merge_payload(request)
    parent_id = str(
        data.get("parentId") or data.get("parent_id") or data.get("comId") or ""
    ).strip()
    from apps.core.db_utils import fetch_all

    if parent_id.isdigit():
        rows = fetch_all(
            """
            SELECT id, mobile
            FROM exp_user
            WHERE IFNULL(deleteStatus, 0) = 0
              AND parent_id = %(pid)s
              AND IFNULL(mobile, '') <> ''
            ORDER BY id DESC
            LIMIT 5000
            """,
            {"pid": int(parent_id)},
        )
    else:
        rows = fetch_all(
            """
            SELECT id, mobile
            FROM exp_user
            WHERE IFNULL(deleteStatus, 0) = 0
              AND IFNULL(mobile, '') <> ''
            ORDER BY id DESC
            LIMIT 5000
            """
        )
    return Response(ajax_ok(obj=rows or [], res_msg="获取成功!"))
