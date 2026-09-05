"""青岛会员账号（userType=5）接口层。"""

from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_member.repositories import member_account as account_repo
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


def _parse_is_app_login(data: dict) -> bool:
    """对齐 Java：checkbox name=userRole，值为 on 时 is_app_login=true。"""
    raw = data.get("is_app_login")
    if raw is None:
        raw = data.get("isAppLogin")
    if raw is None:
        raw = data.get("userRole")
    if raw is None:
        raw = data.get("operable")
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in ("on", "true", "1", "yes"):
            return True
        if lowered in ("off", "false", "0", "no", ""):
            return False
    return bool(raw) and raw not in (0, "0", False)


def _company_id(data: dict, *keys: str):
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            value = value.get("id")
        if value not in (None, ""):
            return value
    return None


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = account_repo.list_accounts(
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        company_name=(data.get("company_name") or data.get("companyName") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        mobile=(data.get("mobile") or data.get("telephone") or "").strip(),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = _to_int(data.get("id"))
    if not account_id:
        return Response(ajax_fail("参数错误"))
    row = account_repo.get_account(account_id)
    if not row:
        return Response(ajax_fail("账号不存在"))
    row.pop("password", None)
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_save(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = _to_int(data.get("id"))
    user_name = (data.get("userName") or data.get("user_name") or "").strip()
    company_id = _company_id(data, "company_name", "companyId", "company_id")
    cg_company_id = _company_id(data, "cg_company_name", "cgCompanyId", "cg_company_id")
    mobile = (data.get("mobile") or data.get("telephone") or "").strip()
    true_name = (data.get("trueName") or data.get("true_name") or "").strip()
    password = (data.get("password") or "").strip()
    photo_id = _to_int(data.get("photo_id") or data.get("photoId"))
    is_app_login = _parse_is_app_login(data)

    if not account_id and not user_name:
        return Response(ajax_fail("请填写用户名"))
    if not mobile:
        return Response(ajax_fail("请填写手机号"))
    # Java 允许销售企业为空；保存时仍建议有销售企业便于列表 INNER JOIN 可见
    if not company_id:
        return Response(ajax_fail("请选择(销售)企业名称"))

    payload = {
        "trueName": true_name or user_name,
        "mobile": mobile,
        "telephone": mobile,
        "email": (data.get("email") or "").strip(),
        "company_name": company_id,
        "cg_company_name": cg_company_id,
        "is_app_login": is_app_login,
    }
    if photo_id:
        payload["photo_id"] = photo_id

    if account_id:
        if user_name and account_repo.username_exists(user_name, exclude_id=account_id):
            return Response(ajax_fail("用户名已存在"))
        if user_name:
            payload["userName"] = user_name
        if password:
            payload["password"] = encrypt_password_for_storage(password)
        account_repo.update_account(account_id, payload)
        return Response(ajax_ok(obj={"id": account_id}, res_msg="更新会员成功"))

    if account_repo.username_exists(user_name):
        return Response(ajax_fail("用户名已存在"))
    if not password:
        password = "123456"
    new_id = account_repo.insert_account(
        {
            "userName": user_name,
            "password": encrypt_password_for_storage(password),
            **payload,
        }
    )
    return Response(ajax_ok(obj={"id": new_id}, res_msg="保存成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_update_status(request: Request, user=None):
    del user
    data = merge_payload(request)
    account_id = _to_int(data.get("id"))
    if not account_id:
        return Response(ajax_fail("参数错误"))
    status = data.get("status")
    account_repo.update_status(account_id, _to_int(status) if status not in (None, "") else None)
    return Response(ajax_ok(res_msg="操作成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def account_valid_username(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_name = (data.get("userName") or data.get("user_name") or "").strip()
    exclude_id = _to_int(data.get("id"))
    if not user_name:
        return Response(ajax_ok(obj=True))
    exists = account_repo.username_exists(user_name, exclude_id=exclude_id)
    return Response(ajax_ok(obj=not exists))
