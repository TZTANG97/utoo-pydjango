"""微信小程序 getPhoneNumber code → 手机号。"""
from __future__ import annotations

import logging
from typing import Literal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MpBrand = Literal["utoo", "tz"]


def _mp_credentials(brand: MpBrand) -> tuple[str, str]:
    if brand == "tz":
        appid = (getattr(settings, "WEIXIN_MP_TZ_APPID", "") or "").strip()
        secret = (getattr(settings, "WEIXIN_MP_TZ_SECRET", "") or "").strip()
    else:
        appid = (getattr(settings, "WEIXIN_MP_APPID", "") or "").strip()
        secret = (getattr(settings, "WEIXIN_MP_SECRET", "") or "").strip()
    # 回退到通用 WEIXIN_APPID（若未单独配置小程序）
    if not appid:
        appid = (getattr(settings, "WEIXIN_APPID", "") or "").strip()
    if not secret:
        secret = (getattr(settings, "WEIXIN_SECRET", "") or "").strip()
    return appid, secret


def _access_token(appid: str, secret: str) -> str | None:
    url = "https://api.weixin.qq.com/cgi-bin/token"
    try:
        r = requests.get(
            url,
            params={"grant_type": "client_credential", "appid": appid, "secret": secret},
            timeout=10,
        )
        data = r.json()
    except Exception as exc:
        logger.exception("wechat access_token failed: %s", exc)
        return None
    token = data.get("access_token")
    if not token:
        logger.warning("wechat access_token error: %s", data)
    return token


def get_phone_number(code: str, *, brand: MpBrand = "utoo") -> tuple[bool, str, str]:
    """
    返回 (ok, message, mobile)。
    开发环境若未配置 appid，可用 DEV_WX_PHONE 固定手机号联调。
    """
    if not code:
        return False, "code 不能为空", ""

    appid, secret = _mp_credentials(brand)
    if not appid or not secret:
        dev_phone = (getattr(settings, "DEV_WX_PHONE", "") or "").strip()
        if getattr(settings, "APP_ENV", "development") == "development" and dev_phone:
            logger.warning("WEIXIN_MP_* 未配置，使用 DEV_WX_PHONE=%s", dev_phone)
            return True, "ok", dev_phone
        return False, "未配置小程序 WEIXIN_MP_APPID / WEIXIN_MP_SECRET", ""

    token = _access_token(appid, secret)
    if not token:
        return False, "获取微信 access_token 失败", ""

    try:
        r = requests.post(
            f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={token}",
            json={"code": code},
            timeout=10,
        )
        data = r.json()
    except Exception as exc:
        logger.exception("getuserphonenumber failed: %s", exc)
        return False, "调用微信手机号接口失败", ""

    if data.get("errcode", 0) != 0:
        logger.warning("getuserphonenumber error: %s", data)
        return False, data.get("errmsg") or "获取手机号失败", ""

    info = data.get("phone_info") or {}
    mobile = (info.get("purePhoneNumber") or info.get("phoneNumber") or "").strip()
    if not mobile:
        return False, "微信未返回手机号", ""
    return True, "ok", mobile
