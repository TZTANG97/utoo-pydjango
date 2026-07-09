"""微信扫码登录 — WeChatQRCodeGenerator / qrScanStatusCheck"""
from __future__ import annotations

import logging
from urllib.parse import quote

import httpx
from django.conf import settings

from apps.auth_support.customer import CustomerUserService
from apps.auth_support.jwt_tokens import create_access_token, create_refresh_token
from apps.auth_support.profile import UserProfileService
from apps.core import redis_client
from apps.wx.repositories import reservation as res_repo
from qd_common.oss_url import default_avatar_url

logger = logging.getLogger(__name__)

QR_PLACEHOLDER = "已生成二维码"
GZH_TOKEN_KEY = "gzh_access_token"

STATUS_NOT_SCAN = "NOT_SCAN"
STATUS_SCANNED = "SCANNED"
STATUS_LOGGED_IN = "LOGGED_IN"
STATUS_EXPIRED = "EXPIRED"


def _gzh_appid() -> str:
    return (settings.WEIXIN_GZH_APPID or settings.WEIXIN_APPID or "").strip()


def _gzh_secret() -> str:
    return (settings.WEIXIN_GZH_SECRET or settings.WEIXIN_SECRET or "").strip()


def wechat_configured() -> bool:
    return bool(_gzh_appid() and _gzh_secret())


def _format_wechat_api_error(data: dict) -> str:
    errcode = data.get("errcode")
    errmsg = str(data.get("errmsg") or "微信接口调用失败")
    if errcode in (40164, 40165) or "not in whitelist" in errmsg.lower():
        return (
            "微信公众号接口 IP 未在白名单：请在微信公众平台 → 开发 → 基本配置 → "
            "IP 白名单中加入当前服务器公网 IP 后重试"
        )
    return f"微信接口错误({errcode})：{errmsg}"


def _get_gzh_access_token(client: httpx.Client) -> tuple[str | None, str]:
    cached = redis_client.get_string(GZH_TOKEN_KEY)
    if cached:
        return cached, ""
    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={_gzh_appid()}"
        f"&secret={_gzh_secret()}"
    )
    data = client.get(url, timeout=15.0).json()
    token = data.get("access_token")
    if not token:
        logger.warning("wechat token error: %s", data)
        return None, _format_wechat_api_error(data)
    expires = int(data.get("expires_in") or 7200)
    redis_client.set_string(GZH_TOKEN_KEY, token, ex=max(expires - 10, 60))
    return token, ""


def _create_qr_ticket(client: httpx.Client, access_token: str) -> str | None:
    url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}"
    body = {
        "expire_seconds": 120,
        "action_name": "QR_STR_SCENE",
        "action_info": {"scene": {"scene_str": "pc_login"}},
    }
    data = client.post(url, json=body, timeout=15.0).json()
    if data.get("errcode"):
        logger.warning("wechat qrcode create error: %s", data)
        return None
    return data.get("ticket")


def generate_qrcode_url() -> tuple[bool, str, dict]:
    if not wechat_configured():
        return (
            False,
            "微信扫码登录未配置 WEIXIN_GZH_APPID / WEIXIN_GZH_SECRET",
            {},
        )
    try:
        with httpx.Client() as client:
            access_token, token_err = _get_gzh_access_token(client)
            if not access_token:
                return False, token_err or "获取微信 access_token 失败", {}
            ticket = _create_qr_ticket(client, access_token)
            if not ticket:
                redis_client.delete_key(GZH_TOKEN_KEY)
                access_token, token_err = _get_gzh_access_token(client)
                if access_token:
                    ticket = _create_qr_ticket(client, access_token)
            if not ticket:
                return False, "生成二维码失败", {}
            redis_client.set_string(ticket, QR_PLACEHOLDER, ex=120)
            show_url = (
                "https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket="
                + quote(ticket, safe="")
            )
            return True, "ok", {"url": show_url}
    except Exception as exc:
        logger.exception("generate_qrcode_url failed: %s", exc)
        return False, f"生成二维码失败：{exc}", {}


def check_qr_scan_status(ticket: str) -> tuple[bool, str, object]:
    if not ticket:
        return False, "ticket 不能为空", STATUS_EXPIRED
    try:
        openid = redis_client.get_string(ticket)
        if openid is None:
            return True, "二维码已过期", STATUS_EXPIRED
        if openid == QR_PLACEHOLDER:
            return True, "未扫码", STATUS_NOT_SCAN

        phone = redis_client.get_string(openid)
        user = CustomerUserService.find_by_login_name(phone) if phone else None
        if user is None and openid:
            uid = res_repo.find_user_by_wx_openid(openid)
            if uid:
                user = CustomerUserService.get_by_id(uid)

        if user is None:
            return True, "已扫码", STATUS_SCANNED

        token_data = CustomerUserService.exp_user_token_data(user)
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(
            {"user_id": str(user.id), "account_kind": token_data.get("account_kind")}
        )
        avatar = UserProfileService.avatar_url(user.photo_id)
        payload = {
            "token": access_token,
            "refresh_token": refresh_token,
            "nickName": CustomerUserService.display_name(user),
            "phone": user.mobile or "",
            "avatar": avatar or default_avatar_url(),
        }
        redis_client.delete_key(ticket)
        return True, "已登录", payload
    except Exception as exc:
        logger.exception("check_qr_scan_status failed: %s", exc)
        return False, "扫码登录状态查询失败!", STATUS_EXPIRED
