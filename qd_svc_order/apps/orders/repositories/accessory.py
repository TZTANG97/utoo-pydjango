from typing import Any

from apps.core.db_utils import execute_insert, fetch_one, scalar


def get_order_type(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, order_type FROM experiment_order WHERE id = %(oid)s LIMIT 1",
        {"oid": order_id},
    )


def count_order_accessories(order_id: int) -> int:
    return int(
        scalar(
            """
            SELECT COUNT(1) FROM accessory
            WHERE deleteStatus = 0 AND exp_of_id = %(oid)s
            """,
            {"oid": order_id},
            0,
        )
        or 0
    )


def get_yyd_attachment(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT path, name FROM accessory
        WHERE deleteStatus = 0 AND exp_of_id = %(oid)s AND type = 6
        ORDER BY id ASC LIMIT 1
        """,
        {"oid": order_id},
    )


def get_order_num(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
        {"oid": order_id},
    )


def insert_accessory(
    *,
    add_time,
    name: str,
    path: str,
    ext: str,
    info: str,
    acc_type: int,
    exp_of_id: int | None = None,
) -> int:
    if exp_of_id is not None:
        return execute_insert(
            """
            INSERT INTO accessory
                (addTime, deleteStatus, name, path, ext, info, type, exp_of_id)
            VALUES
                (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s, %(exp_of_id)s)
            """,
            {
                "t": add_time,
                "name": name,
                "path": path,
                "ext": ext,
                "info": info,
                "acc_type": acc_type,
                "exp_of_id": exp_of_id,
            },
        )
    return execute_insert(
        """
        INSERT INTO accessory
            (addTime, deleteStatus, name, path, ext, info, type)
        VALUES
            (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s)
        """,
        {
            "t": add_time,
            "name": name,
            "path": path,
            "ext": ext,
            "info": info,
            "acc_type": acc_type,
        },
    )
