from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any

import jwt
from django.conf import settings

from apps.identity.channel import ChannelContext
from apps.identity.jwt_tokens import create_access_token, create_refresh_token
from apps.identity.repositories import scope as scope_repo
from apps.identity.repositories import staff as staff_repo
from apps.identity.services import menus as menu_proj
from apps.identity.services.customer import CustomerUserService
from qd_common.password_java import verify_password

LEGACY_HEX_DIGITS = "A1B3C5D7E9F0G2H4"


def _legacy_md5(password: str) -> str:
    encoding = getattr(settings, "LEGACY_PASSWORD_ENCODING", "utf-8")
    digest = hashlib.md5(password.encode(encoding)).digest()
    return "".join(LEGACY_HEX_DIGITS[byte >> 4] + LEGACY_HEX_DIGITS[byte & 0x0F] for byte in digest)


def _validate_staff_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    ok, _ = verify_password(password, stored)
    if ok:
        return True
    return hmac.compare_digest(_legacy_md5(password), stored)


def _build_child_menus_utoo(all_menus: list[dict[str, Any]], super_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for row in all_menus:
        if str(row.get("menu_super_id") or "") != super_id:
            continue
        menu_id = str(row.get("id") or "")
        children.append(
            {
                "id": menu_id,
                "name": row.get("menu_name") or "",
                "url": row.get("menu_url") or "",
                "icon": row.get("menu_icon") or "",
                "superId": row.get("menu_super_id") or "",
                "childrenMenus": _build_child_menus_utoo(all_menus, menu_id),
            }
        )
    return children


def _build_child_menus_mall(all_menus: list[dict[str, Any]], super_id: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for row in all_menus:
        if str(row.get("menu_super_id") or "") != (super_id or ""):
            continue
        menu_id = str(row.get("id") or "")
        children.append(
            {
                "id": menu_id,
                "menu_super_id": row.get("menu_super_id"),
                "menu_name": row.get("menu_name") or "",
                "menu_url": row.get("menu_url"),
                "menu_icon": row.get("menu_icon"),
                "menu_target": row.get("menu_target"),
                "menu_rel": row.get("menu_rel"),
                "children": _build_child_menus_mall(all_menus, menu_id),
            }
        )
    return children


def build_menu_tree(user_id: str, ctx: ChannelContext) -> list[dict[str, Any]]:
    if not ctx.returns_admin_menus or not ctx.platform:
        return []
    role_type = int(ctx.platform)
    tops = staff_repo.fetch_top_level_menus(user_id, role_type, ctx.platform)
    all_menus = staff_repo.fetch_user_menus(user_id, role_type, ctx.platform)
    all_menus = menu_proj.filter_menus_by_platform(all_menus, ctx.platform)
    tree: list[dict[str, Any]] = []
    for row in tops:
        if not menu_proj.menu_matches_platform(row.get("pt_type"), ctx.platform):
            continue
        menu_id = str(row.get("id") or "")
        if ctx.channel == "mall_qd":
            tree.append(
                {
                    "id": menu_id,
                    "menu_super_id": row.get("menu_super_id"),
                    "menu_name": row.get("menu_name") or "",
                    "menu_url": row.get("menu_url"),
                    "menu_icon": row.get("menu_icon"),
                    "menu_target": row.get("menu_target"),
                    "menu_rel": row.get("menu_rel"),
                    "children": _build_child_menus_mall(all_menus, menu_id),
                }
            )
        else:
            tree.append(
                {
                    "id": menu_id,
                    "menuName": row.get("menu_name") or "",
                    "url": row.get("menu_url") or "",
                    "icon": row.get("menu_icon") or "",
                    "childMenu": _build_child_menus_utoo(all_menus, menu_id),
                }
            )
    return tree


def _issue_mall_token(user_row: dict[str, Any], ctx: ChannelContext, permissions: dict) -> str:
    user_id = str(user_row["id"])
    scope = scope_repo.build_data_scope(user_id, user_row.get("type") or user_row.get("account_type"), ctx.platform or "1")
    now = datetime.utcnow()
    ttl = int(getattr(settings, "MALL_JWT_TTL_SECONDS", settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    payload = {
        "sub": user_id,
        "user_name": user_row.get("user_name") or "",
        "dept_id": user_row.get("dept_id"),
        "type": user_row.get("type") or user_row.get("account_type"),
        "scope": scope,
        "role_ids": permissions["role_ids"],
        "permissions": permissions["permissions"],
        "channel": ctx.channel,
        "platform": ctx.platform,
        "account_kind": "sy_user",
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "iss": settings.MALL_JWT_ISSUER,
    }
    secret = settings.MALL_JWT_SECRET
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token.decode("utf-8") if isinstance(token, bytes) else token


def authenticate_staff(
    login_name: str, password: str, ctx: ChannelContext
) -> tuple[dict[str, Any] | None, str]:
    if ctx.account_kind != "sy_user" or not ctx.platform:
        return None, "当前渠道不是员工登录"
    row = staff_repo.find_sy_user_by_login_name(login_name)
    if not row:
        return None, "登录失败,请确认是否有此平台登录权限!"
    if int(row.get("user_status") or 0) == 0:
        return None, "用户被限制登录，请联系管理员"
    if not _validate_staff_password(password, row.get("user_password") or ""):
        return None, "用户名或密码错误，请重新登录"

    user_id = str(row["id"])
    permissions = scope_repo.build_permissions(user_id, ctx.platform)
    scope = scope_repo.build_data_scope(
        user_id, str(row.get("type") or row.get("account_type") or ""), ctx.platform
    )

    if ctx.channel == "mall_qd":
        access = _issue_mall_token(row, ctx, permissions)
        return {
            "access_token": access,
            "token_type": "Bearer",
            "expires_in": int(
                getattr(settings, "MALL_JWT_TTL_SECONDS", settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
            ),
            "user": {
                "id": user_id,
                "user_name": row.get("user_name") or "",
                "true_name": row.get("true_name") or "",
                "dept_id": row.get("dept_id"),
                "mobile_phone_number": row.get("mobile_phone_number"),
                "email": row.get("email"),
                "type": row.get("type") or row.get("account_type"),
                "pt_type": row.get("pt_type"),
                "scope": scope,
                "role_ids": permissions["role_ids"],
            },
            "permissions": permissions["permissions"],
        }, ""

    token_data = {
        "sub": user_id,
        "user_id": user_id,
        "user_name": row.get("user_name") or "",
        "true_name": row.get("true_name") or "",
        "user_type": "0",
        "dept_id": str(row.get("dept_id") or ""),
        "account_kind": "sy_user",
        "channel": ctx.channel,
        "platform": ctx.platform,
        "role_ids": permissions["role_ids"],
    }
    access = create_access_token(token_data)
    refresh = create_refresh_token(
        {
            "user_id": user_id,
            "account_kind": "sy_user",
            "channel": ctx.channel,
            "platform": ctx.platform,
        }
    )
    return {
        "token": access,
        "refreshToken": refresh,
        "userName": row.get("true_name") or row.get("user_name") or "",
        "loginName": row.get("user_name") or "",
        "userType": 0,
        "channel": ctx.channel,
        "platform": ctx.platform,
        "accountKind": "sy_user",
        "roleIds": permissions["role_ids"],
    }, ""


def authenticate_customer(
    login_name: str, password: str, ctx: ChannelContext
) -> tuple[dict[str, Any] | None, str]:
    if ctx.account_kind != "exp_user":
        return None, "当前渠道不是会员登录"
    user = CustomerUserService.find_by_login_name(login_name)
    if not user:
        return None, "账号未注册"
    ok, scheme = verify_password(password, user.password or "")
    if not ok:
        return None, "密码错误"
    if scheme in ("std_hex_md5", "plaintext"):
        CustomerUserService.rehash_password_if_legacy(user, password)
    token_data = CustomerUserService.exp_user_token_data(user, channel=ctx.channel)
    access = create_access_token(token_data)
    refresh = create_refresh_token(
        {"user_id": str(user.id), "account_kind": "exp_user", "channel": ctx.channel}
    )
    payload = CustomerUserService.build_login_payload(user, access, refresh)
    payload["channel"] = ctx.channel
    return payload, ""


def login(login_name: str, password: str, ctx: ChannelContext) -> tuple[dict[str, Any] | None, str]:
    if ctx.account_kind == "exp_user":
        return authenticate_customer(login_name, password, ctx)
    return authenticate_staff(login_name, password, ctx)


def refresh_customer(refresh_token: str) -> tuple[dict[str, Any] | None, str]:
    from apps.identity.jwt_tokens import decode_token

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None, "刷新令牌无效"
    if payload.get("account_kind") != "exp_user":
        return None, "仅支持会员刷新"
    user_id = payload.get("user_id")
    channel = payload.get("channel") or "pc"
    if not user_id:
        return None, "刷新令牌无效"
    user = CustomerUserService.get_by_id(int(user_id))
    if not user:
        return None, "用户不存在"
    token_data = CustomerUserService.exp_user_token_data(user, channel=channel)
    access = create_access_token(token_data)
    refresh = create_refresh_token(
        {"user_id": str(user.id), "account_kind": "exp_user", "channel": channel}
    )
    body = CustomerUserService.build_login_payload(user, access, refresh)
    body["channel"] = channel
    return body, ""
