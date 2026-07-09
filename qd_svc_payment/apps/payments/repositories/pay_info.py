from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db import connection

from apps.core import redis_client
from apps.core.db_utils import execute, execute_insert, fetch_one
from apps.payments.repositories.pay_order_code import order_num_generate, payment_pa_num_generate

logger = logging.getLogger(__name__)

PAY_PENDING_TIMEOUT_MINUTES = 15


def create_pay_info_log(
    *,
    user_id: int,
    money: Decimal,
    pay_type: int,
    pay_way: int = 2,
    order_id: str = "",
    use_integral: Decimal = Decimal("0"),
    integral_money: Decimal = Decimal("0"),
    fkjes: str = "",
) -> int:
    pa_num = payment_pa_num_generate(str(pay_type))
    return execute_insert(
        """
        INSERT INTO pay_info_log
            (addTime, deleteStatus, user_id, money, status, order_id,
             pay_type, pay_way, pa_num, use_integral, integral_money, fkjes)
        VALUES
            (NOW(), 1, %(uid)s, %(money)s, 1, %(order_id)s,
             %(pay_type)s, %(pay_way)s, %(pa_num)s, %(use_integral)s,
             %(integral_money)s, %(fkjes)s)
        """,
        {
            "uid": user_id,
            "money": float(money),
            "order_id": order_id or "",
            "pay_type": pay_type,
            "pay_way": pay_way,
            "pa_num": pa_num,
            "use_integral": float(use_integral),
            "integral_money": float(integral_money),
            "fkjes": fkjes or "",
        },
    )


def link_exp_pay_order_num(*, pay_log_id: int, out_trade_no: str, num_type: int = 3) -> None:
    execute(
        """
        INSERT INTO exp_pay_order_num (addTime, order_id, order_num, type)
        VALUES (NOW(), %(pid)s, %(onum)s, %(typ)s)
        """,
        {"pid": pay_log_id, "onum": out_trade_no, "typ": num_type},
    )


def new_out_trade_no(pay_log_id: int, gen_type: int) -> str:
    out_no = order_num_generate(gen_type)
    link_exp_pay_order_num(pay_log_id=pay_log_id, out_trade_no=out_no)
    return out_no


def find_pay_order_by_out_trade_no(out_trade_no: str) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT * FROM exp_pay_order_num WHERE order_num = %(onum)s LIMIT 1",
        {"onum": out_trade_no},
    )


def get_pay_info_log(log_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT * FROM pay_info_log WHERE id = %(id)s LIMIT 1",
        {"id": log_id},
    )


def lock_pay_info_log_for_update(log_id: int) -> dict[str, Any] | None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT * FROM pay_info_log WHERE id = %(id)s LIMIT 1 FOR UPDATE",
            {"id": int(log_id)},
        )
        if not cur.description:
            return None
        cols = [c[0] for c in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def update_pay_order_transaction(epo_id: int, transaction_id: str) -> None:
    execute(
        "UPDATE exp_pay_order_num SET transaction_id = %(tid)s WHERE id = %(id)s",
        {"tid": transaction_id, "id": epo_id},
    )


def mark_pay_info_paid_if_pending(log_id: int) -> bool:
    return (
        execute(
            """
            UPDATE pay_info_log
            SET status = 2, deleteStatus = 0, payTime = NOW()
            WHERE id = %(id)s AND status = 1
            """,
            {"id": log_id},
        )
        > 0
    )


def _pay_native_cache_key(pay_log_id: int) -> str:
    return f"pay_native:{pay_log_id}"


def cache_pay_native_payload(pay_log_id: int, payload: dict[str, Any]) -> None:
    redis_client.cache_json(
        _pay_native_cache_key(pay_log_id),
        payload,
        ex=PAY_PENDING_TIMEOUT_MINUTES * 60,
    )


def get_cached_pay_native_payload(pay_log_id: int) -> dict[str, Any] | None:
    return redis_client.get_cached_json(_pay_native_cache_key(pay_log_id))


def get_out_trade_no_for_pay_log(pay_log_id: int) -> str | None:
    row = fetch_one(
        """
        SELECT order_num FROM exp_pay_order_num
        WHERE order_id = %(pid)s
        ORDER BY id DESC
        LIMIT 1
        """,
        {"pid": pay_log_id},
    )
    return str(row["order_num"]) if row and row.get("order_num") else None


def refresh_out_trade_no(pay_log_id: int, gen_type: int) -> str:
    out_no = order_num_generate(gen_type)
    row = fetch_one(
        """
        SELECT id FROM exp_pay_order_num
        WHERE order_id = %(pid)s
        ORDER BY id DESC
        LIMIT 1
        """,
        {"pid": pay_log_id},
    )
    if row:
        execute(
            "UPDATE exp_pay_order_num SET order_num = %(onum)s WHERE id = %(id)s",
            {"onum": out_no, "id": int(row["id"])},
        )
    else:
        link_exp_pay_order_num(pay_log_id=pay_log_id, out_trade_no=out_no)
    return out_no


def pay_log_close_at(add_time: Any) -> datetime | None:
    if not add_time:
        return None
    if isinstance(add_time, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                add_time = datetime.strptime(add_time[:19], fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if not isinstance(add_time, datetime):
        return None
    return add_time + timedelta(minutes=PAY_PENDING_TIMEOUT_MINUTES)


def pay_log_remaining_seconds(add_time: Any) -> int:
    close_at = pay_log_close_at(add_time)
    if not close_at:
        return 0
    return max(0, int((close_at - datetime.now()).total_seconds()))


def save_exp_user_log(user_id: int, info: str) -> None:
    execute(
        """
        INSERT INTO exp_user_log (addTime, deleteStatus, user_id, info)
        VALUES (NOW(), 0, %(uid)s, %(info)s)
        """,
        {"uid": user_id, "info": info},
    )
