"""订单附件/预约单 — 业务层（无 SQL）"""
from __future__ import annotations

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import accessory as accessory_repo
from apps.payments.repositories.pay_info import save_exp_user_log


def can_upload_accessory(*, order_id: int) -> tuple[bool, str]:
    of = accessory_repo.get_order_type(order_id)
    if not of:
        return False, "订单不存在"
    order_type = str(of.get("order_type") or "")
    if order_type in ("0", "10"):
        return False, "当前订单状态不能进行添加回执单"
    if accessory_repo.count_order_accessories(order_id) == 0:
        return True, "可以上传"
    return False, "已有回执单"


def print_yyd_url(*, user_id: int, order_id: int) -> tuple[bool, str, dict]:
    acc = accessory_repo.get_yyd_attachment(order_id)
    config = get_config_row()
    base = image_web_server(config).rstrip("/")
    url = ""
    if acc and acc.get("path") and acc.get("name"):
        url = f"{base}/{str(acc['path']).strip('/')}/{str(acc['name']).strip('/')}"

    orow = accessory_repo.get_order_num(order_id)
    if orow:
        save_exp_user_log(
            user_id,
            f"打印预约单成功，关联单号{orow.get('order_id') or order_id}",
        )
    return True, "ok", {"url": url}
