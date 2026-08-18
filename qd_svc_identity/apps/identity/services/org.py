import hashlib
import hmac
import uuid

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.identity.models import (
    Department,
    Menu,
    Role,
    RoleAction,
    RoleMenu,
    SystemUser,
    UserCompanyLink,
    UserOrderTypeLink,
    UserRole,
    UserSalesLink,
)
from apps.identity.repositories import access as access_repo
from apps.identity.repositories import departments as departments_repo
from apps.identity.repositories import menus as menus_repo
from apps.identity.repositories import roles as roles_repo
from apps.identity.repositories import scope as scope_repo
from apps.identity.repositories import users as users_repo
from apps.identity.services.menus import normalize_menu_write, serialize_sy_menu_map

LEGACY_HEX_DIGITS = "A1B3C5D7E9F0G2H4"
USER_WRITE_FIELDS = {
    "user_name",
    "true_name",
    "dept_id",
    "mobile_phone_number",
    "email",
    "type",
    "user_status",
    "pt_type",
}
ROLE_WRITE_FIELDS = {"role_name", "role_desc", "type"}
MENU_WRITE_FIELDS = {
    "menu_super_id",
    "menu_status",
    "menu_sort",
    "menu_name",
    "menu_icon",
    "menu_url",
    "menu_target",
    "menu_rel",
    "menu_open",
    "menu_external",
    "menu_fresh",
}
DEPT_WRITE_FIELDS = {
    "dept_sort",
    "dept_name",
    "dept_phone",
    "dept_fax",
    "dept_address",
    "super_id",
    "lead_uid",
    "dept_desc",
}


def new_id():
    return uuid.uuid4().hex


def legacy_md5(password: str) -> str:
    encoding = getattr(settings, "LEGACY_PASSWORD_ENCODING", "utf-8")
    digest = hashlib.md5(password.encode(encoding)).digest()
    return "".join(LEGACY_HEX_DIGITS[byte >> 4] + LEGACY_HEX_DIGITS[byte & 0x0F] for byte in digest)


def validate_legacy_password(password, stored_hash):
    return bool(stored_hash) and hmac.compare_digest(legacy_md5(password), stored_hash)


def require_write_enabled():
    if not getattr(settings, "IDENTITY_WRITE_ENABLED", True):
        raise PermissionDenied("组织写入尚未启用")


def require_legacy_permission(claims, *legacy_urls):
    scope = claims.get("scope") or {}
    if scope.get("filter_list") == 2:
        return
    permissions = {str(url).lstrip("/") for url in claims.get("permissions") or []}
    if not any(str(url).lstrip("/") in permissions for url in legacy_urls):
        raise PermissionDenied("当前用户没有该操作权限")


def as_payload(value):
    if not isinstance(value, dict):
        raise ValidationError("请求体必须是 JSON 对象")
    return value


def reject_unknown_fields(data, allowed_fields):
    unknown = sorted(set(data) - set(allowed_fields))
    if unknown:
        raise ValidationError({"detail": f"不支持写入字段：{', '.join(unknown)}"})


def required_text(data, name, *, max_length):
    value = data.get(name)
    if not isinstance(value, str):
        raise ValidationError({name: "为必填字符串"})
    text = value.strip()
    if not text:
        raise ValidationError({name: "不能为空"})
    if len(text) > max_length:
        raise ValidationError({name: f"不能超过 {max_length} 个字符"})
    return text


def optional_text(data, name, *, max_length):
    if name not in data or data[name] in (None, ""):
        return None
    if not isinstance(data[name], str):
        raise ValidationError({name: "必须是字符串"})
    text = data[name].strip()
    if len(text) > max_length:
        raise ValidationError({name: f"不能超过 {max_length} 个字符"})
    return text


def optional_int(data, name):
    if name not in data or data[name] in (None, ""):
        return None
    try:
        return int(data[name])
    except (TypeError, ValueError) as error:
        raise ValidationError({name: "必须是整数"}) from error


def is_placeholder_id(value):
    return str(value or "") in {"", "0"}


def user_matches_platform(user, pt_type: str) -> bool:
    return pt_type in (user.pt_type or "")


def id_list(value, name):
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValidationError({name: "必须是字符串 ID 数组"})
    return [item.strip() for item in value]


def mixed_id_list(value, name):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError({name: "必须是 ID 数组"})
    result = []
    for item in value:
        if isinstance(item, bool) or item in (None, ""):
            raise ValidationError({name: "必须是 ID 数组"})
        if isinstance(item, int):
            result.append(item)
            continue
        if isinstance(item, str) and item.strip():
            text = item.strip()
            result.append(int(text) if text.isdigit() else text)
            continue
        raise ValidationError({name: "必须是 ID 数组"})
    return result


def serialize_user(user, *, role_ids=None):
    payload = {
        "id": user.id,
        "user_name": user.user_name,
        "true_name": user.true_name,
        "user_status": user.user_status,
        "dept_id": user.dept_id,
        "mobile_phone_number": user.mobile_phone_number,
        "email": user.email,
        "type": user.type,
        "pt_type": user.pt_type,
    }
    if role_ids is not None:
        payload["role_ids"] = role_ids
    return payload


def serialize_role(role, *, menu_ids=None, action_ids=None):
    payload = {
        "id": role.id,
        "role_name": role.role_name,
        "role_desc": role.role_desc,
        "type": role.type,
    }
    if menu_ids is not None:
        payload["menu_ids"] = menu_ids
    if action_ids is not None:
        payload["action_ids"] = action_ids
    return payload


def serialize_department(dept):
    return {
        "id": dept.id,
        "dept_sort": dept.dept_sort,
        "dept_name": dept.dept_name,
        "dept_phone": dept.dept_phone,
        "dept_fax": dept.dept_fax,
        "dept_address": dept.dept_address,
        "super_id": dept.super_id,
        "lead_uid": dept.lead_uid,
        "dept_desc": dept.dept_desc,
    }


def get_user(user_id, *, pt_type=None):
    user = users_repo.get_by_id(user_id)
    if not user:
        raise NotFound("用户不存在")
    if pt_type and not user_matches_platform(user, pt_type):
        raise NotFound("用户不存在")
    return user


def user_role_ids(user_id, *, role_type=None):
    return users_repo.list_role_ids(user_id, role_type=role_type)


def list_admin_users(*, keyword="", include_disabled=False, pt_type="1"):
    return [
        serialize_user(user)
        for user in users_repo.list_admin(keyword=keyword, include_disabled=include_disabled, pt_type=pt_type)
    ]


def _assert_unique_username(user_name, *, exclude_id=None):
    if users_repo.username_exists(user_name, exclude_id=exclude_id):
        raise ValidationError({"user_name": "用户名已存在"})


def _assert_roles_exist(role_ids, role_type: int):
    if not role_ids:
        return
    found = roles_repo.find_existing_ids(role_ids, role_type)
    missing = sorted(set(role_ids) - found)
    if missing:
        raise ValidationError({"role_ids": f"角色不存在：{', '.join(missing)}"})


def replace_user_roles(user_id, role_ids, *, role_type: int):
    _assert_roles_exist(role_ids, role_type)
    users_repo.delete_user_roles(user_id, role_type=role_type)
    users_repo.bulk_create_user_roles(
        [UserRole(id=new_id(), user_id=user_id, role_id=role_id) for role_id in role_ids]
    )
    return user_role_ids(user_id, role_type=role_type)


def create_user(raw_data, *, pt_type: str, role_type: int):
    data = as_payload(raw_data)
    reject_unknown_fields(data, USER_WRITE_FIELDS | {"password", "role_ids"})
    user_name = required_text(data, "user_name", max_length=64)
    password = data.get("password")
    if not isinstance(password, str) or not password:
        raise ValidationError({"password": "为必填字符串"})
    _assert_unique_username(user_name)
    role_ids = id_list(data.get("role_ids"), "role_ids")
    user = SystemUser(
        id=new_id(),
        user_name=user_name,
        user_password=legacy_md5(password),
        true_name=optional_text(data, "true_name", max_length=64),
        user_status=optional_int(data, "user_status") if "user_status" in data else 1,
        dept_id=optional_text(data, "dept_id", max_length=64),
        mobile_phone_number=optional_text(data, "mobile_phone_number", max_length=32),
        email=optional_text(data, "email", max_length=255),
        type=optional_text(data, "type", max_length=32),
        pt_type=pt_type,
        error_count=0,
        last_login_ip="x.x.x.x",
    )
    with transaction.atomic():
        users_repo.save_user(user)
        assigned = replace_user_roles(user.id, role_ids, role_type=role_type) if role_ids else []
    return serialize_user(user, role_ids=assigned)


def update_user(user_id, raw_data, *, pt_type=None, role_type=None):
    data = as_payload(raw_data)
    reject_unknown_fields(data, USER_WRITE_FIELDS)
    user = get_user(user_id, pt_type=pt_type)
    if "user_name" in data:
        user_name = required_text(data, "user_name", max_length=64)
        _assert_unique_username(user_name, exclude_id=user_id)
        user.user_name = user_name
    if "true_name" in data:
        user.true_name = optional_text(data, "true_name", max_length=64)
    if "dept_id" in data:
        user.dept_id = optional_text(data, "dept_id", max_length=64)
    if "mobile_phone_number" in data:
        user.mobile_phone_number = optional_text(data, "mobile_phone_number", max_length=32)
    if "email" in data:
        user.email = optional_text(data, "email", max_length=255)
    if "type" in data:
        user.type = optional_text(data, "type", max_length=32)
    if "pt_type" in data:
        user.pt_type = optional_text(data, "pt_type", max_length=32)
    if "user_status" in data:
        status_value = optional_int(data, "user_status")
        if status_value not in (0, 1):
            raise ValidationError({"user_status": "只能是 0 或 1"})
        user.user_status = status_value
    users_repo.save_user(user)
    return serialize_user(user, role_ids=user_role_ids(user.id, role_type=role_type))


def set_user_status(user_id, user_status, *, actor_id, pt_type=None, role_type=None):
    if user_id == actor_id and user_status == 0:
        raise ValidationError({"detail": "不能停用当前登录账号"})
    if user_status not in (0, 1):
        raise ValidationError({"user_status": "只能是 0 或 1"})
    user = get_user(user_id, pt_type=pt_type)
    user.user_status = user_status
    users_repo.save_user(user, update_fields=["user_status"])
    return serialize_user(user, role_ids=user_role_ids(user.id, role_type=role_type))


def reset_user_password(user_id, raw_data, *, pt_type=None):
    data = as_payload(raw_data)
    reject_unknown_fields(data, {"password"})
    password = data.get("password")
    if not isinstance(password, str) or not password:
        raise ValidationError({"password": "为必填字符串"})
    user = get_user(user_id, pt_type=pt_type)
    user.user_password = legacy_md5(password)
    user.error_count = 0
    users_repo.save_user(user, update_fields=["user_password", "error_count"])
    return serialize_user(user)


def change_my_password(user_id, raw_data):
    data = as_payload(raw_data)
    reject_unknown_fields(data, {"old_password", "new_password"})
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not isinstance(old_password, str) or not old_password:
        raise ValidationError({"old_password": "为必填字符串"})
    if not isinstance(new_password, str) or not new_password:
        raise ValidationError({"new_password": "为必填字符串"})
    user = get_user(user_id)
    if not validate_legacy_password(old_password, user.user_password):
        raise ValidationError({"old_password": "原密码不正确"})
    user.user_password = legacy_md5(new_password)
    user.error_count = 0
    users_repo.save_user(user, update_fields=["user_password", "error_count"])
    return {"id": user.id}


def get_data_scope(user_id, *, pt_type: str):
    user = get_user(user_id, pt_type=pt_type)
    return scope_repo.build_data_scope(user.id, user.type, pt_type)


def get_role(role_id, *, role_type: int):
    role = roles_repo.get_platform_by_id(role_id, role_type)
    if not role:
        raise NotFound("角色不存在")
    return role


def list_roles(*, keyword="", role_type: int = 1):
    return roles_repo.list_platform(keyword=keyword, role_type=role_type)


def role_menu_ids(role_id, *, pt_type=None):
    return roles_repo.list_menu_ids(role_id, pt_type=pt_type)


def role_action_ids(role_id):
    return roles_repo.list_action_ids(role_id)


def create_role(raw_data, *, role_type: int):
    data = as_payload(raw_data)
    reject_unknown_fields(data, ROLE_WRITE_FIELDS | {"menu_ids", "action_ids"})
    role_name = required_text(data, "role_name", max_length=64)
    if roles_repo.role_name_exists(role_name, role_type=role_type):
        raise ValidationError({"role_name": "角色名称已存在"})
    role = Role(
        id=new_id(),
        role_name=role_name,
        role_desc=optional_text(data, "role_desc", max_length=255),
        type=role_type,
    )
    with transaction.atomic():
        roles_repo.save_role(role)
        menus = (
            replace_role_menus(
                role.id, id_list(data.get("menu_ids"), "menu_ids"), role_type=role_type, pt_type=str(role_type)
            )
            if "menu_ids" in data
            else []
        )
        actions = (
            replace_role_actions(role.id, id_list(data.get("action_ids"), "action_ids"), role_type=role_type)
            if "action_ids" in data
            else []
        )
    return serialize_role(role, menu_ids=menus, action_ids=actions)


def update_role(role_id, raw_data, *, role_type: int):
    data = as_payload(raw_data)
    reject_unknown_fields(data, ROLE_WRITE_FIELDS)
    role = get_role(role_id, role_type=role_type)
    if "role_name" in data:
        role_name = required_text(data, "role_name", max_length=64)
        if roles_repo.role_name_exists(role_name, exclude_id=role_id, role_type=role_type):
            raise ValidationError({"role_name": "角色名称已存在"})
        role.role_name = role_name
    if "role_desc" in data:
        role.role_desc = optional_text(data, "role_desc", max_length=255)
    role.type = role_type
    roles_repo.save_role(role)
    return serialize_role(
        role, menu_ids=role_menu_ids(role.id, pt_type=str(role_type)), action_ids=role_action_ids(role.id)
    )


def delete_role(role_id, *, role_type: int):
    role = get_role(role_id, role_type=role_type)
    if roles_repo.role_has_users(role_id):
        raise ValidationError({"detail": "角色仍分配给用户，无法删除"})
    with transaction.atomic():
        roles_repo.delete_role_menus(role_id)
        roles_repo.delete_role_actions(role_id)
        roles_repo.delete_role(role)


def replace_role_menus(role_id, menu_ids, *, role_type: int, pt_type: str):
    get_role(role_id, role_type=role_type)
    menu_ids = [menu_id for menu_id in menu_ids if not is_placeholder_id(menu_id)]
    if menu_ids:
        found = roles_repo.find_existing_menu_ids(menu_ids, pt_type=pt_type)
        missing = sorted(set(menu_ids) - found)
        if missing:
            raise ValidationError({"menu_ids": f"菜单不存在：{', '.join(missing)}"})
    roles_repo.delete_role_menus(role_id)
    roles_repo.bulk_create_role_menus(
        [RoleMenu(id=new_id(), role_id=role_id, menu_id=menu_id) for menu_id in menu_ids]
    )
    return role_menu_ids(role_id, pt_type=pt_type)


def replace_role_actions(role_id, action_ids, *, role_type: int):
    get_role(role_id, role_type=role_type)
    if action_ids:
        found = roles_repo.find_existing_action_ids(action_ids)
        missing = sorted(set(action_ids) - found)
        if missing:
            raise ValidationError({"action_ids": f"操作不存在：{', '.join(missing)}"})
    roles_repo.delete_role_actions(role_id)
    roles_repo.bulk_create_role_actions(
        [RoleAction(id=new_id(), role_id=role_id, action_id=action_id) for action_id in action_ids]
    )
    return role_action_ids(role_id)


def serialize_menu(menu):
    return serialize_sy_menu_map(menu)


def list_all_menu_rows():
    return [serialize_sy_menu_map(row) for row in menus_repo.list_all_rows()]


def get_menu(menu_id, *, pt_type: str | None = None):
    menu = menus_repo.get_platform_by_id(menu_id, pt_type) if pt_type else menus_repo.get_by_id(menu_id)
    if not menu:
        raise NotFound("菜单不存在")
    return menu


def create_menu(raw_data, *, pt_type: str):
    data = normalize_menu_write(as_payload(raw_data))
    reject_unknown_fields(data, MENU_WRITE_FIELDS)
    menu_name = required_text(data, "menu_name", max_length=255)
    menu_super_id = optional_text(data, "menu_super_id", max_length=64)
    if menu_super_id and not is_placeholder_id(menu_super_id):
        get_menu(menu_super_id)
    if menus_repo.menu_name_exists(menu_name, menu_super_id):
        raise ValidationError({"menu_name": "同级菜单名称已存在"})
    menu = Menu(
        id=new_id(),
        menu_super_id=menu_super_id,
        menu_status=optional_int(data, "menu_status") if "menu_status" in data else 1,
        menu_sort=optional_int(data, "menu_sort") if "menu_sort" in data else 0,
        menu_name=menu_name,
        menu_icon=optional_text(data, "menu_icon", max_length=255),
        menu_url=optional_text(data, "menu_url", max_length=1024),
        menu_target=optional_text(data, "menu_target", max_length=64),
        menu_rel=optional_text(data, "menu_rel", max_length=255),
        menu_open=optional_text(data, "menu_open", max_length=16),
        menu_external=optional_text(data, "menu_external", max_length=16),
        menu_fresh=optional_text(data, "menu_fresh", max_length=16),
        pt_type=pt_type,
    )
    menus_repo.save_menu(menu)
    return serialize_menu(menu)


def update_menu(menu_id, raw_data, *, pt_type: str):
    data = normalize_menu_write(as_payload(raw_data))
    reject_unknown_fields(data, MENU_WRITE_FIELDS)
    menu = get_menu(menu_id)
    menu_super_id = menu.menu_super_id
    if "menu_super_id" in data:
        menu_super_id = optional_text(data, "menu_super_id", max_length=64)
        if menu_super_id == menu_id:
            raise ValidationError({"menu_super_id": "不能把菜单设为自己的上级"})
        if menu_super_id and not is_placeholder_id(menu_super_id):
            get_menu(menu_super_id)
        menu.menu_super_id = menu_super_id
    if "menu_name" in data:
        menu_name = required_text(data, "menu_name", max_length=255)
        if menus_repo.menu_name_exists(menu_name, menu_super_id, exclude_id=menu_id):
            raise ValidationError({"menu_name": "同级菜单名称已存在"})
        menu.menu_name = menu_name
    if "menu_status" in data:
        menu.menu_status = optional_int(data, "menu_status")
    if "menu_sort" in data:
        menu.menu_sort = optional_int(data, "menu_sort")
    if "menu_icon" in data:
        menu.menu_icon = optional_text(data, "menu_icon", max_length=255)
    if "menu_url" in data:
        menu.menu_url = optional_text(data, "menu_url", max_length=1024)
    if "menu_target" in data:
        menu.menu_target = optional_text(data, "menu_target", max_length=64)
    if "menu_rel" in data:
        menu.menu_rel = optional_text(data, "menu_rel", max_length=255)
    if "menu_open" in data:
        menu.menu_open = optional_text(data, "menu_open", max_length=16)
    if "menu_external" in data:
        menu.menu_external = optional_text(data, "menu_external", max_length=16)
    if "menu_fresh" in data:
        menu.menu_fresh = optional_text(data, "menu_fresh", max_length=16)
    menus_repo.save_menu(menu)
    return serialize_menu(menu)


def delete_menu(menu_id, *, pt_type: str):
    menu = get_menu(menu_id)
    if menus_repo.has_children(menu_id):
        raise ValidationError({"detail": "菜单下属还有子菜单，无法删除"})
    with transaction.atomic():
        menus_repo.delete_role_menus_for_menu(menu_id)
        menus_repo.delete_menu(menu)


def list_department_rows():
    return departments_repo.list_tree_rows()


def get_department(dept_id):
    dept = departments_repo.get_by_id(dept_id)
    if not dept:
        raise NotFound("部门不存在")
    return dept


def create_department(raw_data):
    data = as_payload(raw_data)
    reject_unknown_fields(data, DEPT_WRITE_FIELDS)
    dept_name = required_text(data, "dept_name", max_length=255)
    super_id = optional_text(data, "super_id", max_length=64)
    if super_id:
        get_department(super_id)
    dept = Department(
        id=new_id(),
        dept_sort=optional_int(data, "dept_sort") if "dept_sort" in data else 0,
        dept_name=dept_name,
        dept_phone=optional_text(data, "dept_phone", max_length=64),
        dept_fax=optional_text(data, "dept_fax", max_length=64),
        dept_address=optional_text(data, "dept_address", max_length=255),
        super_id=super_id,
        lead_uid=optional_text(data, "lead_uid", max_length=64),
        dept_desc=optional_text(data, "dept_desc", max_length=1024),
    )
    departments_repo.save_department(dept)
    return serialize_department(dept)


def update_department(dept_id, raw_data):
    data = as_payload(raw_data)
    reject_unknown_fields(data, DEPT_WRITE_FIELDS)
    dept = get_department(dept_id)
    if "super_id" in data:
        super_id = optional_text(data, "super_id", max_length=64)
        if super_id == dept_id:
            raise ValidationError({"super_id": "不能把部门设为自己的上级"})
        if super_id:
            get_department(super_id)
        dept.super_id = super_id
    if "dept_name" in data:
        dept.dept_name = required_text(data, "dept_name", max_length=255)
    if "dept_sort" in data:
        dept.dept_sort = optional_int(data, "dept_sort")
    if "dept_phone" in data:
        dept.dept_phone = optional_text(data, "dept_phone", max_length=64)
    if "dept_fax" in data:
        dept.dept_fax = optional_text(data, "dept_fax", max_length=64)
    if "dept_address" in data:
        dept.dept_address = optional_text(data, "dept_address", max_length=255)
    if "lead_uid" in data:
        dept.lead_uid = optional_text(data, "lead_uid", max_length=64)
    if "dept_desc" in data:
        dept.dept_desc = optional_text(data, "dept_desc", max_length=1024)
    departments_repo.save_department(dept)
    return serialize_department(dept)


def delete_department(dept_id):
    dept = get_department(dept_id)
    if departments_repo.has_children(dept_id):
        raise ValidationError({"detail": "部门下还有子部门，无法删除"})
    departments_repo.delete_department(dept)


def get_user_access(user_id, *, pt_type: str):
    user = get_user(user_id, pt_type=pt_type)
    return {
        "pt_type": user.pt_type,
        "company_ids": list(access_repo.list_company_ids(user_id, pt_type)),
        "order_type_ids": list(access_repo.list_order_type_ids(user_id, pt_type)),
        "saleuser_ids": list(access_repo.list_saleuser_ids(user_id, pt_type)),
    }


def replace_user_access(user_id, payload, *, pt_type: str):
    data = as_payload(payload)
    reject_unknown_fields(data, {"company_ids", "order_type_ids", "saleuser_ids", "pt_type"})
    user = get_user(user_id, pt_type=pt_type)
    company_ids = mixed_id_list(data.get("company_ids"), "company_ids")
    order_type_ids = mixed_id_list(data.get("order_type_ids"), "order_type_ids")
    saleuser_ids = mixed_id_list(data.get("saleuser_ids"), "saleuser_ids")
    with transaction.atomic():
        if "pt_type" in data:
            user.pt_type = optional_text(data, "pt_type", max_length=32)
            users_repo.save_user(user)
        access_repo.soft_delete_company_links(user_id, pt_type)
        access_repo.soft_delete_order_type_links(user_id, pt_type)
        access_repo.soft_delete_saleuser_links(user_id, pt_type)
        access_repo.bulk_create_company_links(
            [
                UserCompanyLink(user_id=user_id, company_id=int(company_id), pt_type=pt_type, delete_status=False)
                for company_id in company_ids
            ]
        )
        access_repo.bulk_create_order_type_links(
            [
                UserOrderTypeLink(user_id=user_id, type_id=int(type_id), pt_type=pt_type, delete_status=False)
                for type_id in order_type_ids
            ]
        )
        access_repo.bulk_create_saleuser_links(
            [
                UserSalesLink(user_id=user_id, saleuser_id=str(saleuser_id), pt_type=pt_type, delete_status=False)
                for saleuser_id in saleuser_ids
            ]
        )
    return get_user_access(user_id, pt_type=pt_type)
