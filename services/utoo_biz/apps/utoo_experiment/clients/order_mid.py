"""HTTP 客户端：utoo_biz → platform/order 中台。"""
from __future__ import annotations

from shared.utoo_order_proxy import proxy_order_mid_path


def forward(
    request,
    path: str,
    *,
    channel: str | None = None,
    extra_headers: dict[str, str] | None = None,
):
    return proxy_order_mid_path(
        request,
        path,
        channel=channel,
        extra_headers=extra_headers,
    )
