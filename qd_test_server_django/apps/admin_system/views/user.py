from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.admin_core.datatable import datatable_payload, parse_datatable_params
from apps.admin_system.repositories import user as user_repo
from apps.admin_system.repositories import user_access as access_repo
from apps.admin_system.views.common import merge_payload, split_ids
from apps.core.responses import ajax_fail, ajax_ok


def _to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _actor_id(request: Request, user) -> str:
    if isinstance(user, dict):
        return str(user.get("id") or user.get("userId") or "")
    data = merge_payload(request)
    return str(data.get("operatorId") or data.get("logUserId") or "")


def _user_payload(data: dict) -> dict:
    return {
        "id": data.get("id"),
        "user_name": (data.get("userName") or data.get("user_name") or "").strip(),
        "true_name": (data.get("trueName") or data.get("true_name") or "").strip(),
        "user_password": data.get("userPassword") or data.get("user_password"),
        "user_status": _to_int(data.get("userStatus") or data.get("user_status"), 1) or 1,
        "dept_id": data.get("deptId") or data.get("dept_id") or "0",
        "mobile_phone_number": data.get("mobilePhoneNumber") or data.get("mobile_phone_number"),
        "email": data.get("email"),
        "type": data.get("type") or "0",
        "show_type": data.get("showType") or data.get("show_type"),
        "user_type_role_id": data.get("userTypeRoleId") or data.get("user_type_role_id"),
        "user_desc": data.get("userDesc") or data.get("user_desc"),
        "user_sex": _to_int(data.get("userSex") if data.get("userSex") is not None else data.get("user_sex"), 1),
        "qq_number": data.get("qqNumber") or data.get("qq_number"),
        "utoo_type": data.get("utooType") or data.get("utoo_type"),
        "linked_user_id": data.get("userId") or data.get("user_id") or data.get("linkedUserId"),
        "is_czqx": _to_int(data.get("isCzqx") if data.get("isCzqx") is not None else data.get("is_czqx"), 0),
        "helper_id": data.get("helperId") or data.get("helper_id") or None,
        "account_type": _to_int(
            data.get("accountType") if data.get("accountType") is not None else data.get("account_type"),
            0,
        ),
        "is_email": _to_int(data.get("isEmail") if data.get("isEmail") is not None else data.get("is_email"), 1),
        "is_rate": _to_int(data.get("isRate") if data.get("isRate") is not None else data.get("is_rate"), 1),
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_list(request: Request, user=None):
    del user
    user_repo.backfill_null_register_times()
    data = merge_payload(request)
    draw, page, page_size = parse_datatable_params(request)
    rows, total = user_repo.list_users(
        dept_id=str(data.get("deptId") or data.get("dept_id") or ""),
        user_name=(data.get("userName") or data.get("user_name") or "").strip(),
        true_name=(data.get("trueName") or data.get("true_name") or "").strip(),
        user_sex=str(data.get("userSex") if data.get("userSex") is not None else data.get("user_sex") or ""),
        role_type=str(data.get("type") if data.get("type") is not None else ""),
        page=page,
        page_size=page_size,
    )
    return Response(datatable_payload(draw=draw, total=total, rows=rows))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=False)
def user_list_except(request: Request, user=None):
    """小程序分成人选 — sys/user/queryUsersExcept.ajax → {res,obj:[...]}。"""
    del user
    data = merge_payload(request)
    except_id = str(data.get("exceptUserId") or data.get("except_user_id") or "").strip()
    rows, _total = user_repo.list_users(page=1, page_size=2000)
    obj = []
    for row in rows:
        uid = str(row.get("id") or "")
        if except_id and uid == except_id:
            continue
        if int(row.get("userStatus") or 0) != 1:
            continue
        obj.append(
            {
                "id": row.get("id"),
                "userId": row.get("id"),
                "userName": row.get("userName") or "",
                "trueName": row.get("trueName") or "",
                "true_name": row.get("trueName") or "",
            }
        )
    return Response(ajax_ok(obj=obj, res_msg="获取成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_get(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = data.get("id")
    if not user_id:
        return Response(ajax_fail("数据错误"))
    row = user_repo.get_user(str(user_id))
    return Response(ajax_ok(obj=row))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_add(request: Request, user=None):
    data = merge_payload(request)
    payload = _user_payload(data)
    if not payload["user_name"]:
        return Response(False)
    if user_repo.find_by_login_name(payload["user_name"]):
        return Response(False)
    actor = _actor_id(request, user)
    payload["register_uid"] = actor or None
    user_id = user_repo.insert_user(payload)
    role_ids = split_ids(data.get("roleIds") or data.get("role_ids"))
    if role_ids:
        user_repo.set_user_roles(user_id, role_ids)
    # 再扫一遍，避免历史脏数据导致旧平台 Date.format(null) 整页 500
    user_repo.backfill_null_register_times()
    user_repo.insert_user_log(user_id=user_id, log_user_id=actor or user_id, log_info="新增用户")
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_update(request: Request, user=None):
    data = merge_payload(request)
    payload = _user_payload(data)
    if not payload["id"] or not payload["user_name"]:
        return Response(False)
    old = user_repo.get_user(str(payload["id"]))
    user_repo.update_user(payload)
    if "roleIds" in data or "role_ids" in data:
        user_repo.set_user_roles(
            str(payload["id"]),
            split_ids(data.get("roleIds") or data.get("role_ids")),
        )
    actor = _actor_id(request, user)
    changes = []
    if old:
        mapping = [
            ("trueName", "true_name", "姓名"),
            ("deptId", "dept_id", "部门"),
            ("utooType", "utoo_type", "用户类型"),
            ("mobilePhoneNumber", "mobile_phone_number", "手机号"),
            ("email", "email", "邮箱"),
            ("accountType", "account_type", "企业用户"),
            ("isCzqx", "is_czqx", "操作权限"),
            ("helperId", "helper_id", "协助者"),
        ]
        for old_key, new_key, label in mapping:
            before = old.get(old_key)
            after = payload.get(new_key)
            if str(before or "") != str(after or ""):
                changes.append(f"{label}:{before}->{after}")
    user_repo.insert_user_log(
        user_id=str(payload["id"]),
        log_user_id=actor or str(payload["id"]),
        log_info=("修改用户：" + "；".join(changes)) if changes else "修改用户信息",
    )
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_disable(request: Request, user=None):
    data = merge_payload(request)
    user_id = data.get("id")
    if not user_id:
        return Response(False)
    status = _to_int(data.get("status") if data.get("status") is not None else data.get("userStatus"), 0)
    if status is None:
        status = 0
    user_repo.set_user_status(str(user_id), status)
    actor = _actor_id(request, user)
    user_repo.insert_user_log(
        user_id=str(user_id),
        log_user_id=actor or str(user_id),
        log_info="启用用户" if status == 1 else "禁用用户",
    )
    return Response(True)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_update_password(request: Request, user=None):
    data = merge_payload(request)
    user_id = str(data.get("id") or "").strip()
    pwd = str(data.get("userPassword") or data.get("user_password") or "").strip()
    pwd2 = str(data.get("pwd") or data.get("confirmPassword") or pwd).strip()
    if not user_id or not pwd:
        return Response(ajax_fail("参数错误"))
    if len(pwd) < 6:
        return Response(ajax_fail("密码长度至少6位"))
    if pwd != pwd2:
        return Response(ajax_fail("两次输入的新密码不一致"))
    user_repo.update_password(user_id, pwd)
    actor = _actor_id(request, user)
    user_repo.insert_user_log(user_id=user_id, log_user_id=actor or user_id, log_info="重置密码")
    return Response(ajax_ok(res_msg="密码已重置"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_update_roles(request: Request, user=None):
    data = merge_payload(request)
    user_id = str(data.get("id") or data.get("userId") or data.get("user_id") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    role_ids = split_ids(data.get("roleIds") or data.get("role_ids") or data.get("addRoleIds"))
    user_repo.set_user_roles(user_id, role_ids)
    actor = _actor_id(request, user)
    user_repo.insert_user_log(user_id=user_id, log_user_id=actor or user_id, log_info="修改权限(角色)")
    return Response(ajax_ok(res_msg="权限已更新"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_show_powers(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("id") or data.get("userId") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    roles = [{"id": rid} for rid in user_repo.get_user_role_ids(user_id)]
    menus = user_repo.list_user_powers(user_id)
    return Response(ajax_ok(obj={"roleIds": [r["id"] for r in roles], "menus": menus}))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_logs(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("id") or data.get("userId") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    return Response(ajax_ok(obj=user_repo.list_user_logs(user_id)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_form_options(_request: Request, user=None):
    del user
    return Response(
        ajax_ok(
            obj={
                "roles": user_repo.list_role_options(),
                "utooTypes": user_repo.list_utoo_type_options(),
                "helpers": user_repo.list_helper_options(),
                "members": user_repo.list_member_options(),
            }
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_role_options(_request: Request, user=None):
    del user
    return ajax_response(True, obj=user_repo.list_role_options())


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_access_rights_query(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("id") or data.get("userId") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    return Response(ajax_ok(obj=access_repo.get_access_rights(user_id)))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_access_rights_update(request: Request, user=None):
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("user_id") or data.get("id") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    if "companyIds" in data or "hasCompanys" in data:
        company_ids = split_ids(data.get("companyIds") if "companyIds" in data else data.get("hasCompanys"))
    elif "addCompanyIds" in data or "delCompanyIds" in data:
        current = set(access_repo.find_company_ids(user_id))
        current |= set(split_ids(data.get("addCompanyIds")))
        current -= set(split_ids(data.get("delCompanyIds")))
        company_ids = list(current)
    else:
        company_ids = access_repo.find_company_ids(user_id)

    if "orderTypeIds" in data or "hasTypes" in data:
        order_type_ids = split_ids(data.get("orderTypeIds") if "orderTypeIds" in data else data.get("hasTypes"))
    elif "addOrderTypeIds" in data or "delOrderTypeIds" in data:
        current = set(access_repo.find_order_type_ids(user_id))
        current |= set(split_ids(data.get("addOrderTypeIds")))
        current -= set(split_ids(data.get("delOrderTypeIds")))
        order_type_ids = list(current)
    else:
        order_type_ids = access_repo.find_order_type_ids(user_id)
    sale_user_ids = split_ids(
        data.get("saleUserIds")
        or data.get("other_user_id")
        or data.get("userInfo")
    )
    access_repo.update_access_rights(
        user_id,
        company_ids=company_ids,
        order_type_ids=order_type_ids,
        sale_user_ids=sale_user_ids,
    )
    actor = _actor_id(request, user)
    user_repo.insert_user_log(
        user_id=user_id,
        log_user_id=actor or user_id,
        log_info="修改订单访问权限",
    )
    return Response(ajax_ok(res_msg="保存成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_access_sale_options(_request: Request, user=None):
    del user
    return Response(ajax_ok(obj=access_repo.list_access_sale_users()))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_exp_manage_available(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("id") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    return Response(ajax_ok(obj=access_repo.list_available_exp_projects(user_id)))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_exp_manage_list(request: Request, user=None):
    del user
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("id") or "").strip()
    if not user_id:
        return Response(ajax_fail("参数错误"))
    return Response(ajax_ok(obj=access_repo.list_user_exp_projects(user_id)))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_exp_manage_add(request: Request, user=None):
    data = merge_payload(request)
    user_id = str(data.get("userId") or data.get("user_id") or data.get("id") or "").strip()
    exp_manage_id = data.get("exp_manage_id") or data.get("expManageId")
    if not user_id or exp_manage_id in (None, ""):
        return Response(ajax_fail("参数错误"))
    obj = access_repo.add_user_exp_manage(user_id, exp_manage_id)
    actor = _actor_id(request, user)
    user_repo.insert_user_log(
        user_id=user_id,
        log_user_id=actor or user_id,
        log_info=f"添加管理测试项目:{exp_manage_id}",
    )
    return Response(ajax_ok(obj=obj, res_msg="添加成功"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view()
def user_exp_manage_delete(request: Request, user=None):
    data = merge_payload(request)
    row_id = data.get("id")
    if row_id in (None, ""):
        return Response(ajax_fail("参数错误"))
    access_repo.delete_user_exp_manage(row_id)
    return Response(ajax_ok(res_msg="已删除"))
