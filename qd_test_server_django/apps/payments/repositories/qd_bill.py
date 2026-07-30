from __future__ import annotations

import logging
from decimal import Decimal

from apps.core.db_utils import execute

logger = logging.getLogger(__name__)


def insert_receive_bill(
    *, order_id: int, money: Decimal, user_id: int | None, log_info: str, bill_type: int = 2
) -> None:
    uid = int(user_id) if user_id not in (None, "") else None
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark)
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, %(bill_type)s, 0, NOW(), %(log_info)s)
        """,
        {
            "oid": order_id,
            "money": float(money),
            "bill_type": bill_type,
            "log_info": log_info,
            "uid": uid,
        },
    )
    # 对齐 Java saveBillAndAccessory：type=2 且成本已结清时触发分钱
    if int(bill_type or 2) == 2:
        try:
            from apps.payments.services.split_money import try_split_on_receive

            try_split_on_receive(int(order_id))
        except Exception:
            logger.exception("split after insert_receive_bill order_id=%s", order_id)
