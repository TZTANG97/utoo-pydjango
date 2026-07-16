from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar

# 在库相关（可占用）
AVAILABLE_STATUSES = (1, 5, 6, 7, 11, 12, 13, 17, 18)
# 总数量统计排除：已售/报废/销售出库/无订单销售出库
TOTAL_EXCLUDE_STATUSES = (3, 4, 21, 16)

GI_STATUS_LABELS = {
    1: "在库",
    2: "已租",
    3: "已售",
    4: "已报废",
    5: "租赁锁定",
    6: "其他出库锁定",
    7: "销售锁定",
    10: "借调出库",
    11: "采购入库",
    12: "租赁归还入库",
    13: "其他入库",
    14: "租赁出库",
    15: "其他出库",
    16: "销售出库",
    17: "借调入库",
    18: "维修入库",
    19: "维修出库",
    21: "无订单销售出库",
    22: "调租出库",
    23: "在途",
}


def status_label(code: Any) -> str:
    try:
        return GI_STATUS_LABELS.get(int(code), str(code or ""))
    except (TypeError, ValueError):
        return str(code or "")


def _statis_filters(
    *,
    goods_name: str,
    goods_spec: str,
    serial_number: str,
    expmanage_line_id: str,
    private_lease_type: str,
    list_type: str,
) -> tuple[str, dict[str, Any]]:
    where = """
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND t.inventory_type != 0
          AND IFNULL(m.name, '') != ''
          AND EXISTS (SELECT 1 FROM goods g WHERE g.id = t.goods_id)
    """
    params: dict[str, Any] = {}
    if goods_name:
        where += " AND t.goods_name LIKE %(goods_name)s"
        params["goods_name"] = f"%{goods_name}%"
    if goods_spec:
        where += " AND t.goods_spec LIKE %(goods_spec)s"
        params["goods_spec"] = f"%{goods_spec}%"
    if serial_number:
        where += " AND t.serial_number LIKE %(serial_number)s"
        params["serial_number"] = f"%{serial_number}%"
    if expmanage_line_id:
        where += " AND CAST(t.expmanage_line_id AS CHAR) LIKE %(expmanage_line_id)s"
        params["expmanage_line_id"] = f"%{expmanage_line_id}%"
    if private_lease_type:
        where += " AND m.name = %(private_lease_type)s"
        params["private_lease_type"] = private_lease_type
    if list_type == "1":
        where += f" AND t.gi_status IN ({','.join(str(x) for x in AVAILABLE_STATUSES)})"
    elif list_type == "2":
        where += " AND t.gi_status IN (2,14,15,16,19,10,21,22)"
    elif list_type == "3":
        where += " AND t.gi_status = 23"
    return where, params


def list_inventory_statis(
    *,
    goods_name: str = "",
    goods_spec: str = "",
    serial_number: str = "",
    expmanage_line_id: str = "",
    private_lease_type: str = "",
    list_type: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java inventoryStatis：按 goods_id + brand + spec 聚合。"""
    where, params = _statis_filters(
        goods_name=goods_name,
        goods_spec=goods_spec,
        serial_number=serial_number,
        expmanage_line_id=expmanage_line_id,
        private_lease_type=private_lease_type,
        list_type=list_type,
    )
    avail = ",".join(str(x) for x in AVAILABLE_STATUSES)
    exclude = ",".join(str(x) for x in TOTAL_EXCLUDE_STATUSES)

    total = int(
        scalar(
            f"""
            SELECT COUNT(*) FROM (
                SELECT t.goods_id, t.goods_brand_id, t.goods_spec
                FROM goods_inventory t
                LEFT JOIN experiment_manage m ON t.expmanage_id = m.id
                LEFT JOIN (
                    SELECT id, inventory_num
                    FROM goods_inventory
                    WHERE gi_status NOT IN ({exclude})
                ) t1 ON t.id = t1.id
                {where}
                  AND IFNULL(t1.inventory_num, 0) > 0
                GROUP BY t.goods_id, t.goods_brand_id, t.goods_spec
            ) g
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            MIN(t.id) AS id,
            t.goods_id AS goodsId,
            t.goods_brand_id AS goodsBrandId,
            MAX(IFNULL(good.goods_name, t.goods_name)) AS goodsName,
            MAX(t.goods_brand_name) AS goodsBrandName,
            t.goods_spec AS goodsSpec,
            IFNULL(SUM(tt.inventory_num), 0) AS nums,
            IFNULL(SUM(t1.inventory_num), 0) AS totalnum,
            MAX(t2.zlckj) AS zlckj,
            MAX(t.nbzlj) AS nbzlj,
            MAX(t.produce_time) AS produceTime,
            GROUP_CONCAT(DISTINCT NULLIF(l.line_num, '') SEPARATOR ', ') AS lineNum,
            GROUP_CONCAT(DISTINCT NULLIF(t.serial_number, '') SEPARATOR ', ') AS serialNumber,
            GROUP_CONCAT(DISTINCT NULLIF(t.inventory_id, '') SEPARATOR ', ') AS inventoryId
        FROM goods_inventory t
        LEFT JOIN (
            SELECT id, inventory_num
            FROM goods_inventory
            WHERE gi_status IN ({avail})
        ) tt ON t.id = tt.id
        LEFT JOIN (
            SELECT id, inventory_num
            FROM goods_inventory
            WHERE gi_status NOT IN ({exclude})
        ) t1 ON t.id = t1.id
        LEFT JOIN (
            SELECT goods_spec, MAX(zlckj) AS zlckj
            FROM goods_inventory
            WHERE gi_status NOT IN ({exclude})
            GROUP BY goods_spec
        ) t2 ON t.goods_spec = t2.goods_spec
        LEFT JOIN goods good ON t.goods_id = good.id
        LEFT JOIN experiment_manage m ON t.expmanage_id = m.id
        LEFT JOIN experiment_line l ON CAST(t.expmanage_line_id AS CHAR) = CAST(l.id AS CHAR)
        {where}
          AND IFNULL(t1.inventory_num, 0) > 0
        GROUP BY t.goods_id, t.goods_brand_id, t.goods_spec
        ORDER BY MAX(t.addTime) DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_inventory_children(
    *,
    goods_id: str,
    goods_brand_id: str = "",
    goods_spec: str = "",
    serial_number: str = "",
    private_lease_type: str = "",
    expmanage_line_id: str = "",
) -> list[dict[str, Any]]:
    where = """
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND t.gi_status NOT IN (3, 4, 21, 16)
          AND t.goods_id = %(goods_id)s
    """
    params: dict[str, Any] = {"goods_id": goods_id}
    if goods_brand_id not in ("", None):
        where += " AND t.goods_brand_id = %(goods_brand_id)s"
        params["goods_brand_id"] = goods_brand_id
    if goods_spec not in ("", None):
        where += " AND IFNULL(t.goods_spec, '') = %(goods_spec)s"
        params["goods_spec"] = goods_spec
    if serial_number:
        where += " AND t.serial_number LIKE %(serial_number)s"
        params["serial_number"] = f"%{serial_number}%"
    if private_lease_type:
        where += " AND m.name = %(private_lease_type)s"
        params["private_lease_type"] = private_lease_type
    if expmanage_line_id:
        where += " AND CAST(t.expmanage_line_id AS CHAR) LIKE %(expmanage_line_id)s"
        params["expmanage_line_id"] = f"%{expmanage_line_id}%"

    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.inventory_id AS inventoryId, t.goods_id AS goodsId,
            IFNULL(good.goods_name, t.goods_name) AS goodsName,
            t.serial_number AS serialNumber, t.goods_spec AS goodsSpec,
            t.goods_price AS goodsPrice, t.inventory_num AS inventoryNum,
            t.goods_brand_id AS goodsBrandId, t.goods_brand_name AS goodsBrandName,
            t.old_or_new AS oldOrNew, t.store_id AS storeId, t.company_id AS companyId,
            t.mark, t.gi_status AS giStatus, t.inventory_type AS inventoryType,
            t.reference_price AS referencePrice, t.zlckj, t.nbzlj,
            t.produce_time AS produceTime, t.expmanage_id AS expmanageId,
            t.expmanage_line_id AS expmanageLineId,
            s.store_name AS storeName, u.company_name AS companyName,
            m.name AS expmanageName, l.line_num AS lineNum,
            CONCAT(IFNULL(b.block, ''), IFNULL(p.number, '')) AS storePosition
        FROM goods_inventory t
        LEFT JOIN goods good ON t.goods_id = good.id
        LEFT JOIN goods_storehouse s ON t.store_id = s.id
        LEFT JOIN user u ON t.company_id = u.id
        LEFT JOIN experiment_manage m ON t.expmanage_id = m.id
        LEFT JOIN experiment_line l ON CAST(t.expmanage_line_id AS CHAR) = CAST(l.id AS CHAR)
        LEFT JOIN goods_store_position p ON t.store_position_id = p.id
        LEFT JOIN goods_store_block b ON p.block_id = b.id
        {where}
        ORDER BY t.addTime DESC
        """,
        params,
    )
    for row in rows:
        row["giStatusLabel"] = status_label(row.get("giStatus"))
    return rows


def inventory_summary() -> dict[str, Any]:
    """UT实验租用总数量 + 筛选项。"""
    ut_count = int(
        scalar(
            """
            SELECT COUNT(*)
            FROM goods_inventory t
            INNER JOIN experiment_manage m ON t.expmanage_id = m.id
            WHERE IFNULL(t.deleteStatus, 0) = 0
              AND IFNULL(m.name, '') != ''
            """
        )
        or 0
    )
    lease_options = fetch_all(
        """
        SELECT DISTINCT m.name AS name
        FROM goods_inventory t
        INNER JOIN experiment_manage m ON t.expmanage_id = m.id
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND IFNULL(m.name, '') != ''
        ORDER BY m.name ASC
        LIMIT 200
        """
    )
    lines = fetch_all(
        """
        SELECT id, line_num AS lineNum
        FROM experiment_line
        WHERE IFNULL(deleteStatus, 0) = 0 AND status = 1
        ORDER BY line_num ASC
        LIMIT 500
        """
    )
    return {
        "inventorynum": ut_count,
        "leaseOptions": [r.get("name") for r in lease_options if r.get("name")],
        "expLines": lines,
        "statusOptions": [{"value": k, "label": v} for k, v in sorted(GI_STATUS_LABELS.items())],
    }


def list_inventory(
    *,
    goods_name: str = "",
    store_name: str = "",
    inventory_id: str = "",
    serial_number: str = "",
    gi_status: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """扁平列表（兼容旧接口）。"""
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0"
    params: dict[str, Any] = {}
    if goods_name:
        where += " AND t.goods_name LIKE %(goods_name)s"
        params["goods_name"] = f"%{goods_name}%"
    if store_name:
        where += " AND s.store_name LIKE %(store_name)s"
        params["store_name"] = f"%{store_name}%"
    if inventory_id:
        where += " AND t.inventory_id LIKE %(inventory_id)s"
        params["inventory_id"] = f"%{inventory_id}%"
    if serial_number:
        where += " AND t.serial_number LIKE %(serial_number)s"
        params["serial_number"] = f"%{serial_number}%"
    if gi_status == "1":
        where += f" AND t.gi_status IN ({','.join(str(x) for x in AVAILABLE_STATUSES)})"
    elif gi_status != "":
        where += " AND t.gi_status = %(gi_status)s"
        params["gi_status"] = gi_status

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM goods_inventory t
            LEFT JOIN goods_storehouse s ON t.store_id = s.id
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
            t.id, t.addTime, t.inventory_id AS inventoryId, t.goods_id AS goodsId,
            t.goods_name AS goodsName, t.serial_number AS serialNumber,
            t.goods_spec AS goodsSpec, t.goods_price AS goodsPrice,
            t.inventory_num AS inventoryNum, t.goods_brand_name AS goodsBrandName,
            t.old_or_new AS oldOrNew, t.store_id AS storeId, t.company_id AS companyId,
            t.mark, t.gi_status AS giStatus, t.inventory_type AS inventoryType,
            t.reference_price AS referencePrice, t.zlckj, t.nbzlj,
            t.produce_time AS produceTime,
            s.store_name AS storeName, u.company_name AS companyName
        FROM goods_inventory t
        LEFT JOIN goods_storehouse s ON t.store_id = s.id
        LEFT JOIN user u ON t.company_id = u.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        row["giStatusLabel"] = status_label(row.get("giStatus"))
    return rows, total


def get_inventory(inventory_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.inventory_id AS inventoryId, t.goods_id AS goodsId,
            t.goods_name AS goodsName, t.serial_number AS serialNumber,
            t.goods_spec AS goodsSpec, t.goods_price AS goodsPrice,
            t.inventory_num AS inventoryNum, t.goods_brand_name AS goodsBrandName,
            t.old_or_new AS oldOrNew, t.store_id AS storeId, t.company_id AS companyId,
            t.mark, t.gi_status AS giStatus, t.inventory_type AS inventoryType,
            t.reference_price AS referencePrice, t.zlckj, t.nbzlj,
            t.produce_time AS produceTime,
            s.store_name AS storeName
        FROM goods_inventory t
        LEFT JOIN goods_storehouse s ON t.store_id = s.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": inventory_id},
    )
    if row:
        row["giStatusLabel"] = status_label(row.get("giStatus"))
    return row


def update_inventory(row_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE goods_inventory
        SET store_id = %(store_id)s,
            serial_number = %(serial_number)s,
            inventory_num = %(inventory_num)s,
            gi_status = %(gi_status)s,
            goods_price = %(goods_price)s,
            mark = %(mark)s,
            zlckj = %(zlckj)s,
            nbzlj = %(nbzlj)s,
            produce_time = %(produce_time)s
        WHERE id = %(id)s
        """,
        {**data, "id": row_id},
    )


def soft_delete_inventory(row_id: int) -> None:
    execute(
        "UPDATE goods_inventory SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )
