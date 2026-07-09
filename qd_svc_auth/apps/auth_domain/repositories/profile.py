from typing import Any

from apps.core.db_utils import execute, fetch_one


def get_exp_user(user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT * FROM exp_user WHERE id = %(uid)s AND deleteStatus = 0 LIMIT 1",
        {"uid": user_id},
    )


def get_district_parent(district_id: str) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, super_id FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": district_id},
    )


def get_accessory_photo(photo_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT path, name FROM accessory
        WHERE id = %(aid)s AND deleteStatus = 0 LIMIT 1
        """,
        {"aid": photo_id},
    )


def update_exp_user_fields(user_id: int, sets: list[str], params: dict[str, Any]) -> int:
    sql = f"UPDATE exp_user SET {', '.join(sets)} WHERE id = %(uid)s"
    params["uid"] = user_id
    return execute(sql, params)
