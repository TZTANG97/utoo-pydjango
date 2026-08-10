from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction

from apps.admin_ops.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


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
        # Java：1=是，2=否；勿用 _bit_flag 否则 2 会被当成真
        row["isCalibration"] = 1 if _to_int(row.get("isCalibration"), 0) == 1 else 0
        row["isMaintenance"] = 1 if _to_int(row.get("isMaintenance"), 0) == 1 else 0
        row["isInstall"] = 1 if _to_int(row.get("isInstall"), 0) == 1 else 0
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


def _to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _to_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _flag01(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "是"):
        return 1
    if s in ("0", "false", "no", "否"):
        return 0
    return _bit_flag(value)


def _parse_skus(raw: Any) -> list[dict[str, Any]]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(item)
    return out


def get_goods(goods_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            g.id,
            g.goods_name,
            g.en_name,
            g.goods_details,
            g.goods_price,
            g.store_price,
            g.local_price,
            g.local_type,
            g.goods_time,
            g.goods_inventory,
            g.goods_serial,
            g.goods_status,
            g.goods_recommend,
            g.inventory_type,
            g.goods_spec,
            g.gc_id,
            g.goods_brand_id,
            g.goods_main_photo_id,
            g.is_calibration,
            g.is_maintenance,
            g.is_install,
            g.is_secondhand,
            g.is_lease,
            g.zdqzr,
            g.relation_goods,
            g.head_user_id,
            g.goods_choice_type,
            a.path AS photo_path,
            a.name AS photo_name,
            gc.className AS class_name,
            gb.name AS brand_name,
            su.user_name AS head_user_name
        FROM goods g
        LEFT JOIN accessory a ON g.goods_main_photo_id = a.id
        LEFT JOIN goodsclass gc ON g.gc_id = gc.id
        LEFT JOIN goodsbrand gb ON g.goods_brand_id = gb.id
        LEFT JOIN sy_users su ON TRIM(g.head_user_id) = TRIM(su.id)
        WHERE g.id = %(id)s
        LIMIT 1
        """,
        {"id": goods_id},
    )
    if not row:
        return None
    data = normalize_row(row) or {}
    data["goodsRecommend"] = _bit_flag(data.get("goodsRecommend"))
    # Java 服务类标记：1=是，2=否
    for key in ("isCalibration", "isMaintenance", "isInstall", "isSecondhand", "isLease"):
        data[key] = _service_flag(data.get(key))
    skus = fetch_all(
        """
        SELECT
            id,
            sku_id AS skuId,
            sku_name AS skuName,
            specpids,
            stocks,
            price,
            sku_code AS skuCode,
            yzjzj,
            yzscj
        FROM goods_sku
        WHERE goods_id = %(id)s
          AND IFNULL(deleteStatus, 0) = 0
        ORDER BY id ASC
        """,
        {"id": goods_id},
    )
    data["skus"] = normalize_rows(skus)
    data["relationGoodsList"] = _relation_goods_list(data.get("relationGoods") or "")
    return data


def _service_flag(value: Any, default: int = 2) -> int:
    """对齐 Java：1=是，2=否。"""
    if value in (None, ""):
        return default
    try:
        n = int(value)
        if n == 1:
            return 1
        if n == 2:
            return 2
    except (TypeError, ValueError):
        pass
    return 1 if _bit_flag(value) else 2


def _relation_goods_list(raw: Any) -> list[dict[str, Any]]:
    ids: list[int] = []
    text = str(raw or "").strip()
    if not text:
        return []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for gid in ids:
        if gid in seen:
            continue
        seen.add(gid)
        r = fetch_one(
            "SELECT id, goods_name AS goodsName FROM goods WHERE id=%(id)s LIMIT 1",
            {"id": gid},
        )
        if r:
            out.append({"id": r["id"], "goodsName": r["goodsName"]})
    return out


def search_goods_options(*, keyword: str = "", limit: int = 30) -> list[dict[str, Any]]:
    where = "WHERE g.goods_status != -1 AND g.goods_status > -2"
    params: dict[str, Any] = {"limit": max(1, min(int(limit or 30), 100))}
    if keyword.strip():
        where += " AND (g.goods_name LIKE %(kw)s OR IFNULL(g.en_name,'') LIKE %(kw)s)"
        params["kw"] = f"%{keyword.strip()}%"
    return fetch_all(
        f"""
        SELECT g.id, g.goods_name AS goodsName, gb.name AS brandName
        FROM goods g
        LEFT JOIN goodsbrand gb ON g.goods_brand_id = gb.id
        {where}
        ORDER BY g.addTime DESC
        LIMIT %(limit)s
        """,
        params,
    )


def _sync_skus(
    goods_id: int,
    *,
    skus: list[dict[str, Any]],
    inventory_type: str,
    goods_price: Decimal | None,
    goods_inventory: int,
    goods_serial: str,
) -> None:
    execute("DELETE FROM goods_sku WHERE goods_id = %(id)s", {"id": goods_id})
    rows = skus
    if not rows:
        rows = [
            {
                "skuName": "标准商品",
                "specpids": "",
                "stocks": goods_inventory,
                "price": goods_price,
                "skuCode": goods_serial,
            }
        ]
        inventory_type = "all"
    for item in rows:
        stocks = _to_int(item.get("stocks") if "stocks" in item else item.get("goodsInventory"), 0) or 0
        price = _to_decimal(item.get("price") if "price" in item else item.get("goodsPrice"), Decimal("0"))
        specpids = str(item.get("specpids") or item.get("specPids") or "").strip()
        sku_name = str(item.get("skuName") or item.get("sku_name") or "").strip() or ("标准商品" if not specpids else "")
        sku_code = str(item.get("skuCode") or item.get("sku_code") or "").strip()
        yzjzj = _to_decimal(item.get("yzjzj"), Decimal("0"))
        yzscj = _to_decimal(item.get("yzscj"), Decimal("0"))
        # 对齐 Java：sku_id = goodsId + "," + specpids
        sku_id = f"{goods_id},{specpids}" if specpids else f"{goods_id},"
        execute_insert(
            """
            INSERT INTO goods_sku
                (addTime, deleteStatus, goods_id, specpids, sku_id, sku_name, stocks, price, sku_code, yzjzj, yzscj)
            VALUES
                (CURDATE(), 0, %(goods_id)s, %(specpids)s, %(sku_id)s, %(sku_name)s,
                 %(stocks)s, %(price)s, %(sku_code)s, %(yzjzj)s, %(yzscj)s)
            """,
            {
                "goods_id": goods_id,
                "specpids": specpids or None,
                "sku_id": sku_id,
                "sku_name": sku_name or None,
                "stocks": stocks,
                "price": price,
                "sku_code": sku_code or None,
                "yzjzj": yzjzj,
                "yzscj": yzscj,
            },
        )
    # 库存汇总到商品表
    total_stocks = int(
        scalar(
            "SELECT IFNULL(SUM(stocks), 0) FROM goods_sku WHERE goods_id=%(id)s AND IFNULL(deleteStatus,0)=0",
            {"id": goods_id},
        )
        or 0
    )
    execute(
        "UPDATE goods SET goods_inventory=%(inv)s, inventory_type=%(itype)s WHERE id=%(id)s",
        {
            "inv": total_stocks if rows else goods_inventory,
            "itype": inventory_type or ("spec" if len(rows) > 1 else "all"),
            "id": goods_id,
        },
    )


@transaction.atomic
def save_goods(
    *,
    goods_id: int | None,
    edit_type: str = "",
    form_mode: str = "full",
    goods_name: str,
    en_name: str = "",
    goods_details: str = "",
    goods_price: Any = None,
    store_price: Any = None,
    local_price: Any = None,
    goods_inventory: Any = 0,
    goods_serial: str = "",
    goods_status: Any = 0,
    goods_recommend: Any = 0,
    inventory_type: str = "all",
    goods_spec: str = "",
    gc_id: int | None = None,
    goods_brand_id: int | None = None,
    goods_main_photo_id: int | None = None,
    is_calibration: Any = 1,
    is_maintenance: Any = 1,
    is_install: Any = 1,
    is_secondhand: Any = 1,
    is_lease: Any = 1,
    zdqzr: Any = 0,
    relation_goods: str = "",
    head_user_id: str = "",
    local_type: str = "4",
    goods_time: Any = None,
    goods_choice_type: Any = 1,
    skus: Any = None,
    add_user_id: int | None = None,
) -> int:
    """
    对齐 Java：
    - form_mode=lite → add_goods_finishNew（精简字段；编辑时不覆盖完整版专有字段/SKU）
    - form_mode=full → add_goods_finish（完整字段）
    - editType=2 → 复制新建
    """
    if str(edit_type) == "2":
        goods_id = None
    is_lite = str(form_mode or "full").lower() in ("lite", "new", "2")

    price = _to_decimal(goods_price, Decimal("0")) or Decimal("0")
    s_price = _to_decimal(store_price, price) or price
    l_price = _to_decimal(local_price, price) or price
    inventory = _to_int(goods_inventory, 0) or 0
    status = _to_int(goods_status, 0)
    if status is None:
        status = 0
    recommend = _flag01(goods_recommend, 0)
    choice_type = _to_int(goods_choice_type, 1) or 1
    g_time = _to_int(goods_time, None)
    zd = _to_int(zdqzr, 0) or 0
    itype = (inventory_type or "all").strip() or "all"
    sku_rows = _parse_skus(skus)
    if sku_rows and itype == "all" and len(sku_rows) > 1:
        itype = "spec"
    relation = (relation_goods or "").strip() or None

    # 精简版新建：对齐 Java 隐藏默认值（服务类均为「是」=1）
    if is_lite and not goods_id:
        is_calibration = 1
        is_maintenance = 1
        is_install = 1
        is_secondhand = 1
        is_lease = 1
        zdqzr = 0
        recommend = 0
        status = 0

    lite_params = {
        "goods_name": goods_name.strip(),
        "goods_details": goods_details or None,
        "goods_spec": (goods_spec or "").strip() or None,
        "gc_id": gc_id,
        "goods_brand_id": goods_brand_id,
        "goods_main_photo_id": goods_main_photo_id,
        "relation_goods": relation,
    }

    if is_lite and goods_id:
        execute(
            """
            UPDATE goods SET
                goods_name=%(goods_name)s,
                goods_details=%(goods_details)s,
                goods_spec=%(goods_spec)s,
                gc_id=%(gc_id)s,
                goods_brand_id=%(goods_brand_id)s,
                goods_main_photo_id=%(goods_main_photo_id)s,
                relation_goods=%(relation_goods)s,
                modify_time=NOW()
            WHERE id=%(id)s
            """,
            {**lite_params, "id": goods_id},
        )
        return goods_id

    params = {
        **lite_params,
        "en_name": (en_name or "").strip() or None,
        "goods_price": price,
        "store_price": s_price,
        "local_price": l_price,
        "goods_inventory": inventory,
        "goods_serial": (goods_serial or "").strip() or None,
        "goods_status": status,
        "goods_recommend": recommend,
        "inventory_type": itype,
        "is_calibration": _service_flag(is_calibration, 1),
        "is_maintenance": _service_flag(is_maintenance, 1),
        "is_install": _service_flag(is_install, 1),
        "is_secondhand": _service_flag(is_secondhand, 1),
        "is_lease": _service_flag(is_lease, 1),
        "zdqzr": zd,
        "head_user_id": (str(head_user_id).strip() if head_user_id not in (None, "") else None),
        "local_type": str(local_type if local_type not in (None, "") else "4"),
        "goods_time": g_time,
        "goods_choice_type": choice_type,
    }

    if goods_id:
        execute(
            """
            UPDATE goods SET
                goods_name=%(goods_name)s,
                en_name=%(en_name)s,
                goods_details=%(goods_details)s,
                goods_price=%(goods_price)s,
                store_price=%(store_price)s,
                local_price=%(local_price)s,
                goods_inventory=%(goods_inventory)s,
                goods_serial=%(goods_serial)s,
                goods_status=%(goods_status)s,
                goods_recommend=%(goods_recommend)s,
                inventory_type=%(inventory_type)s,
                goods_spec=%(goods_spec)s,
                gc_id=%(gc_id)s,
                goods_brand_id=%(goods_brand_id)s,
                goods_main_photo_id=%(goods_main_photo_id)s,
                is_calibration=%(is_calibration)s,
                is_maintenance=%(is_maintenance)s,
                is_install=%(is_install)s,
                is_secondhand=%(is_secondhand)s,
                is_lease=%(is_lease)s,
                zdqzr=%(zdqzr)s,
                relation_goods=%(relation_goods)s,
                head_user_id=%(head_user_id)s,
                local_type=%(local_type)s,
                goods_time=%(goods_time)s,
                goods_choice_type=%(goods_choice_type)s,
                modify_time=NOW()
            WHERE id=%(id)s
            """,
            {**params, "id": goods_id},
        )
        new_id = goods_id
    else:
        new_id = execute_insert(
            """
            INSERT INTO goods (
                addTime, deleteStatus, goods_click, goods_details, goods_inventory,
                goods_name, goods_price, goods_recommend, goods_salenum, goods_serial,
                goods_status, goods_transfee, inventory_type, store_price, store_recommend,
                gc_id, goods_brand_id, goods_main_photo_id, goods_collect, group_buy,
                goods_choice_type, activity_status, bargain_status, delivery_status,
                goods_current_price, description_evaluate, goods_spec,
                is_calibration, is_maintenance, is_install, is_secondhand, is_lease,
                zdqzr, relation_goods, add_user_id,
                local_type, local_price, goods_time, head_user_id, en_name, goods_seller_time
            ) VALUES (
                NOW(), 0, 0, %(goods_details)s, %(goods_inventory)s,
                %(goods_name)s, %(goods_price)s, %(goods_recommend)s, 0, %(goods_serial)s,
                %(goods_status)s, 0, %(inventory_type)s, %(store_price)s, 0,
                %(gc_id)s, %(goods_brand_id)s, %(goods_main_photo_id)s, 0, 0,
                %(goods_choice_type)s, 0, 0, 0,
                %(goods_price)s, 5, %(goods_spec)s,
                %(is_calibration)s, %(is_maintenance)s, %(is_install)s, %(is_secondhand)s, %(is_lease)s,
                %(zdqzr)s, %(relation_goods)s, %(add_user_id)s,
                %(local_type)s, %(local_price)s, %(goods_time)s, %(head_user_id)s, %(en_name)s, NOW()
            )
            """,
            {**params, "add_user_id": add_user_id},
        )

    # 精简版新建也落一条标准 SKU；完整版始终同步 SKU
    if not is_lite or not goods_id:
        _sync_skus(
            new_id,
            skus=[] if is_lite else sku_rows,
            inventory_type="all" if is_lite else itype,
            goods_price=price,
            goods_inventory=inventory,
            goods_serial=(goods_serial or "").strip(),
        )
    return new_id
