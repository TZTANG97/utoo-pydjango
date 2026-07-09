from __future__ import annotations

from decimal import Decimal

from apps.core.db_utils import execute


def insert_receive_bill(
    *, order_id: int, money: Decimal, user_id: int, log_info: str, bill_type: int = 2
) -> None:
    execute(
        """
        INSERT INTO qd_bill
            (add_time, delete_status, exp_of_id, money, type, is_split,
             bill_date, log_info, log_user_id)
        VALUES
            (NOW(), 0, %(oid)s, %(money)s, %(bill_type)s, 0, NOW(), %(log_info)s, %(uid)s)
        """,
        {
            "oid": order_id,
            "money": float(money),
            "bill_type": bill_type,
            "log_info": log_info,
            "uid": user_id,
        },
    )
