from typing import Any

from apps.core.db_utils import fetch_all, fetch_one


def list_attribute_states() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM attribute_state
        WHERE deleteStatus = 0
        ORDER BY addTime DESC
        """
    )


def list_stability_rows() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM stability
        WHERE deleteStatus = 0
        ORDER BY addTime DESC
        """
    )


def get_attribute_root(special_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT * FROM sample_attribute_manage
        WHERE deleteStatus = 0 AND special_id = %(sid)s
        ORDER BY addTime DESC
        LIMIT 1
        """,
        {"sid": special_id},
    )


def list_attribute_children(parent_id: int, *, level: int) -> list[dict[str, Any]]:
    if level == 2:
        sql = """
            SELECT sttribute_name AS name, id, parent_id, type, selection
            FROM sample_attribute_manage
            WHERE type = 2 AND parent_id = %(pid)s
        """
    else:
        sql = """
            SELECT sttribute_name AS name, id, parent_id, type
            FROM sample_attribute_manage
            WHERE type = 3 AND parent_id = %(pid)s
        """
    return fetch_all(sql, {"pid": parent_id})
