from __future__ import annotations

from typing import Any, Literal

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

Kind = Literal["goods", "sample"]


def _block_table(kind: Kind) -> str:
    return "goods_store_block" if kind == "goods" else "sample_goods_store_block"


def _pos_table(kind: Kind) -> str:
    return "goods_store_position" if kind == "goods" else "sample_goods_store_position"


def _store_fk(kind: Kind) -> str:
    return "store_id" if kind == "goods" else "sample_store_id"


def _block_fk(kind: Kind) -> str:
    return "block_id" if kind == "goods" else "sample_block_id"


def list_blocks(
    *,
    kind: Kind,
    store_id: int,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    table = _block_table(kind)
    fk = _store_fk(kind)
    where = f"WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.{fk} = %(store_id)s"
    params: dict[str, Any] = {"store_id": store_id}
    total = int(scalar(f"SELECT COUNT(*) FROM {table} t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.id, t.addTime, t.block, t.{fk} AS storeId
        FROM {table} t
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows or [], total


def list_block_options(*, kind: Kind, store_id: int) -> list[dict[str, Any]]:
    table = _block_table(kind)
    fk = _store_fk(kind)
    return fetch_all(
        f"""
        SELECT t.id, t.block
        FROM {table} t
        WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.{fk} = %(store_id)s
        ORDER BY t.block ASC
        """,
        {"store_id": store_id},
    )


def add_block(*, kind: Kind, store_id: int, block: str) -> tuple[bool, str]:
    block = (block or "").strip()
    if not block:
        return False, "请填写地块名!"
    table = _block_table(kind)
    fk = _store_fk(kind)
    exists = scalar(
        f"""
        SELECT COUNT(*) FROM {table}
        WHERE IFNULL(deleteStatus, 0) = 0 AND {fk} = %(store_id)s AND block = %(block)s
        """,
        {"store_id": store_id, "block": block},
    )
    if int(exists or 0) > 0:
        return False, "地块名不能重复!"
    execute_insert(
        f"""
        INSERT INTO {table} (addTime, deleteStatus, {fk}, block)
        VALUES (NOW(), 0, %(store_id)s, %(block)s)
        """,
        {"store_id": store_id, "block": block},
    )
    return True, "ok"


def list_positions(
    *,
    kind: Kind,
    store_id: int,
    block_pos: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    pos = _pos_table(kind)
    blk = _block_table(kind)
    sfk = _store_fk(kind)
    bfk = _block_fk(kind)
    where = f"WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.{sfk} = %(store_id)s"
    params: dict[str, Any] = {"store_id": store_id}
    block_pos = (block_pos or "").replace(" ", "")
    if block_pos:
        parts = block_pos.split("-", 1)
        where += " AND b.block = %(block_name)s"
        params["block_name"] = parts[0]
        if len(parts) == 2 and parts[1]:
            where += " AND t.number = %(number)s"
            params["number"] = parts[1]

    if kind == "goods":
        total = int(
            scalar(
                f"""
                SELECT COUNT(*)
                FROM {pos} t
                LEFT JOIN {blk} b ON t.{bfk} = b.id
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
                t.id, t.addTime, t.number, t.char_number AS charNumber,
                t.goods_brand_id AS goodsBrandId,
                t.goods_brand_name AS goodsBrandName,
                t.serial_number AS serialNumber,
                t.goods_spec AS goodsSpec,
                t.{sfk} AS storeId, t.{bfk} AS blockId,
                b.block AS blockName,
                CONCAT(IFNULL(b.block, ''), '-', IFNULL(t.number, '')) AS positionLabel
            FROM {pos} t
            LEFT JOIN {blk} b ON t.{bfk} = b.id
            {where}
            ORDER BY b.block ASC, CONVERT(t.number, SIGNED) ASC
            {clause}
            """,
            {**params, **page_params},
        )
    else:
        total = int(
            scalar(
                f"""
                SELECT COUNT(*)
                FROM {pos} t
                LEFT JOIN {blk} b ON t.{bfk} = b.id
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
                t.id, t.addTime, t.number, t.char_number AS charNumber,
                t.goods_brand_id AS goodsBrandId,
                t.goods_brand_name AS goodsBrandName,
                t.serial_number AS serialNumber,
                t.goods_spec AS goodsSpec,
                t.sample_name AS sampleName,
                t.position_status AS positionStatus,
                t.{sfk} AS storeId, t.{bfk} AS blockId,
                b.block AS blockName,
                eg.goods_name AS goodsName,
                CONCAT(IFNULL(b.block, ''), '-', IFNULL(t.number, '')) AS positionLabel
            FROM {pos} t
            LEFT JOIN {blk} b ON t.{bfk} = b.id
            LEFT JOIN experiment_goods eg ON t.goods_id = eg.id
            {where}
            ORDER BY b.block ASC, CONVERT(t.number, SIGNED) ASC
            {clause}
            """,
            {**params, **page_params},
        )
    for row in rows or []:
        brand = str(row.get("goodsBrandName") or "").strip()
        if kind == "goods":
            row["occupiedLabel"] = "已放置" if brand else "空闲"
        else:
            st = int(row.get("positionStatus") or 0)
            if st == 2:
                row["occupiedLabel"] = "留存"
            elif st == 1 or brand:
                row["occupiedLabel"] = "已放置"
            else:
                row["occupiedLabel"] = "空闲"
    return rows or [], total


def _position_exists(*, kind: Kind, store_id: int, block_id: int, number: str) -> bool:
    pos = _pos_table(kind)
    sfk = _store_fk(kind)
    bfk = _block_fk(kind)
    n = int(
        scalar(
            f"""
            SELECT COUNT(*) FROM {pos}
            WHERE IFNULL(deleteStatus, 0) = 0
              AND {sfk} = %(store_id)s
              AND {bfk} = %(block_id)s
              AND number = %(number)s
            """,
            {"store_id": store_id, "block_id": block_id, "number": str(number)},
        )
        or 0
    )
    return n > 0


def add_positions(
    *,
    kind: Kind,
    store_id: int,
    block_id: int,
    number: str = "",
    batch: bool = False,
    start_number: str = "",
    end_number: str = "",
    char_number: str = "",
) -> tuple[bool, str]:
    if not block_id:
        return False, "请选择地块名!"
    pos = _pos_table(kind)
    sfk = _store_fk(kind)
    bfk = _block_fk(kind)
    char_number = (char_number or "").strip() or None

    def _insert_one(num: str) -> None:
        execute_insert(
            f"""
            INSERT INTO {pos}
                (addTime, deleteStatus, {sfk}, {bfk}, number, char_number)
            VALUES
                (NOW(), 0, %(store_id)s, %(block_id)s, %(number)s, %(char_number)s)
            """,
            {
                "store_id": store_id,
                "block_id": block_id,
                "number": str(num),
                "char_number": char_number,
            },
        )

    if batch:
        try:
            start = int(start_number)
            end = int(end_number)
        except (TypeError, ValueError):
            return False, "请填写正确的起止编号!"
        if end < start:
            return False, "结束编号不能小于开始编号!"
        for i in range(start, end + 1):
            if _position_exists(kind=kind, store_id=store_id, block_id=block_id, number=str(i)):
                return False, f"编号：{i}位置标识不能重复!"
            _insert_one(str(i))
        return True, "ok"

    number = (number or "").strip()
    if not number:
        return False, "请填写位置编号!"
    if _position_exists(kind=kind, store_id=store_id, block_id=block_id, number=number):
        return False, "位置标识不能重复!"
    _insert_one(number)
    return True, "ok"


def soft_delete_position(*, kind: Kind, pos_id: int) -> tuple[bool, str]:
    pos = _pos_table(kind)
    row = fetch_one(
        f"""
        SELECT id, goods_brand_name AS goodsBrandName
        FROM {pos}
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": pos_id},
    )
    if not row:
        return False, "位置不存在"
    if str(row.get("goodsBrandName") or "").strip():
        return False, "位置中的产品不为空,不允许删除"
    execute(
        f"UPDATE {pos} SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": pos_id},
    )
    return True, "操作成功!"


def clear_sample_goods(*, pos_id: int) -> tuple[bool, str]:
    row = fetch_one(
        "SELECT id FROM sample_goods_store_position WHERE id = %(id)s LIMIT 1",
        {"id": pos_id},
    )
    if not row:
        return False, "位置不存在"
    execute(
        """
        UPDATE sample_goods_store_position
        SET position_status = 0,
            char_number = NULL,
            goods_id = NULL,
            sample_name = NULL,
            inventory_id = NULL,
            goods_spec = NULL,
            serial_number = NULL,
            goods_brand_name = NULL,
            goods_brand_id = NULL
        WHERE id = %(id)s
        """,
        {"id": pos_id},
    )
    return True, "操作成功!"


def get_qr_payload(*, kind: Kind, pos_id: int, retain: bool = False) -> tuple[bool, str]:
    if kind == "goods":
        row = fetch_one(
            """
            SELECT
                t.id AS posId, t.number, s.id AS storeId, s.store_name AS storeName,
                b.block AS blockName
            FROM goods_store_position t
            LEFT JOIN goods_storehouse s ON t.store_id = s.id
            LEFT JOIN goods_store_block b ON t.block_id = b.id
            WHERE t.id = %(id)s
            LIMIT 1
            """,
            {"id": pos_id},
        )
        if not row:
            return False, "位置不存在"
        text = f"{row.get('storeId')};{row.get('storeName') or ''};{row.get('blockName') or ''}-{row.get('number') or ''}"
        return True, text

    row = fetch_one(
        """
        SELECT
            t.id AS posId, t.number,
            s.sample_store_name AS storeName,
            b.block AS blockName
        FROM sample_goods_store_position t
        LEFT JOIN sample_goods_storehouse s ON t.sample_store_id = s.id
        LEFT JOIN sample_goods_store_block b ON t.sample_block_id = b.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": pos_id},
    )
    if not row:
        return False, "位置不存在"
    prefix = "newStorePosId_" if retain else "storePosId_"
    text = (
        f"{prefix}{row.get('posId')};"
        f"{row.get('storeName') or ''};"
        f"{row.get('blockName') or ''}-{row.get('number') or ''}"
    )
    return True, text
