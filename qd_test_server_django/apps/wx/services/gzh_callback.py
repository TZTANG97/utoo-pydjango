"""公众号服务器回调 wechatconfig — 对齐 Java WxController / WxServiceImpl。"""
from __future__ import annotations

import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

import httpx
from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.core import redis_client
from apps.wx.repositories import reservation as res_repo
from apps.wx.repositories import wx_openid_info as temp_repo
from apps.wx.services.qr_login import (
    QR_PLACEHOLDER,
    _format_wechat_api_error,
    _get_gzh_access_token,
    _gzh_appid,
    wechat_configured,
)

logger = logging.getLogger(__name__)

RESPONSE_TXT = (
    "<xml><ToUserName><![CDATA[{to}]]></ToUserName>"
    "<FromUserName><![CDATA[{frm}]]></FromUserName>"
    "<CreateTime>{ts}</CreateTime>"
    "<MsgType><![CDATA[text]]></MsgType>"
    "<Content><![CDATA[{content}]]></Content></xml>"
)


def _gzh_server_token() -> str:
    return (getattr(settings, "WEIXIN_GZH_TOKEN", "") or "").strip() or "youtu"


def _mp_appid() -> str:
    return (
        (getattr(settings, "WEIXIN_MP_APPID", "") or "")
        or (getattr(settings, "WEIXIN_APPID", "") or "")
    ).strip()


def _auth_pagepath(openid: str, ticket: str) -> str:
    base = (
        getattr(settings, "WEIXIN_MP_AUTH_PAGEPATH", "") or "staffB/auth_phone/auth_phone"
    ).strip()
    return f"{base}?openid={quote(openid, safe='')}&ticket={quote(ticket, safe='')}"


def _thumb_media_id() -> str:
    return (getattr(settings, "WEIXIN_GZH_MINI_THUMB_MEDIA_ID", "") or "").strip()


def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    if not signature:
        return False
    parts = sorted([timestamp or "", nonce or "", _gzh_server_token()])
    digest = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return digest == signature


def parse_xml_message(body: bytes | str) -> dict[str, str]:
    if isinstance(body, bytes):
        text = body.decode("utf-8", errors="replace")
    else:
        text = body or ""
    if not text.strip():
        return {}
    root = ET.fromstring(text)
    out: dict[str, str] = {}
    for child in root:
        tag = child.tag
        out[tag] = (child.text or "").strip()
    return out


def _fetch_unionid(client: httpx.Client, access_token: str, openid: str) -> str:
    url = (
        "https://api.weixin.qq.com/cgi-bin/user/info"
        f"?access_token={access_token}&openid={openid}&lang=zh_CN"
    )
    try:
        data = client.get(url, timeout=15.0).json()
    except Exception as exc:
        logger.warning("user/info failed: %s", exc)
        return ""
    if data.get("errcode"):
        logger.warning("user/info error: %s", data)
        return ""
    return str(data.get("unionid") or "").strip()


def _welcome_text(openid: str) -> str:
    row = res_repo.find_user_brief_by_wx_openid(openid)
    if not row:
        return "你好，欢迎来到愉兔检测！请先绑定手机号注册登录."
    mobile = str(row.get("mobile") or "").strip()
    job = str(row.get("job") or "").strip()
    if not mobile or not job:
        return "你好，欢迎来到愉兔检测！请绑定手机号注册登录。"
    return "你好，欢迎来到愉兔检测！"


def _send_miniprogram_card(
    client: httpx.Client,
    *,
    access_token: str,
    openid: str,
    ticket: str,
) -> None:
    appid = _mp_appid()
    thumb = _thumb_media_id()
    if not appid:
        logger.warning("skip miniprogram card: WEIXIN_MP_APPID empty")
        return
    if not thumb:
        logger.warning("skip miniprogram card: WEIXIN_GZH_MINI_THUMB_MEDIA_ID empty")
        return
    pagepath = _auth_pagepath(openid, ticket)
    payload = {
        "touser": openid,
        "msgtype": "miniprogrampage",
        "miniprogrampage": {
            "title": "愉兔小程序",
            "appid": appid,
            "pagepath": pagepath,
            "thumb_media_id": thumb,
        },
    }
    url = (
        "https://api.weixin.qq.com/cgi-bin/message/custom/send"
        f"?access_token={access_token}"
    )
    try:
        data = client.post(url, json=payload, timeout=15.0).json()
        if data.get("errcode"):
            logger.warning("custom/send card error: %s", data)
    except Exception as exc:
        logger.warning("custom/send card failed: %s", exc)


def exec_event_and_send(
    msg: dict[str, str],
    *,
    mark_ticket: bool = False,
) -> str:
    """处理扫码/关注：写 Redis、存 unionid、回欢迎语、推授权卡片或写 openid→mobile。"""
    openid = (msg.get("FromUserName") or "").strip()
    to_user = (msg.get("ToUserName") or "").strip()
    ticket = (msg.get("Ticket") or "").strip()
    event = (msg.get("Event") or "").strip()
    if not openid:
        return "success"

    if mark_ticket and ticket:
        cur = redis_client.get_string(ticket)
        if cur == QR_PLACEHOLDER:
            redis_client.set_string(ticket, openid, ex=120)

    welcome = "success"
    try:
        with httpx.Client() as client:
            access_token, err = _get_gzh_access_token(client)
            if not access_token:
                logger.warning("gzh token for callback: %s", err or _format_wechat_api_error({}))
            else:
                unionid = _fetch_unionid(client, access_token, openid)
                if unionid:
                    temp_repo.insert_openid_unionid(openid, unionid)
                    temp_repo.update_sy_user_unionid(openid, unionid)

            if event in ("subscribe", "SCAN", "TEMPLATESENDJOBFINISH", ""):
                welcome = RESPONSE_TXT.format(
                    to=openid,
                    frm=to_user,
                    ts=int(time.time()),
                    content=_welcome_text(openid),
                )

            # sendpicture
            row = res_repo.find_user_brief_by_wx_openid(openid)
            need_card = True
            if row:
                mobile = str(row.get("mobile") or "").strip()
                job = str(row.get("job") or "").strip()
                if mobile and job:
                    redis_client.set_string(openid, mobile, ex=120)
                    need_card = False
            if need_card and access_token and ticket:
                _send_miniprogram_card(
                    client,
                    access_token=access_token,
                    openid=openid,
                    ticket=ticket,
                )
            elif need_card and access_token and not ticket:
                # 非扫码关注：仍尝试推卡（无 ticket 时页面可能过期校验失败）
                _send_miniprogram_card(
                    client,
                    access_token=access_token,
                    openid=openid,
                    ticket="",
                )
    except Exception as exc:
        logger.exception("exec_event_and_send failed: %s", exc)

    return welcome


def handle_wechatconfig(request: HttpRequest) -> HttpResponse:
    method = request.method.upper()
    if method == "GET":
        signature = request.GET.get("signature") or ""
        timestamp = request.GET.get("timestamp") or ""
        nonce = request.GET.get("nonce") or ""
        echostr = request.GET.get("echostr") or ""
        if verify_signature(signature, timestamp, nonce):
            return HttpResponse(echostr, content_type="text/plain; charset=utf-8")
        return HttpResponse("invalid signature", status=403, content_type="text/plain")

    if method != "POST":
        return HttpResponse("method not allowed", status=405)

    if not wechat_configured() and not _gzh_appid():
        logger.warning("wechatconfig POST but GZH appid empty")

    try:
        msg = parse_xml_message(request.body)
    except Exception as exc:
        logger.exception("wechatconfig XML parse error: %s", exc)
        return HttpResponse("success", content_type="text/plain")

    msg_type = (msg.get("MsgType") or "").strip().lower()
    event = (msg.get("Event") or "").strip()
    ticket = (msg.get("Ticket") or "").strip()

    reply = "success"
    if msg_type == "event" and ticket:
        # 若 Redis 仍是占位则写入 openid；否则仍走欢迎语/推卡
        reply = exec_event_and_send(msg, mark_ticket=True)
    elif event.upper() == "CLICK":
        # 菜单点击：仅回简单欢迎，不推登录卡
        openid = msg.get("FromUserName") or ""
        to_user = msg.get("ToUserName") or ""
        reply = RESPONSE_TXT.format(
            to=openid,
            frm=to_user,
            ts=int(time.time()),
            content="请发送文字留言，客服会尽快回复",
        )
    elif not ticket and msg_type == "event":
        reply = exec_event_and_send(msg, mark_ticket=False)
    elif msg_type == "text":
        reply = "success"

    if reply.startswith("<xml"):
        return HttpResponse(reply, content_type="application/xml; charset=utf-8")
    return HttpResponse(reply or "success", content_type="text/plain; charset=utf-8")
