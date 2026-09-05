from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from django.conf import settings
from wechatpayv3 import WeChatPay, WeChatPayType

from apps.payments.services.wx_settings import load_private_key_pem, notify_url
from apps.payments.services.wx_sign import sign_native_display

logger = logging.getLogger(__name__)


def _build_client(callback_path: str) -> WeChatPay:
    return WeChatPay(
        wechatpay_type=WeChatPayType.NATIVE,
        mchid=settings.WEIXIN_MERCHANT_ID,
        private_key=load_private_key_pem(),
        cert_serial_no=settings.WEIXIN_MERCHANT_SERIAL_NUMBER,
        apiv3_key=settings.WEIXIN_API_V3_KEY,
        appid=settings.WEIXIN_APPID,
        notify_url=notify_url(callback_path),
    )


def native_prepay(
    *,
    callback_path: str,
    description: str,
    out_trade_no: str,
    total_fen: int,
) -> tuple[bool, str, dict[str, Any]]:
    try:
        wx = _build_client(callback_path)
        code, message = wx.pay(
            description=description,
            out_trade_no=out_trade_no,
            amount={"total": total_fen, "currency": "CNY"},
            pay_type=WeChatPayType.NATIVE,
        )
        if code != 200:
            logger.warning("wechat prepay failed code=%s msg=%s", code, message)
            return False, f"微信下单失败：{message}", {}
        payload = json.loads(message) if isinstance(message, str) else (message or {})
        code_url = payload.get("code_url") or payload.get("codeUrl")
        if not code_url:
            return False, "微信未返回 code_url", {}
        ts = int(time.time())
        nonce = uuid.uuid4().hex[:32]
        pay_sign = sign_native_display(settings.WEIXIN_APPID, ts, nonce, code_url)
        return True, "ok", {
            "codeUrl": code_url,
            "timeStamp": ts,
            "nonceStr": nonce,
            "paySign": pay_sign,
            "outTradeNo": out_trade_no,
        }
    except Exception as exc:
        logger.exception("native_prepay error: %s", exc)
        return False, f"微信下单失败：{exc}", {}


def query_by_transaction_id(transaction_id: str) -> tuple[bool, str]:
    try:
        wx = _build_client("/pc/pay.ajax")
        code, message = wx.query(transaction_id=transaction_id)
        if code != 200:
            return False, ""
        data = json.loads(message) if isinstance(message, str) else (message or {})
        return True, str(data.get("trade_state") or "")
    except Exception as exc:
        logger.exception("query order failed: %s", exc)
        return False, ""


def parse_notify(headers: dict, body: bytes) -> dict[str, Any] | None:
    try:
        wx = _build_client("/pc/pay.ajax")
        data = wx.callback(headers, body)
    except Exception as exc:
        logger.warning("parse_notify failed: %s", exc)
        return None
    if not data:
        return None
    return data.get("resource") or {}
