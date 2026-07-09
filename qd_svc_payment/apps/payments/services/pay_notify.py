from __future__ import annotations

from apps.payments.services.wechat_notify_handler import (
    handle_recharge_notify,
    handle_single_order_pay_notify,
)

KIND_RECHARGE = "recharge"
KIND_ORDER = "order"


def dispatch_pay_notify(kind: str, resource: dict) -> None:
    """同步处理微信回调（Django 版；队列消费可后续交给 qd_worker）。"""
    if kind == KIND_RECHARGE:
        handle_recharge_notify(resource)
    else:
        handle_single_order_pay_notify(resource)
