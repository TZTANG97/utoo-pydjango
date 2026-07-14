from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, fetch_one


def get_integral_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT expireIntegralDay, integral_convert_ratio
        FROM sysconfig
        WHERE id = 1
        LIMIT 1
        """
    ) or {}
    return {
        "expireIntegralDay": row.get("expireIntegralDay") or 0,
        "integralConvertRatio": row.get("integral_convert_ratio") or 0,
    }


def save_expire_days(days: int) -> None:
    execute(
        "UPDATE sysconfig SET expireIntegralDay = %(days)s WHERE id = 1",
        {"days": days},
    )


def save_convert_ratio(ratio: float) -> None:
    execute(
        "UPDATE sysconfig SET integral_convert_ratio = %(ratio)s WHERE id = 1",
        {"ratio": ratio},
    )
