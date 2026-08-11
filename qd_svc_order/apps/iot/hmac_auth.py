"""IOT 回调 HMAC 校验。"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from django.conf import settings


class HmacAuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _header(request, name: str) -> str:
    meta_key = "HTTP_" + name.upper().replace("-", "_")
    return str(request.META.get(meta_key) or "").strip()


def verify_iot_hmac(request, raw_body: bytes) -> dict[str, str]:
    """
    校验 X-IOT-* 头。
    stringToSign = timestamp + "\\n" + nonce + "\\n" + rawBody
    """
    app_id = _header(request, "X-IOT-App-Id")
    ts_raw = _header(request, "X-IOT-Timestamp")
    nonce = _header(request, "X-IOT-Nonce")
    signature = _header(request, "X-IOT-Signature")

    expected_app = str(getattr(settings, "IOT_APP_ID", "") or "").strip()
    secret = str(getattr(settings, "IOT_HMAC_SECRET", "") or "").strip()
    if not secret:
        raise HmacAuthError("IOT_SIGN_INVALID", "IOT_HMAC_SECRET 未配置")
    if expected_app and app_id and app_id != expected_app:
        raise HmacAuthError("IOT_SIGN_INVALID", "AppId 不匹配")
    if not ts_raw or not nonce or not signature:
        raise HmacAuthError("IOT_SIGN_INVALID", "缺少签名头")

    try:
        ts = int(ts_raw)
    except (TypeError, ValueError) as exc:
        raise HmacAuthError("IOT_SIGN_INVALID", "Timestamp 无效") from exc

    now = int(time.time())
    if abs(now - ts) > 300:
        raise HmacAuthError("IOT_TS_EXPIRED", "Timestamp 过期")

    body_text = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else str(raw_body or "")
    string_to_sign = f"{ts}\n{nonce}\n{body_text}"
    digest = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest.lower(), signature.lower()):
        raise HmacAuthError("IOT_SIGN_INVALID", "签名校验失败")

    whitelist = str(getattr(settings, "IOT_CALLBACK_IP_WHITELIST", "") or "").strip()
    if whitelist:
        allowed = {x.strip() for x in whitelist.split(",") if x.strip()}
        client_ip = _client_ip(request)
        if allowed and client_ip and client_ip not in allowed:
            raise HmacAuthError("IOT_SIGN_INVALID", f"IP 不在白名单: {client_ip}")

    return {"appId": app_id, "timestamp": ts_raw, "nonce": nonce}


def _client_ip(request) -> str:
    xff = str(request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    if xff:
        return xff
    return str(request.META.get("REMOTE_ADDR") or "").strip()
