from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_one, scalar


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
        ORDER BY id DESC LIMIT 1
        """,
        {"oid": order_id},
    )


def soft_delete_yyd_attachments(order_id: int) -> int:
    """软删主单上旧预约单 PDF（type=6），便于重新生成后预览最新文件。"""
    if not order_id:
        return 0
    return int(
        execute(
            """
            UPDATE accessory
            SET deleteStatus = 1
            WHERE IFNULL(deleteStatus, 0) = 0
              AND exp_of_id = %(oid)s
              AND type = 6
            """,
            {"oid": order_id},
        )
        or 0
    )


def get_order_num(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
        {"oid": order_id},
    )


def soft_delete_accessory(accessory_id: int) -> bool:
    row = fetch_one(
        "SELECT id FROM accessory WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0 LIMIT 1",
        {"id": accessory_id},
    )
    if not row:
        return False
    execute(
        "UPDATE accessory SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": accessory_id},
    )
    return True


def insert_accessory(
    *,
    add_time,
    name: str,
    path: str,
    ext: str,
    info: str,
    acc_type: int,
    exp_of_id: int | None = None,
    child_of_id: int | None = None,
) -> int:
    params = {
        "t": add_time,
        "name": name,
        "path": path,
        "ext": ext,
        "info": info,
        "acc_type": acc_type,
        "exp_of_id": exp_of_id,
        "child_of_id": child_of_id,
    }
    if exp_of_id is not None and child_of_id is not None:
        try:
            return execute_insert(
                """
                INSERT INTO accessory
                    (addTime, deleteStatus, name, path, ext, info, type, exp_of_id, child_of_id)
                VALUES
                    (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s,
                     %(exp_of_id)s, %(child_of_id)s)
                """,
                params,
            )
        except Exception:
            pass
    if child_of_id is not None and exp_of_id is None:
        try:
            return execute_insert(
                """
                INSERT INTO accessory
                    (addTime, deleteStatus, name, path, ext, info, type, child_of_id)
                VALUES
                    (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s, %(child_of_id)s)
                """,
                params,
            )
        except Exception:
            pass
    if exp_of_id is not None:
        return execute_insert(
            """
            INSERT INTO accessory
                (addTime, deleteStatus, name, path, ext, info, type, exp_of_id)
            VALUES
                (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s, %(exp_of_id)s)
            """,
            params,
        )
    return execute_insert(
        """
        INSERT INTO accessory
            (addTime, deleteStatus, name, path, ext, info, type)
        VALUES
            (%(t)s, 0, %(name)s, %(path)s, %(ext)s, %(info)s, %(acc_type)s)
        """,
        params,
    )
