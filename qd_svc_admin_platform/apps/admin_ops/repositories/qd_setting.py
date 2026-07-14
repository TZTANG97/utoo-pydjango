from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, fetch_one


SETTING_COLUMNS = {
    "rent": "rent_device",
    "secondhand": "secondhand_device",
    "deviceservice": "device_service",
    "product": "prodct_test",
    "business": "business_support",
}


def get_setting() -> dict[str, Any] | None:
    return fetch_one("SELECT * FROM qd_setting WHERE id = 1 LIMIT 1")


def update_setting_field(setting_type: str, content: str) -> bool:
    column = SETTING_COLUMNS.get(setting_type)
    if not column:
        return False
    execute(
        f"UPDATE qd_setting SET `{column}` = %(content)s WHERE id = 1",
        {"content": content},
    )
    return True
