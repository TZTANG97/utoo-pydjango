from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def _bit_flag(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (bytes, bytearray)):
        return 1 if value and value[0] else 0
    if isinstance(value, str) and len(value) == 1 and ord(value) <= 1:
        return ord(value)
    try:
        return 1 if int(value) else 0
    except (TypeError, ValueError):
        return 1 if value else 0


def list_goods(
    *,
    goods_name: str = "",
    gc_id: str | int | None = None,
    goods_brand_id: str | int | None = None,
    goods_recommend: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # Java goods_list: goods_status != -1 AND goods_status > -2
    # map=1 → 自有品牌 + platform_type 含 2（愉兔）
    where = """
        WHERE g.goods_status != -1
          AND g.goods_status > -2
          AND gb.is_own_brand = 1
          AND IFNULL(gb.platform_type, '') LIKE %(platform_type)s
    """
    params: dict[str, Any] = {"platform_type": "%2%"}
    if goods_name:
        where += " AND (g.goods_name LIKE %(goods_name)s OR IFNULL(g.en_name, '') LIKE %(goods_name)s)"
        params["goods_name"] = f"%{goods_name}%"
    if gc_id not in (None, ""):
        where += " AND g.gc_id = %(gc_id)s"
        params["gc_id"] = gc_id
    if goods_brand_id not in (None, ""):
        where += " AND g.goods_brand_id = %(goods_brand_id)s"
        params["goods_brand_id"] = goods_brand_id
    if goods_recommend not in (None, ""):
        flag = str(goods_recommend).lower()
        if flag in ("true", "1"):
            where += " AND g.goods_recommend = 1"
        elif flag in ("false", "0"):
            where += " AND IFNULL(g.goods_recommend, 0) = 0"
        else:
            where += " AND g.goods_recommend = %(goods_recommend)s"
            params["goods_recommend"] = goods_recommend

    from_sql = """
        FROM goods g
        INNER JOIN goodsbrand gb ON g.goods_brand_id = gb.id
        LEFT JOIN goodsclass gc ON g.gc_id = gc.id
        LEFT JOIN accessory a ON g.goods_main_photo_id = a.id
        LEFT JOIN sy_users su ON TRIM(g.head_user_id) = TRIM(su.id)
    """

    total = int(scalar(f"SELECT COUNT(*) {from_sql} {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            g.id,
            g.addTime,
            g.goods_name AS goodsName,
            g.en_name AS enName,
            g.goods_price AS goodsPrice,
            g.store_price AS storePrice,
            g.goods_inventory AS goodsInventory,
            g.goods_salenum AS goodsSalenum,
            g.goods_status AS goodsStatus,
            g.goods_recommend AS goodsRecommend,
            g.gc_id AS gcId,
            g.goods_brand_id AS goodsBrandId,
            g.head_user_id AS headUserId,
            g.is_calibration AS isCalibration,
            g.is_maintenance AS isMaintenance,
            g.is_install AS isInstall,
            g.goods_main_photo_id AS goodsMainPhotoId,
            a.path AS photoPath,
            a.name AS photoName,
            gc.className,
            gb.name AS brandName,
            su.user_name AS headUserName
        {from_sql}
        {where}
        ORDER BY g.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        row["goodsRecommend"] = _bit_flag(row.get("goodsRecommend"))
        row["isCalibration"] = _bit_flag(row.get("isCalibration"))
        row["isMaintenance"] = _bit_flag(row.get("isMaintenance"))
        row["isInstall"] = _bit_flag(row.get("isInstall"))
        # 对齐 Java：查到用户显示 userName，查不到显示空
        row["headUserName"] = (row.get("headUserName") or "") if row.get("headUserId") else ""
    return rows, total


def list_brand_options() -> list[dict[str, Any]]:
    # 对齐 Java 品牌下拉：isOwnBrand=1、platformType=2
    return fetch_all(
        """
        SELECT id, name
        FROM goodsbrand
        WHERE IFNULL(deleteStatus, 0) = 0
          AND is_own_brand = 1
          AND IFNULL(platform_type, '') LIKE %(platform_type)s
        ORDER BY sequence ASC, name ASC
        LIMIT 500
        """,
        {"platform_type": "%2%"},
    )


def list_class_options() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, className, parent_id AS parentId, level
        FROM goodsclass
        WHERE IFNULL(deleteStatus, 0) = 0
        ORDER BY sequence ASC, className ASC
        LIMIT 1000
        """
    )


def toggle_recommend(goods_id: int) -> int | None:
    row = fetch_one("SELECT goods_recommend FROM goods WHERE id = %(id)s LIMIT 1", {"id": goods_id})
    if not row:
        return None
    current = _bit_flag(row.get("goods_recommend"))
    next_val = 0 if current == 1 else 1
    execute(
        "UPDATE goods SET goods_recommend = %(val)s WHERE id = %(id)s",
        {"val": next_val, "id": goods_id},
    )
    return next_val


def toggle_sale(goods_id: int) -> int | None:
    """对齐 Java goods_sale：status==0 → -1(下架)，否则 → 0(上架)。"""
    row = fetch_one("SELECT goods_status FROM goods WHERE id = %(id)s LIMIT 1", {"id": goods_id})
    if not row:
        return None
    current = int(row.get("goods_status") or 0)
    next_val = -1 if current == 0 else 0
    execute(
        "UPDATE goods SET goods_status = %(val)s WHERE id = %(id)s",
        {"val": next_val, "id": goods_id},
    )
    return next_val
