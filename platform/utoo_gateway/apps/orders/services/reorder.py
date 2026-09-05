"""再来一单 — 业务层（无 SQL）"""
from __future__ import annotations

from datetime import datetime

from django.db import transaction

from apps.orders.repositories import reorder as reorder_repo
from apps.payments.repositories.pay_info import save_exp_user_log

_CONSULT_SKIP = {"id", "order_id"}
_CHILD_SKIP = {"id"}
_SAMPLE_SKIP = {"id"}


@transaction.atomic
def save_service_consult_from_order(*, user_id: int, order_id: int) -> tuple[bool, str]:
    consult = reorder_repo.get_consult_by_order_id(order_id)
    if not consult:
        return False, "未找到关联预约，请到测试预约详情重新预约"
    if int(consult.get("user_id") or 0) != int(user_id):
        return False, "无权操作"

    order_row = reorder_repo.get_order_brief(order_id)
    if not order_row:
        return False, "订单不存在"

    new_consult = dict(consult)
    new_consult["addTime"] = datetime.now()
    new_consult["status"] = 0
    new_consult["order_id"] = None
    new_consult_id = reorder_repo.insert_row(
        "service_consult", new_consult, skip=_CONSULT_SKIP
    )

    for child in reorder_repo.list_consult_children(int(consult["id"])):
        sample_id = child.get("sample_id")
        c = dict(child)
        c["consult_id"] = new_consult_id
        c["addTime"] = datetime.now()
        reorder_repo.insert_row("service_consult_child", c, skip=_CHILD_SKIP)
        if sample_id:
            sample = reorder_repo.get_sample_by_id(int(sample_id))
            if sample:
                s = dict(sample)
                s["consult_id"] = new_consult_id
                s["addTime"] = datetime.now()
                s["deleteStatus"] = 0
                reorder_repo.insert_row(
                    "order_sample_information", s, skip=_SAMPLE_SKIP
                )

    order_num = order_row.get("order_id") or str(order_id)
    save_exp_user_log(user_id, f"根据订单{order_num}操作再来一单成功")
    return True, "保存成功"
