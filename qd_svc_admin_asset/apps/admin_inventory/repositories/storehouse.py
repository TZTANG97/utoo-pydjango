from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_storehouses(
    *,
    store_name: str = "",
    true_name: str = "",
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if store_name:
        where += " AND t.store_name LIKE %(store_name)s"
        params["store_name"] = f"%{store_name}%"
    if true_name:
        where += " AND u.user_name LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if mobile:
        where += " AND t.moblie LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM goods_storehouse t
            LEFT JOIN sy_users u ON t.store_userid = u.id
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.store_num AS storeNum, t.store_name AS storeName,
            t.store_userid AS storeUserid, t.moblie, t.address, t.mark, t.status,
            u.user_name AS userName, u.true_name AS trueName
        FROM goods_storehouse t
        LEFT JOIN sy_users u ON t.store_userid = u.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_storehouse(store_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.store_num AS storeNum, t.store_name AS storeName,
            t.store_userid AS storeUserid, t.moblie, t.address, t.mark, t.status,
            u.user_name AS userName, u.true_name AS trueName
        FROM goods_storehouse t
        LEFT JOIN sy_users u ON t.store_userid = u.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": store_id},
    )


def insert_storehouse(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO goods_storehouse
            (addTime, deleteStatus, store_num, store_name, store_userid, moblie, address, mark, status)
        VALUES
            (NOW(), 0, %(store_num)s, %(store_name)s, %(store_userid)s, %(moblie)s, %(address)s, %(mark)s, %(status)s)
        """,
        data,
    )


def update_storehouse(store_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE goods_storehouse
        SET store_num = %(store_num)s,
            store_name = %(store_name)s,
            store_userid = %(store_userid)s,
            moblie = %(moblie)s,
            address = %(address)s,
            mark = %(mark)s,
            status = %(status)s
        WHERE id = %(id)s
        """,
        {**data, "id": store_id},
    )


def set_storehouse_status(store_id: int, status: int) -> None:
    execute(
        "UPDATE goods_storehouse SET status = %(status)s WHERE id = %(id)s",
        {"id": store_id, "status": status},
    )


def soft_delete_storehouse(store_id: int) -> None:
    execute(
        "UPDATE goods_storehouse SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": store_id},
    )


def list_sample_storehouses(
    *,
    store_type: int,
    store_name: str = "",
    true_name: str = "",
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0 AND t.type = %(type)s"
    params: dict[str, Any] = {"type": store_type}
    if store_name:
        where += " AND t.sample_store_name LIKE %(store_name)s"
        params["store_name"] = f"%{store_name}%"
    if true_name:
        where += " AND (u.true_name LIKE %(true_name)s OR u.user_name LIKE %(true_name)s)"
        params["true_name"] = f"%{true_name}%"
    if mobile:
        where += " AND t.moblie LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM sample_goods_storehouse t
            LEFT JOIN sy_users u ON t.store_userid = u.id
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.sample_store_num AS storeNum, t.sample_store_name AS storeName,
            t.store_userid AS storeUserid, t.moblie, t.address, t.mark, t.status, t.type,
            u.user_name AS userName, u.true_name AS trueName
        FROM sample_goods_storehouse t
        LEFT JOIN sy_users u ON t.store_userid = u.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_sample_storehouse(store_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.sample_store_num AS storeNum, t.sample_store_name AS storeName,
            t.store_userid AS storeUserid, t.moblie, t.address, t.mark, t.status, t.type,
            u.user_name AS userName, u.true_name AS trueName
        FROM sample_goods_storehouse t
        LEFT JOIN sy_users u ON t.store_userid = u.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": store_id},
    )


def insert_sample_storehouse(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO sample_goods_storehouse
            (addTime, deleteStatus, sample_store_num, sample_store_name, store_userid,
             moblie, address, mark, status, type)
        VALUES
            (NOW(), 0, %(store_num)s, %(store_name)s, %(store_userid)s,
             %(moblie)s, %(address)s, %(mark)s, %(status)s, %(type)s)
        """,
        data,
    )


def update_sample_storehouse(store_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sample_goods_storehouse
        SET sample_store_num = %(store_num)s,
            sample_store_name = %(store_name)s,
            store_userid = %(store_userid)s,
            moblie = %(moblie)s,
            address = %(address)s,
            mark = %(mark)s,
            status = %(status)s
        WHERE id = %(id)s
        """,
        {**data, "id": store_id},
    )


def set_sample_storehouse_status(store_id: int, status: int) -> None:
    execute(
        "UPDATE sample_goods_storehouse SET status = %(status)s WHERE id = %(id)s",
        {"id": store_id, "status": status},
    )


def soft_delete_sample_storehouse(store_id: int) -> None:
    execute(
        "UPDATE sample_goods_storehouse SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": store_id},
    )
