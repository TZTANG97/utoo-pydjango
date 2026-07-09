from typing import Any

from apps.core.db_utils import execute_insert, fetch_all, fetch_one


def get_consult_by_order_id(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT * FROM service_consult
        WHERE order_id = %(oid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"oid": order_id},
    )


def get_order_brief(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
        {"oid": order_id},
    )


def insert_row(table: str, row: dict[str, Any], *, skip: set[str]) -> int:
    data = {k: v for k, v in row.items() if k not in skip and v is not None}
    if not data:
        raise ValueError(f"no columns to insert into {table}")
    cols = ", ".join(data.keys())
    placeholders = ", ".join(f"%({k})s" for k in data.keys())
    return execute_insert(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
        data,
    )


def list_consult_children(consult_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM service_consult_child WHERE consult_id = %(cid)s",
        {"cid": consult_id},
    )


def get_sample_by_id(sample_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT * FROM order_sample_information WHERE id = %(sid)s LIMIT 1",
        {"sid": sample_id},
    )
