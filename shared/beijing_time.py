"""北京时间（Asia/Shanghai）约定助手。

现网 MySQL DATETIME 存的是北京墙钟（与 Java NOW() 一致），无时区后缀。
业务写入/展示一律按北京时间；勿用 datetime.utcnow() 写业务字段。
JWT exp 等协议字段可用 UTC，与业务表时间分开。
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def beijing_now() -> datetime:
    """当前北京时间（aware）。"""
    return datetime.now(BEIJING_TZ)


def beijing_now_naive() -> datetime:
    """当前北京墙钟（naive），写入 legacy DATETIME / 对齐 Java NOW()。"""
    return beijing_now().replace(tzinfo=None)


def to_beijing(value: datetime | None) -> datetime | None:
    """转为北京时间；naive 视为已是北京墙钟（不二次偏移）。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=BEIJING_TZ)
    return value.astimezone(BEIJING_TZ)


def format_beijing(value: datetime | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if value is None:
        return ""
    local = to_beijing(value)
    if local is None:
        return ""
    return local.strftime(fmt)


def format_beijing_day(value: datetime | None) -> str:
    return format_beijing(value, "%Y-%m-%d")
