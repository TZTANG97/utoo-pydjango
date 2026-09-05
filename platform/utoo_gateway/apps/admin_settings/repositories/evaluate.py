from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, fetch_one


def get_evaluate_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, evaluate_time, evaluate_time_type
        FROM sysconfig
        WHERE id = 1
        LIMIT 1
        """
    )
    if not row:
        return {"id": 1, "evaluate_time": 0, "evaluate_time_type": 0}
    return row


def save_evaluate_setting(*, evaluate_time: int, evaluate_time_type: int) -> None:
    row = fetch_one("SELECT id FROM sysconfig WHERE id = 1 LIMIT 1")
    if row:
        execute(
            """
            UPDATE sysconfig
            SET evaluate_time = %(evaluate_time)s,
                evaluate_time_type = %(evaluate_time_type)s
            WHERE id = 1
            """,
            {
                "evaluate_time": evaluate_time,
                "evaluate_time_type": evaluate_time_type,
            },
        )
        return
    execute(
        """
        INSERT INTO sysconfig (id, evaluate_time, evaluate_time_type)
        VALUES (1, %(evaluate_time)s, %(evaluate_time_type)s)
        """,
        {
            "evaluate_time": evaluate_time,
            "evaluate_time_type": evaluate_time_type,
        },
    )
