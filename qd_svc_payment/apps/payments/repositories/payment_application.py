from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from apps.core.db_utils import execute, execute_insert, fetch_one
from apps.payments.repositories.pay_order_code import gen_code


def generate_pa_num(_order_type: str | None = None) -> str:
    orderstr = "CZ" + datetime.now().strftime("%Y%m")
    row = fetch_one(
        """
        SELECT pa_num FROM payment_application
        WHERE deleteStatus = 0 AND pa_num LIKE %(like)s
        ORDER BY pa_num DESC
        LIMIT 1
        """,
        {"like": f"{orderstr}%"},
    )
    if row and row.get("pa_num"):
        n = int(str(row["pa_num"])[-5:]) + 1
        return orderstr + gen_code(n)
    return orderstr + gen_code(1)


def insert_application(
    *, user_id: int, amount: Decimal, pay_way: int, pa_num: str
) -> int:
    return execute_insert(
        """
        INSERT INTO payment_application
            (addTime, deleteStatus, userId, orderType, applyStatus,
             money, pay_way, pa_num, ptype)
        VALUES
            (NOW(), 0, %(uid)s, '1', '1', %(money)s, %(pay_way)s, %(pa_num)s, '0')
        """,
        {
            "uid": user_id,
            "money": float(amount),
            "pay_way": pay_way,
            "pa_num": pa_num,
        },
    )


def link_accessories(*, pa_id: int, file_ids: str) -> None:
    for fid in file_ids.split(","):
        fid = fid.strip()
        if fid.isdigit():
            execute(
                "UPDATE accessory SET pa_id = %(pid)s WHERE id = %(aid)s",
                {"pid": pa_id, "aid": int(fid)},
            )


def insert_submitted_log(*, pa_id: int, user_id: int) -> None:
    execute(
        """
        INSERT INTO payment_application_log
            (content, paymentId, userId, addTime, deleteStatus)
        VALUES ('申请已提交', %(pid)s, %(uid)s, NOW(), 0)
        """,
        {"pid": pa_id, "uid": str(user_id)},
    )
