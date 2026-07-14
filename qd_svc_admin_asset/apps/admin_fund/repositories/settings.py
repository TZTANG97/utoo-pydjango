from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one


def get_setting() -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            id, addTime, rmb_rate AS rmbRate, us_rate AS usRate,
            us_exchange_rate AS usExchangeRate
        FROM account_setting
        ORDER BY id ASC
        LIMIT 1
        """
    )


def save_rates(*, rmb_rate: int, us_rate: int) -> None:
    row = get_setting()
    if row:
        execute(
            """
            UPDATE account_setting
            SET rmb_rate = %(rmb_rate)s, us_rate = %(us_rate)s, addTime = NOW()
            WHERE id = %(id)s
            """,
            {"rmb_rate": rmb_rate, "us_rate": us_rate, "id": row["id"]},
        )
    else:
        execute_insert(
            """
            INSERT INTO account_setting (addTime, deleteStatus, rmb_rate, us_rate, us_exchange_rate)
            VALUES (NOW(), 0, %(rmb_rate)s, %(us_rate)s, 1)
            """,
            {"rmb_rate": rmb_rate, "us_rate": us_rate},
        )


def save_exchange_rate(rate: Decimal | float | str) -> None:
    row = get_setting()
    if row:
        execute(
            """
            UPDATE account_setting
            SET us_exchange_rate = %(rate)s, addTime = NOW()
            WHERE id = %(id)s
            """,
            {"rate": rate, "id": row["id"]},
        )
    else:
        execute_insert(
            """
            INSERT INTO account_setting (addTime, deleteStatus, rmb_rate, us_rate, us_exchange_rate)
            VALUES (NOW(), 0, 0, 0, %(rate)s)
            """,
            {"rate": rate},
        )
