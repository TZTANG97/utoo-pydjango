"""公众号模板消息发送（对齐 Java WxServiceImpl）。"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# 与 Java ConstantsUtils 一致
ORDER_REVIEW = "k6r5tC9e7kNdtgTs0dwzjVogf1JtizcnwYGN6DokFd4"
ORDER_EXAMINE_RESULT = "jnI5630HGi-zerAk5r6WzNpd04H9ypxoiW1mNMXTpm8"
ORDER_REVIEW_RESULT = "pUFm4gwYB4CAnuZRHHfnQmpwKUExcOvXqlsSj2JuCbs"
SAMPLE_DETECTION_APPLY = "diMlb0m7cN04maSIk5wCYte-1IkeSSYvCXQIWMNTKQQ"
SAMPLE_DETECTION_RESULT = "QGbyoucerocG7finUBpBcAGnuc217GSwayoqva8ZAbE"
YPYDD = "GDXggLWmRgDBI01QTDJ0gZVMOVAPw-87Ft6Pn6yW0bI"
SAMPLE_SEND = "xdhZW5cmT9hAr58rRI6AtfWPo1i0E_FrhliJ1KJl0PY"

_COLOR = "#459ae9"
_COLOR_REMARK = "#383838"
_token_cache: dict[str, Any] = {"token": "", "expires_at": 0.0}


def _gzh_appid() -> str:
    return (
        getattr(settings, "WEIXIN_GZH_APPID", "")
        or getattr(settings, "WEIXIN_APPID", "")
        or ""
    ).strip()


def _gzh_secret() -> str:
    return (
        getattr(settings, "WEIXIN_GZH_SECRET", "")
        or getattr(settings, "WEIXIN_SECRET", "")
        or ""
    ).strip()


def _mini_appid() -> str:
    return (
        getattr(settings, "WEIXIN_MP_APPID", "")
        or getattr(settings, "WEIXIN_APPID", "")
        or ""
    ).strip()


def gzh_send_enabled() -> bool:
    raw = str(getattr(settings, "WEIXIN_GZH_SEND", "1") or "1").strip()
    return raw in ("1", "true", "True", "yes", "YES")


def wechat_gzh_configured() -> bool:
    return bool(_gzh_appid() and _gzh_secret())


def _init_data(value: Any, color: str = _COLOR) -> dict[str, str]:
    return {"value": "" if value is None else str(value), "color": color}


def _get_gzh_access_token(client: httpx.Client) -> str | None:
    now = time.time()
    if _token_cache["token"] and float(_token_cache["expires_at"]) > now + 30:
        return str(_token_cache["token"])
    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={_gzh_appid()}"
        f"&secret={_gzh_secret()}"
    )
    data = client.get(url, timeout=15.0).json()
    token = data.get("access_token")
    if not token:
        logger.warning("gzh access_token failed: %s", data)
        return None
    expires = int(data.get("expires_in") or 7200)
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + max(expires - 60, 60)
    return str(token)


def _build_payload(
    *,
    template_id: str,
    open_id: str,
    data: dict[str, dict[str, str]],
    page_path: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "touser": open_id,
        "template_id": template_id,
        "data": data,
    }
    path = (page_path or "").strip()
    appid = _mini_appid()
    if path and appid:
        body["miniprogram"] = {"appid": appid, "pagepath": path}
    return body


def send_template(
    *,
    template_id: str,
    open_id: str | None,
    data: dict[str, dict[str, str]],
    page_path: str | None = None,
) -> bool:
    """发送模板；失败只记日志，不抛异常。"""
    oid = (open_id or "").strip()
    if not oid:
        logger.info("skip wx template: empty openid template=%s", template_id)
        return False
    if not gzh_send_enabled():
        logger.info("skip wx template: WEIXIN_GZH_SEND disabled")
        return False
    if not wechat_gzh_configured():
        logger.warning("skip wx template: WEIXIN_GZH_APPID/SECRET not configured")
        return False
    try:
        with httpx.Client() as client:
            token = _get_gzh_access_token(client)
            if not token:
                return False
            payload = _build_payload(
                template_id=template_id,
                open_id=oid,
                data=data,
                page_path=page_path,
            )
            url = (
                "https://api.weixin.qq.com/cgi-bin/message/template/send"
                f"?access_token={token}"
            )
            resp = client.post(url, json=payload, timeout=15.0)
            result = resp.json()
            if int(result.get("errcode") or 0) != 0:
                logger.warning("wx template send failed: %s payload=%s", result, payload)
                if int(result.get("errcode") or 0) in (40001, 42001):
                    _token_cache["token"] = ""
                    _token_cache["expires_at"] = 0.0
                return False
            logger.info("wx template sent ok openid=%s template=%s", oid[:8], template_id)
            return True
    except Exception as exc:
        logger.warning("wx template send exception: %s", exc)
        return False


def send_exam_result(
    open_id: str | None,
    *,
    first: str,
    order_no: str,
    time_str: str,
    auditor: str,
    result: str,
    remark: str | None,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsgexamresult。"""
    data = {
        "first": _init_data(first),
        "character_string1": _init_data(order_no),
        "time2": _init_data(time_str),
        "thing3": _init_data(auditor),
        "const4": _init_data(result),
    }
    if remark is not None:
        data["remark"] = _init_data(remark, _COLOR_REMARK)
    return send_template(
        template_id=ORDER_EXAMINE_RESULT,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_order_apply(
    open_id: str | None,
    *,
    first: str,
    order_no: str,
    customer: str,
    time_str: str,
    amount: str,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsgorderapply（待审核）。"""
    data = {
        "first": _init_data(first),
        "character_string2": _init_data(order_no),
        "thing4": _init_data(customer),
        "time9": _init_data(time_str),
        "amount5": _init_data(amount),
    }
    return send_template(
        template_id=ORDER_REVIEW,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_pay_review(
    open_id: str | None,
    *,
    template_id: str,
    first: str,
    keyword1: str,
    keyword2: str,
    keyword3: str,
    keyword4: str,
    keyword5: str | None,
    remark: str | None,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsg（付款申请/审核结果，thing1/phone_number2/time4/const3）。"""
    data = {
        "first": _init_data(first),
        "thing1": _init_data(keyword1),
        "phone_number2": _init_data(keyword2),
        "time4": _init_data(keyword3),
        "const3": _init_data(keyword4),
    }
    if keyword5:
        data["keyword5"] = _init_data(keyword5)
    if remark is not None:
        data["remark"] = _init_data(remark, _COLOR_REMARK)
    return send_template(
        template_id=template_id,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_sample_apply(
    open_id: str | None,
    *,
    first: str,
    order_no: str,
    status: str,
    time_str: str,
    remark: str | None,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsgsampleapply。"""
    data = {
        "first": _init_data(first),
        "character_string1": _init_data(order_no),
        "const2": _init_data(status),
        "time3": _init_data(time_str),
    }
    if remark is not None:
        data["remark"] = _init_data(remark, _COLOR_REMARK)
    return send_template(
        template_id=SAMPLE_DETECTION_APPLY,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_sample_detection(
    open_id: str | None,
    *,
    first: str,
    order_no: str,
    status: str,
    operator: str,
    time_str: str,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsgdetection（样品到货 YPYDD）。"""
    data = {
        "first": _init_data(first),
        "character_string1": _init_data(order_no),
        "const2": _init_data(status),
        "thing3": _init_data(operator),
        "time4": _init_data(time_str),
    }
    return send_template(
        template_id=YPYDD,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_sample_send(
    open_id: str | None,
    *,
    first: str,
    order_no: str,
    express_name: str,
    express_no: str,
    time_str: str,
    keyword5: str | None,
    page_path: str | None,
) -> bool:
    """对齐 sendTemplateMsgsamplesend。"""
    data = {
        "first": _init_data(first),
        "character_string1": _init_data(order_no),
        "thing2": _init_data(express_name),
        "character_string3": _init_data(express_no),
        "time4": _init_data(time_str),
    }
    if keyword5:
        data["keyword5"] = _init_data(keyword5)
    return send_template(
        template_id=SAMPLE_SEND,
        open_id=open_id,
        data=data,
        page_path=page_path,
    )


def send_video(
    open_id: str | None,
    *,
    first: str,
    time_str: str,
    goods_name: str,
    meeting_num: str,
) -> bool:
    """对齐 sendTemplateMsgvideo（领用带会议号）。"""
    data = {
        "first": _init_data(first),
        "time1": _init_data(time_str),
        "thing2": _init_data(goods_name),
        "character_string3": _init_data(meeting_num),
    }
    return send_template(
        template_id=SAMPLE_DETECTION_RESULT,
        open_id=open_id,
        data=data,
        page_path=None,
    )
