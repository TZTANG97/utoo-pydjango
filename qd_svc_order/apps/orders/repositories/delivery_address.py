from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one


def get_district_name(district_id: str) -> str:
    row = fetch_one(
        "SELECT dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": district_id},
    )
    return (row.get("dis_name") or "") if row else ""


def list_delivery_addresses(user_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM exp_user_delivery_address
        WHERE user_id = %(uid)s AND deleteStatus = 0
        ORDER BY is_default DESC, addTime DESC
        """,
        {"uid": user_id},
    )


def get_user_address_info(user_id: int) -> str:
    row = fetch_one(
        "SELECT address_info FROM exp_user WHERE id = %(uid)s LIMIT 1",
        {"uid": user_id},
    )
    return (row.get("address_info") or "") if row else ""


def count_user_addresses(user_id: int) -> int:
    row = fetch_one(
        """
        SELECT COUNT(1) AS c FROM exp_user_delivery_address
        WHERE user_id = %(uid)s AND deleteStatus = 0
        """,
        {"uid": user_id},
    )
    return int(row["c"]) if row else 0


def insert_delivery_address_row(
    *,
    add_time,
    user_id: int,
    delivery_name: str,
    delivery_phone: str,
    addr_text: str,
    detail_address: str,
    addr_ids: str,
    is_default: int,
) -> int:
    return execute_insert(
        """
        INSERT INTO exp_user_delivery_address
            (addTime, deleteStatus, delivery_address, delivery_name,
             delivery_phone, detail_address, delivery_address_id,
             user_id, is_default)
        VALUES
            (%(add_time)s, 0, %(addr)s, %(name)s, %(phone)s, %(detail)s,
             %(addr_id)s, %(uid)s, %(is_default)s)
        """,
        {
            "add_time": add_time,
            "addr": addr_text,
            "name": delivery_name,
            "phone": delivery_phone,
            "detail": detail_address,
            "addr_id": addr_ids,
            "uid": user_id,
            "is_default": is_default,
        },
    )


def get_owned_address(record_id: int, user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, is_default FROM exp_user_delivery_address
        WHERE id = %(rid)s AND user_id = %(uid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"rid": record_id, "uid": user_id},
    )


def update_delivery_address_row(
    *,
    record_id: int,
    user_id: int,
    delivery_name: str,
    delivery_phone: str,
    addr_text: str,
    detail_address: str,
    addr_ids: str,
) -> int:
    return execute(
        """
        UPDATE exp_user_delivery_address SET
            delivery_name = %(name)s,
            delivery_phone = %(phone)s,
            delivery_address = %(addr)s,
            detail_address = %(detail)s,
            delivery_address_id = %(addr_id)s
        WHERE id = %(rid)s AND user_id = %(uid)s
        """,
        {
            "rid": record_id,
            "uid": user_id,
            "name": delivery_name,
            "phone": delivery_phone,
            "addr": addr_text,
            "detail": detail_address,
            "addr_id": addr_ids,
        },
    )


def soft_delete_address(record_id: int) -> int:
    return execute(
        "UPDATE exp_user_delivery_address SET deleteStatus = 1 WHERE id = %(rid)s",
        {"rid": record_id},
    )


def clear_default_addresses(user_id: int) -> int:
    return execute(
        """
        UPDATE exp_user_delivery_address SET is_default = 0
        WHERE user_id = %(uid)s AND deleteStatus = 0 AND is_default = 1
        """,
        {"uid": user_id},
    )


def set_address_default(record_id: int) -> int:
    return execute(
        "UPDATE exp_user_delivery_address SET is_default = 1 WHERE id = %(rid)s",
        {"rid": record_id},
    )
