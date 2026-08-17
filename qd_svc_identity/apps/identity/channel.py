"""X-Channel → 账号体系 / 平台码投影（一期不含工厂 type=3）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AccountKind = Literal["sy_user", "exp_user"]
PlatformCode = Literal["1", "2"]

# 一期启用渠道；emku/factory 二期再开
CHANNEL_STAFF = frozenset({"mall_qd", "admin"})
CHANNEL_CUSTOMER = frozenset({"pc", "wx"})
CHANNEL_ALL = CHANNEL_STAFF | CHANNEL_CUSTOMER


@dataclass(frozen=True)
class ChannelContext:
    channel: str
    account_kind: AccountKind
    """员工走 sy_users；会员走 exp_user。"""
    platform: PlatformCode | None
    """sy_role.type / sy_menu.pt_type 投影码；会员渠道为 None（不拉后台菜单）。"""
    returns_admin_menus: bool


class ChannelError(ValueError):
    pass


def normalize_channel(raw: str | None) -> str:
    return (raw or "").strip().lower()


def resolve_channel(raw: str | None) -> ChannelContext:
    channel = normalize_channel(raw)
    if not channel:
        raise ChannelError("缺少 X-Channel")
    if channel in ("emku", "factory"):
        raise ChannelError("一期不含工厂渠道 emku/factory")
    if channel not in CHANNEL_ALL:
        raise ChannelError(f"不支持的 X-Channel: {channel}")

    if channel in CHANNEL_CUSTOMER:
        return ChannelContext(
            channel=channel,
            account_kind="exp_user",
            platform=None,
            returns_admin_menus=False,
        )

    platform: PlatformCode = "1" if channel == "mall_qd" else "2"
    return ChannelContext(
        channel=channel,
        account_kind="sy_user",
        platform=platform,
        returns_admin_menus=True,
    )


def channel_from_request(request) -> ChannelContext:
    raw = request.META.get("HTTP_X_CHANNEL") or request.headers.get("X-Channel")
    return resolve_channel(raw)
