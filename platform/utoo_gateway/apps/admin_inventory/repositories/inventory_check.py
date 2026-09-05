from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

CHECK_STATUS_LABELS = {1: "盘点中", 2: "已盘点"}


def list_inventory_checks(
    *,
    check_id: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    sy_user_id: str = "",
    storehouse_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE IFNULL(gic.deleteStatus, 0) = 0"
    params: dict[str, Any] = {}
    if check_id:
        where += " AND gic.check_id LIKE %(check_id)s"
        params["check_id"] = f"%{check_id}%"
    if sy_user_id:
        where += " AND gic.sy_user_id = %(sy_user_id)s"
        params["sy_user_id"] = sy_user_id
    if storehouse_id:
        where += " AND gic.storehouse_id = %(storehouse_id)s"
        params["storehouse_id"] = storehouse_id
    if order_startime:
        where += " AND gic.check_start_time >= %(order_startime)s"
        params["order_startime"] = order_startime
    if order_endtime:
        where += " AND gic.check_end_time <= %(order_endtime)s"
        params["order_endtime"] = f"{order_endtime} 23:59:59" if len(order_endtime) <= 10 else order_endtime

    from_sql = f"""
        FROM good_inventory_check gic
        LEFT JOIN goods_storehouse h ON gic.storehouse_id = h.id
        LEFT JOIN sy_users u ON gic.sy_user_id = u.id
        {where}
    """
    total = int(scalar(f"SELECT COUNT(*) {from_sql}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            gic.id, gic.check_id AS checkId, gic.check_id,
            gic.check_start_time AS checkStartTime,
            gic.check_end_time AS checkEndTime,
            gic.check_status AS checkStatus,
            gic.storehouse_id AS storehouseId,
            gic.sy_user_id AS syUserId,
            gic.selectTime,
            h.store_name AS storeName,
            u.user_name AS userName, u.true_name AS trueName
        {from_sql}
        ORDER BY gic.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        st = int(row.get("checkStatus") or 0)
        row["checkStatusLabel"] = CHECK_STATUS_LABELS.get(st, str(st) if st else "-")
        row["userName"] = row.get("trueName") or row.get("userName") or ""
    return rows, total


def get_store_num(storehouse_id: int) -> str:
    row = fetch_one(
        "SELECT store_num FROM goods_storehouse WHERE id = %(id)s LIMIT 1",
        {"id": storehouse_id},
    )
    return str((row or {}).get("store_num") or "")


def create_inventory_check(*, storehouse_id: int, select_time: str, sy_user_id: str) -> int:
    store_num = get_store_num(storehouse_id)
    check_id = f"{store_num}PD{select_time.replace('-', '')}"
    return execute_insert(
        """
        INSERT INTO good_inventory_check
            (addTime, deleteStatus, check_id, check_start_time, sy_user_id,
             check_status, storehouse_id, selectTime)
        VALUES
            (NOW(), 0, %(check_id)s, NOW(), %(sy_user_id)s, 1, %(storehouse_id)s, %(select_time)s)
        """,
        {
            "check_id": check_id,
            "sy_user_id": sy_user_id,
            "storehouse_id": storehouse_id,
            "select_time": select_time,
        },
    )


def delete_inventory_check(check_pk: int) -> None:
    execute(
        "UPDATE good_inventory_check SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": check_pk},
    )
