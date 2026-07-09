from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, fetch_one


def fetch_by_user_id(user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT * FROM user_account
        WHERE delete_status = 0 AND user_id = %(uid)s LIMIT 1
        """,
        {"uid": user_id},
    )


def insert_default(user_id: int) -> None:
    execute(
        """
        INSERT INTO user_account
            (add_time, update_time, delete_status, user_id,
             amount, arrear_amount, invoicing_amount, invoiced_amount,
             prestore_amount, total_prestore_amount, total_amount, credit_quota)
        VALUES (NOW(), NOW(), 0, %(uid)s, 0,0,0,0,0,0,0,0)
        """,
        {"uid": user_id},
    )


def get_or_create(user_id: int) -> dict[str, Any]:
    row = fetch_by_user_id(user_id)
    if row:
        return row
    insert_default(user_id)
    return fetch_by_user_id(user_id) or {}
