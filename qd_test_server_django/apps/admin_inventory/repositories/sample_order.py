from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import fetch_all, fetch_one, scalar

# 子单 got_status：与 Java 详情页一致
GOT_STATUS_LABEL = {
    1: "在库",
    2: "已领用",
    3: "寄回",
    4: "留存",
    5: "报废",
}


def _list_where(
    *,
    out_num: str = "",
    order_id: str = "",
    sj_out_time: str = "",
    store_id: str = "",
) -> tuple[str, dict[str, Any]]:
    """对齐 Java listPages：in_out_type=1 且 status != 3。"""
    where = "WHERE t.status != 3 AND t.in_out_type = 1"
    params: dict[str, Any] = {}
    if out_num:
        where += " AND t.out_num LIKE %(out_num)s"
        params["out_num"] = f"%{out_num}%"
    if order_id:
        where += " AND o.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if store_id:
        where += " AND t.store_id = %(store_id)s"
        params["store_id"] = store_id
    if sj_out_time:
        where += " AND DATE_FORMAT(t.sj_out_time, '%%Y-%%m-%%d') = %(sj_out_time)s"
        params["sj_out_time"] = sj_out_time[:10]
    return where, params


def list_sample_orders(
    *,
    out_num: str = "",
    order_id: str = "",
    sj_out_time: str = "",
    store_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where, params = _list_where(
        out_num=out_num,
        order_id=order_id,
        sj_out_time=sj_out_time,
        store_id=store_id,
    )
    # 与 Java 相同：按子表明细展开（一单多产品多行）
    from_sql = f"""
        FROM exp_goods_out_treasury t
        LEFT JOIN experiment_order o ON t.order_id = o.id
        LEFT JOIN sy_users u ON t.sale_user = u.id
        LEFT JOIN sample_goods_storehouse h ON t.store_id = h.id
        LEFT JOIN qd_user_company q ON t.customer_id = q.id
        LEFT JOIN exp_goods_out_treasury_child c ON t.id = c.out_id
        {where}
    """
    total = int(scalar(f"SELECT COUNT(*) {from_sql}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.out_num AS outNum, t.order_id AS orderId,
            t.store_id AS storeId, t.status, t.in_out_type AS inOutType, t.ftype,
            t.mark, t.sj_out_time AS sjOutTime, t.sj_out_time AS sj_out_time,
            o.order_id AS orderNum,
            h.sample_store_name AS storeName,
            h.sample_store_name AS store_name,
            u.user_name AS userName, u.true_name AS trueName,
            q.name AS customerName,
            c.goods_name AS goodsName,
            c.goods_name AS goods_name,
            c.goods_spec AS goodsSpec,
            c.goods_spec AS goods_spec,
            c.id AS childId,
            CASE WHEN o.order_status IS NOT NULL AND o.order_status < 30 AND t.ftype = 1
                 THEN 1 ELSE 0 END AS ists
        {from_sql}
        ORDER BY t.addTime DESC, c.id ASC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        row["ists"] = bool(int(row.get("ists") or 0))
    return rows, total


def get_sample_order(order_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.out_num AS outNum, t.order_id AS orderId,
            t.store_id AS storeId, t.status, t.in_out_type AS inOutType, t.ftype,
            t.mark, t.sale_user AS saleUser, t.inTreasury_user AS inTreasuryUser,
            t.sj_out_time AS sjOutTime, t.yj_out_time AS yjOutTime, t.totalPrice,
            o.order_id AS orderNum, o.order_type AS orderType, o.order_status AS orderStatus,
            h.sample_store_name AS storeName,
            sale.user_name AS saleUserName, sale.true_name AS saleTrueName,
            rk.user_name AS rkryUserName, rk.true_name AS rkryTrueName,
            q.name AS customerName
        FROM exp_goods_out_treasury t
        LEFT JOIN experiment_order o ON t.order_id = o.id
        LEFT JOIN sample_goods_storehouse h ON t.store_id = h.id
        LEFT JOIN sy_users sale ON t.sale_user = sale.id
        LEFT JOIN sy_users rk ON t.inTreasury_user = rk.id
        LEFT JOIN qd_user_company q ON t.customer_id = q.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not row:
        return None
    rkry = str(row.get("rkryTrueName") or row.get("rkryUserName") or "").strip()
    row["rkryname"] = rkry
    return row


def list_sample_order_items(out_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            t.id, t.out_id AS outId, t.goods_id AS goodsId,
            t.goods_name AS goodsName, t.goods_brand_name AS goodsBrandName,
            t.serial_number AS serialNumber, t.goods_spec AS goodsSpec,
            t.goods_price AS goodsPrice, t.out_num AS outNum,
            t.inventory_id AS inventoryId, t.got_status AS gotStatus,
            t.store_id AS storeId, t.store_position_id AS storePositionId,
            c.order_id AS childOrderId,
            gs.sample_store_name AS sampleStoreName,
            b.block AS blockName, p.number AS positionNumber
        FROM exp_goods_out_treasury_child t
        LEFT JOIN experiment_order_child c ON t.order_child_id = c.id
        LEFT JOIN sample_goods_storehouse gs ON t.store_id = gs.id
        LEFT JOIN sample_goods_store_position p ON t.store_position_id = p.id
        LEFT JOIN sample_goods_store_block b ON p.sample_block_id = b.id
        WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.out_id = %(out_id)s
        ORDER BY t.addTime ASC, t.id ASC
        """,
        {"out_id": out_id},
    )
    for row in rows:
        st = int(row.get("gotStatus") or 0)
        row["gotStatusLabel"] = GOT_STATUS_LABEL.get(st, str(st) if st else "-")
        block = str(row.get("blockName") or "")
        num = str(row.get("positionNumber") or "")
        row["storePosition"] = f"{block} - {num}".strip(" -") if (block or num) else ""
    return rows


def list_sample_store_options() -> list[dict[str, Any]]:
    """样品仓库下拉（type=1），对齐 Java samplestoreHouse/queryStore.ajax。"""
    return fetch_all(
        """
        SELECT id AS value, sample_store_name AS label, sample_store_num AS storeNum
        FROM sample_goods_storehouse
        WHERE IFNULL(deleteStatus, 0) = 0 AND type = 1 AND IFNULL(status, 1) = 1
        ORDER BY sample_store_name ASC
        LIMIT 500
        """
    )


def list_sample_export_rows(
    *,
    store_id: str = "",
    start_time: str = "",
    end_time: str = "",
) -> list[dict[str, Any]]:
    """对齐 Java getAllList / export.htm：样品到货/领用/归还日志。"""
    where = """
        WHERE t.status != 3 AND t.in_out_type = 1
          AND (
            log.log_info LIKE '样品到货%%'
            OR log.log_info LIKE '样品领用%%'
            OR log.log_info LIKE '样品归还%%'
          )
    """
    params: dict[str, Any] = {}
    if store_id:
        where += " AND t.store_id = %(store_id)s"
        params["store_id"] = store_id
    if start_time:
        where += " AND t.sj_out_time >= %(start_time)s"
        params["start_time"] = start_time
    if end_time:
        where += " AND t.sj_out_time <= %(end_time)s"
        params["end_time"] = end_time
    return fetch_all(
        f"""
        SELECT
            log.addTime AS operateTime,
            u.user_name AS operateUser,
            log.log_info AS operateInfo,
            eoc.order_id AS orderChildId,
            c.goods_brand_name AS goodsBrandName,
            c.goods_name AS goodsName,
            c.goods_spec AS goodsSpec,
            CONCAT(IFNULL(b.block, ''), '-', IFNULL(p.number, '')) AS storeSlot,
            gs.sample_store_name AS storeName
        FROM exp_goods_out_treasury t
        LEFT JOIN exp_outin_depot_log log ON t.id = log.of_id
        LEFT JOIN sy_users u ON log.log_user_id = u.id
        LEFT JOIN exp_goods_out_treasury_child c ON t.id = c.out_id
        LEFT JOIN experiment_order_child eoc ON c.order_child_id = eoc.id
        LEFT JOIN sample_goods_storehouse gs ON log.store_id = gs.id
        LEFT JOIN sample_goods_store_position p ON log.store_position_id = p.id
        LEFT JOIN sample_goods_store_block b ON p.sample_block_id = b.id
        {where}
        ORDER BY log.addTime DESC
        LIMIT 20000
        """,
        params,
    )
