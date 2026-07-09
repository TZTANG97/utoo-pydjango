"""复测申请 — 业务层（无 SQL）"""
from __future__ import annotations

from datetime import datetime

from django.db import transaction

from apps.orders.repositories import retest as retest_repo
from apps.payments.repositories.pay_order_code import gen_code


def _generate_fc_order_id() -> str:
    orderstr = "FC" + datetime.now().strftime("%Y%m")
    row = retest_repo.get_latest_fc_order_id(f"{orderstr}%")
    if row and row.get("order_id"):
        n = int(str(row["order_id"])[-5:]) + 1
        return orderstr + gen_code(n)
    return orderstr + gen_code(1)


@transaction.atomic
def add_retest_application(
    *,
    user_id: int,
    order_id: str,
    mark: str = "",
    remeasurement_require: str = "",
) -> tuple[bool, str]:
    if not order_id or not str(order_id).isdigit():
        return False, "参数错误"

    if not retest_repo.get_child_order(int(order_id)):
        return False, "子订单不存在"

    if retest_repo.get_pending_retest(user_id=user_id, order_id=order_id):
        return False, "您已申请复测，请等待审核！"

    retest_repo.insert_retest_application(
        user_id=user_id,
        order_id=order_id,
        mark=mark or "",
        remeasurement_require=remeasurement_require or "",
        fc_no=_generate_fc_order_id(),
    )
    return True, "申请成功"
