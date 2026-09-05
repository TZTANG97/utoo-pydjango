from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _not_deleted(alias: str = "") -> str:
    col = f"{alias}." if alias else ""
    return f"IFNULL({col}deleteStatus, 0) = 0"


# ---------- Spec ----------
def list_specs(*, name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_not_deleted('s')}"
    params: dict[str, Any] = {}
    if name:
        where += " AND s.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM goodsspecification s {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT s.id, s.addTime, s.name, s.sequence, s.type, s.is_show,
               (
                   SELECT GROUP_CONCAT(p.value ORDER BY p.sequence ASC SEPARATOR ',')
                   FROM goodsspecproperty p
                   WHERE p.spec_id = s.id AND IFNULL(p.deleteStatus, 0) = 0
               ) AS propertyValues
        FROM goodsspecification s
        {where}
        ORDER BY s.sequence ASC, s.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_spec(spec_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        f"SELECT * FROM goodsspecification WHERE id = %(id)s AND {_not_deleted()} LIMIT 1",
        {"id": spec_id},
    )
    if not row:
        return None
    data = normalize_row(row) or {}
    props = fetch_all(
        f"""
        SELECT id, sequence, value, specImage_id AS specImageId
        FROM goodsspecproperty
        WHERE spec_id = %(id)s AND {_not_deleted()}
        ORDER BY sequence ASC, id ASC
        """,
        {"id": spec_id},
    )
    data["properties"] = normalize_rows(props)
    return data


def save_spec(*, spec_id: int | None, name: str, sequence: int, type_: str, is_show: int, properties: list[dict]) -> int:
    if spec_id:
        execute(
            """
            UPDATE goodsspecification
            SET name=%(name)s, sequence=%(sequence)s, type=%(type)s, is_show=%(is_show)s
            WHERE id=%(id)s
            """,
            {"id": spec_id, "name": name, "sequence": sequence, "type": type_, "is_show": is_show},
        )
        execute(
            "UPDATE goodsspecproperty SET deleteStatus=1 WHERE spec_id=%(id)s",
            {"id": spec_id},
        )
        sid = spec_id
    else:
        sid = execute_insert(
            """
            INSERT INTO goodsspecification (addTime, deleteStatus, name, sequence, type, is_show)
            VALUES (NOW(), 0, %(name)s, %(sequence)s, %(type)s, %(is_show)s)
            """,
            {"name": name, "sequence": sequence, "type": type_, "is_show": is_show},
        )
    for idx, prop in enumerate(properties):
        value = str(prop.get("value") or "").strip()
        if not value:
            continue
        execute_insert(
            """
            INSERT INTO goodsspecproperty (addTime, deleteStatus, sequence, value, spec_id)
            VALUES (NOW(), 0, %(sequence)s, %(value)s, %(spec_id)s)
            """,
            {
                "sequence": int(prop.get("sequence") or idx),
                "value": value,
                "spec_id": sid,
            },
        )
    return sid


def delete_spec(spec_id: int) -> None:
    execute("UPDATE goodsspecification SET deleteStatus=1 WHERE id=%(id)s", {"id": spec_id})
    execute("UPDATE goodsspecproperty SET deleteStatus=1 WHERE spec_id=%(id)s", {"id": spec_id})


# ---------- Brand ----------
def list_brands(*, name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    # Java list: audit=1, type=1
    where = f"WHERE {_not_deleted('b')} AND b.audit = 1 AND b.type = 1"
    params: dict[str, Any] = {}
    if name:
        where += " AND b.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM goodsbrand b {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT b.id, b.addTime, b.name, b.first_word AS firstWord, b.sequence,
               b.en_name AS enName, b.recommend, b.is_own_brand AS isOwnBrand, b.platform_type AS platformType
        FROM goodsbrand b
        {where}
        ORDER BY b.sequence ASC, b.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_brand(brand_id: int) -> dict[str, Any] | None:
    return normalize_row(
        fetch_one(f"SELECT * FROM goodsbrand WHERE id=%(id)s AND {_not_deleted()} LIMIT 1", {"id": brand_id})
    )


def save_brand(*, brand_id: int | None, name: str, first_word: str, sequence: int, en_name: str = "") -> int:
    if brand_id:
        execute(
            """
            UPDATE goodsbrand
            SET name=%(name)s, first_word=%(first_word)s, sequence=%(sequence)s, en_name=%(en_name)s
            WHERE id=%(id)s
            """,
            {
                "id": brand_id,
                "name": name,
                "first_word": first_word,
                "sequence": sequence,
                "en_name": en_name or None,
            },
        )
        return brand_id
    return execute_insert(
        """
        INSERT INTO goodsbrand
            (addTime, deleteStatus, audit, name, recommend, sequence, userStatus,
             first_word, type, en_name, is_own_brand, platform_type)
        VALUES
            (NOW(), 0, 1, %(name)s, 0, %(sequence)s, 0,
             %(first_word)s, 1, %(en_name)s, 1, '2')
        """,
        {
            "name": name,
            "sequence": sequence,
            "first_word": first_word,
            "en_name": en_name or None,
        },
    )


def delete_brand(brand_id: int) -> str | None:
    linked = int(
        scalar("SELECT COUNT(*) FROM goods WHERE goods_brand_id=%(id)s AND goods_status > -2", {"id": brand_id})
        or 0
    )
    if linked:
        return "该品牌已关联商品，无法删除"
    execute("UPDATE goodsbrand SET deleteStatus=1 WHERE id=%(id)s", {"id": brand_id})
    return None


# ---------- Type ----------
def list_types(*, name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_not_deleted('t')}"
    params: dict[str, Any] = {}
    if name:
        where += " AND t.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM goodstype t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.id, t.addTime, t.name, t.sequence
        FROM goodstype t
        {where}
        ORDER BY t.sequence ASC, t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_type(type_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        f"SELECT * FROM goodstype WHERE id=%(id)s AND {_not_deleted()} LIMIT 1",
        {"id": type_id},
    )
    if not row:
        return None
    data = normalize_row(row) or {}
    data["specIds"] = [
        r["spec_id"]
        for r in fetch_all("SELECT spec_id FROM goodstype_spec WHERE type_id=%(id)s", {"id": type_id})
    ]
    data["brandIds"] = [
        r["brand_id"]
        for r in fetch_all("SELECT brand_id FROM goodstype_brand WHERE type_id=%(id)s", {"id": type_id})
    ]
    return data


def save_type(
    *,
    type_id: int | None,
    name: str,
    sequence: int,
    spec_ids: list[int] | None = None,
    brand_ids: list[int] | None = None,
) -> int:
    if type_id:
        execute(
            "UPDATE goodstype SET name=%(name)s, sequence=%(sequence)s WHERE id=%(id)s",
            {"id": type_id, "name": name, "sequence": sequence},
        )
        tid = type_id
        execute("DELETE FROM goodstype_spec WHERE type_id=%(id)s", {"id": tid})
        execute("DELETE FROM goodstype_brand WHERE type_id=%(id)s", {"id": tid})
    else:
        tid = execute_insert(
            """
            INSERT INTO goodstype (addTime, deleteStatus, name, sequence)
            VALUES (NOW(), 0, %(name)s, %(sequence)s)
            """,
            {"name": name, "sequence": sequence},
        )
    for sid in spec_ids or []:
        execute("INSERT INTO goodstype_spec (type_id, spec_id) VALUES (%(t)s, %(s)s)", {"t": tid, "s": sid})
    for bid in brand_ids or []:
        execute("INSERT INTO goodstype_brand (type_id, brand_id) VALUES (%(t)s, %(b)s)", {"t": tid, "b": bid})
    return tid


def delete_type(type_id: int) -> None:
    execute("UPDATE goodstype SET deleteStatus=1 WHERE id=%(id)s", {"id": type_id})
    execute("DELETE FROM goodstype_spec WHERE type_id=%(id)s", {"id": type_id})
    execute("DELETE FROM goodstype_brand WHERE type_id=%(id)s", {"id": type_id})


def list_spec_options() -> list[dict[str, Any]]:
    return normalize_rows(
        fetch_all(
            f"""
            SELECT id, name FROM goodsspecification
            WHERE {_not_deleted()}
            ORDER BY sequence ASC, id DESC LIMIT 1000
            """
        )
    )


def list_brand_options_all() -> list[dict[str, Any]]:
    return normalize_rows(
        fetch_all(
            f"""
            SELECT id, name FROM goodsbrand
            WHERE {_not_deleted()} AND audit=1
            ORDER BY sequence ASC, name ASC LIMIT 1000
            """
        )
    )


# ---------- Class ----------
def list_classes(*, parent_id: str | int | None = None) -> list[dict[str, Any]]:
    where = f"WHERE {_not_deleted('c')}"
    params: dict[str, Any] = {}
    if parent_id in (None, "", 0, "0"):
        where += " AND c.parent_id IS NULL"
    else:
        where += " AND c.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id
    rows = fetch_all(
        f"""
        SELECT c.id, c.className, c.sequence, c.display, c.level, c.parent_id AS parentId,
               c.goodsType_id AS goodsTypeId, t.name AS goodsTypeName,
               c.is_consumMaterial AS isConsumMaterial,
               EXISTS(
                   SELECT 1 FROM goodsclass ch
                   WHERE ch.parent_id = c.id AND IFNULL(ch.deleteStatus,0)=0
               ) AS hasChildren
        FROM goodsclass c
        LEFT JOIN goodstype t ON c.goodsType_id = t.id
        {where}
        ORDER BY c.sequence ASC, c.id ASC
        """,
        params,
    )
    result = normalize_rows(rows)
    for row in result:
        row["hasChildren"] = bool(row.get("hasChildren"))
        row["display"] = 1 if row.get("display") in (1, True, b"\x01", "\x01") else 0
    return result


def get_class(class_id: int) -> dict[str, Any] | None:
    return normalize_row(
        fetch_one(
            f"""
            SELECT c.*, t.name AS goodsTypeName
            FROM goodsclass c
            LEFT JOIN goodstype t ON c.goodsType_id = t.id
            WHERE c.id=%(id)s AND {_not_deleted('c')} LIMIT 1
            """,
            {"id": class_id},
        )
    )


def class_name_exists(
    *, class_name: str, parent_id: int | None, exclude_id: int | None = None
) -> bool:
    params: dict[str, Any] = {"name": class_name}
    where = f"WHERE {_not_deleted()} AND className = %(name)s"
    if parent_id:
        where += " AND parent_id = %(pid)s"
        params["pid"] = int(parent_id)
    else:
        where += " AND IFNULL(parent_id, 0) = 0"
    if exclude_id:
        where += " AND id <> %(xid)s"
        params["xid"] = int(exclude_id)
    return int(scalar(f"SELECT COUNT(*) FROM goodsclass {where}", params) or 0) > 0


def save_class(
    *,
    class_id: int | None,
    class_name: str,
    parent_id: int | None,
    goods_type_id: int | None,
    sequence: int,
    display: int,
    is_consum_material: int = 0,
) -> int:
    level = 0
    if parent_id:
        parent = fetch_one("SELECT level FROM goodsclass WHERE id=%(id)s LIMIT 1", {"id": parent_id})
        level = int((parent or {}).get("level") or 0) + 1
    if class_id:
        execute(
            """
            UPDATE goodsclass
            SET className=%(class_name)s, parent_id=%(parent_id)s, goodsType_id=%(goods_type_id)s,
                sequence=%(sequence)s, display=%(display)s, level=%(level)s,
                is_consumMaterial=%(is_consum)s
            WHERE id=%(id)s
            """,
            {
                "id": class_id,
                "class_name": class_name,
                "parent_id": parent_id,
                "goods_type_id": goods_type_id,
                "sequence": sequence,
                "display": display,
                "level": level,
                "is_consum": is_consum_material,
            },
        )
        return class_id
    return execute_insert(
        """
        INSERT INTO goodsclass
            (addTime, deleteStatus, className, display, level, recommend, sequence,
             goodsType_id, parent_id, is_consumMaterial)
        VALUES
            (NOW(), 0, %(class_name)s, %(display)s, %(level)s, 0, %(sequence)s,
             %(goods_type_id)s, %(parent_id)s, %(is_consum)s)
        """,
        {
            "class_name": class_name,
            "display": display,
            "level": level,
            "sequence": sequence,
            "goods_type_id": goods_type_id,
            "parent_id": parent_id,
            "is_consum": is_consum_material,
        },
    )


def delete_class(class_id: int) -> None:
    # soft-delete self and children recursively (one level expand repeated)
    ids = [class_id]
    queue = [class_id]
    while queue:
        pid = queue.pop()
        children = fetch_all(
            f"SELECT id FROM goodsclass WHERE parent_id=%(id)s AND {_not_deleted()}",
            {"id": pid},
        )
        for ch in children:
            cid = int(ch["id"])
            ids.append(cid)
            queue.append(cid)
    placeholders = ", ".join([f"%({i})s" for i in range(len(ids))])
    params = {str(i): v for i, v in enumerate(ids)}
    execute(f"UPDATE goodsclass SET deleteStatus=1 WHERE id IN ({placeholders})", params)


def list_type_options() -> list[dict[str, Any]]:
    return normalize_rows(
        fetch_all(
            f"""
            SELECT id, name FROM goodstype
            WHERE {_not_deleted()}
            ORDER BY sequence ASC, id DESC LIMIT 1000
            """
        )
    )


# ---------- Album ----------
def list_albums(*, name: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_not_deleted('a')}"
    params: dict[str, Any] = {}
    if name:
        where += " AND a.album_name LIKE %(name)s"
        params["name"] = f"%{name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM album a {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT a.id, a.addTime, a.album_name AS albumName, a.album_sequence AS albumSequence,
               a.album_default AS albumDefault, a.album_cover_id AS albumCoverId,
               COALESCE(acc.path, (
                   SELECT p.path FROM accessory p
                   WHERE p.album_id = a.id AND IFNULL(p.deleteStatus, 0) = 0
                   ORDER BY p.id DESC LIMIT 1
               )) AS coverPath,
               COALESCE(acc.name, (
                   SELECT p.name FROM accessory p
                   WHERE p.album_id = a.id AND IFNULL(p.deleteStatus, 0) = 0
                   ORDER BY p.id DESC LIMIT 1
               )) AS coverName,
               (
                   SELECT COUNT(*) FROM accessory p
                   WHERE p.album_id = a.id AND IFNULL(p.deleteStatus,0)=0
               ) AS photoCount
        FROM album a
        LEFT JOIN accessory acc ON a.album_cover_id = acc.id
        {where}
        ORDER BY a.album_sequence ASC, a.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    result = normalize_rows(rows)
    for row in result:
        row["albumDefault"] = 1 if row.get("albumDefault") in (1, True, b"\x01", "\x01") else 0
    return result, total


def get_album(album_id: int) -> dict[str, Any] | None:
    return normalize_row(
        fetch_one(
            f"""
            SELECT a.*, a.album_name AS albumName, a.album_sequence AS albumSequence,
                   a.album_default AS albumDefault, a.album_cover_id AS albumCoverId,
                   COALESCE(acc.path, (
                       SELECT p.path FROM accessory p
                       WHERE p.album_id = a.id AND IFNULL(p.deleteStatus, 0) = 0
                       ORDER BY p.id DESC LIMIT 1
                   )) AS coverPath,
                   COALESCE(acc.name, (
                       SELECT p.name FROM accessory p
                       WHERE p.album_id = a.id AND IFNULL(p.deleteStatus, 0) = 0
                       ORDER BY p.id DESC LIMIT 1
                   )) AS coverName
            FROM album a
            LEFT JOIN accessory acc ON a.album_cover_id = acc.id
            WHERE a.id=%(id)s AND {_not_deleted('a')}
            LIMIT 1
            """,
            {"id": album_id},
        )
    )


def save_album(*, album_id: int | None, album_name: str, album_sequence: int) -> int:
    if album_id:
        execute(
            """
            UPDATE album SET album_name=%(name)s, album_sequence=%(seq)s WHERE id=%(id)s
            """,
            {"id": album_id, "name": album_name, "seq": album_sequence},
        )
        return album_id
    return execute_insert(
        """
        INSERT INTO album (addTime, deleteStatus, album_default, album_name, album_sequence)
        VALUES (NOW(), 0, 0, %(name)s, %(seq)s)
        """,
        {"name": album_name, "seq": album_sequence},
    )


def delete_album(album_id: int) -> str | None:
    row = fetch_one("SELECT album_default FROM album WHERE id=%(id)s LIMIT 1", {"id": album_id})
    if not row:
        return "相册不存在"
    if row.get("album_default") in (1, True, b"\x01", "\x01"):
        return "默认相册不可删除"
    execute("UPDATE album SET deleteStatus=1 WHERE id=%(id)s", {"id": album_id})
    return None


def list_album_images(album_id: int, *, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE album_id=%(album_id)s AND IFNULL(deleteStatus,0)=0"
    params = {"album_id": album_id}
    total = int(scalar(f"SELECT COUNT(*) FROM accessory {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, addTime, name, path, ext, width, height, size
        FROM accessory
        {where}
        ORDER BY id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def list_goods_album_images(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java AccessoryMapper.listPage：轮播/商品「从相册选择」用 path='goods' 图片。"""
    where = """
        WHERE IFNULL(deleteStatus, 0) = 0
          AND path = 'goods'
          AND UPPER(IFNULL(ext, '')) IN (
              'JPG', 'PNG', 'JPEG', 'GIF', 'BMP', 'TIFF', 'PSD', 'SVG', 'EMF', 'PPM'
          )
    """
    total = int(scalar(f"SELECT COUNT(*) FROM accessory {where}") or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, addTime, name, path, ext, width, height, size
        FROM accessory
        {where}
        ORDER BY addTime DESC, id DESC
        {clause}
        """,
        page_params,
    )
    return normalize_rows(rows), total


def delete_album_image(image_id: int) -> None:
    execute("UPDATE accessory SET deleteStatus=1 WHERE id=%(id)s", {"id": image_id})


def set_album_cover(album_id: int, image_id: int) -> None:
    execute(
        "UPDATE album SET album_cover_id=%(image_id)s WHERE id=%(album_id)s",
        {"album_id": album_id, "image_id": image_id},
    )


# ---------- Evaluate ----------
def list_evaluates(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = int(
        scalar(
            """
            SELECT COUNT(*)
            FROM evaluate e
            WHERE IFNULL(e.deleteStatus, 0) = 0
            """
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            e.id, e.addTime, e.evaluate_info AS evaluateInfo, e.evaluate_type AS evaluateType,
            e.evaluate_status AS evaluateStatus, e.evaluate_goods_id AS evaluateGoodsId,
            g.goods_name AS goodsName, gb.name AS goodsBrandName, quc.name AS customerName
        FROM evaluate e
        LEFT JOIN goods g ON e.evaluate_goods_id = g.id
        LEFT JOIN goodsbrand gb ON g.goods_brand_id = gb.id
        LEFT JOIN qd_user_company quc ON e.customer_id = quc.id
        WHERE IFNULL(e.deleteStatus, 0) = 0
        ORDER BY e.addTime DESC
        {clause}
        """,
        page_params,
    )
    return normalize_rows(rows), total


def get_evaluate(evaluate_id: int) -> dict[str, Any] | None:
    return normalize_row(
        fetch_one(
            """
            SELECT
                e.*, g.goods_name AS goodsName, gb.name AS goodsBrandName, quc.name AS customerName
            FROM evaluate e
            LEFT JOIN goods g ON e.evaluate_goods_id = g.id
            LEFT JOIN goodsbrand gb ON g.goods_brand_id = gb.id
            LEFT JOIN qd_user_company quc ON e.customer_id = quc.id
            WHERE e.id=%(id)s LIMIT 1
            """,
            {"id": evaluate_id},
        )
    )


def toggle_evaluate_status(evaluate_id: int, status: int | None = None) -> int | None:
    row = fetch_one("SELECT evaluate_status FROM evaluate WHERE id=%(id)s LIMIT 1", {"id": evaluate_id})
    if not row:
        return None
    if status is None:
        current = int(row.get("evaluate_status") or 0)
        next_val = 1 if current == 0 else 0
    else:
        next_val = 1 if int(status) else 0
    execute(
        "UPDATE evaluate SET evaluate_status=%(val)s WHERE id=%(id)s",
        {"val": next_val, "id": evaluate_id},
    )
    return next_val


# ---------- Consult config ----------
def get_consult_config() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, qd_name AS qdName, service_mobile AS serviceMobile, qd_fax AS qdFax,
               qd_address AS qdAddress, qd_email AS qdEmail
        FROM qd_consult_config
        WHERE IFNULL(delete_status, 0) = 0
        ORDER BY id ASC LIMIT 1
        """
    )
    return normalize_row(row) or {
        "id": None,
        "qdName": "",
        "serviceMobile": "",
        "qdFax": "",
        "qdAddress": "",
        "qdEmail": "",
    }


def save_consult_config(fields: dict[str, Any]) -> int:
    cfg_id = fields.get("id")
    payload = {
        "qd_name": fields.get("qd_name") or "",
        "service_mobile": fields.get("service_mobile") or "",
        "qd_fax": fields.get("qd_fax") or "",
        "qd_address": fields.get("qd_address") or "",
        "qd_email": fields.get("qd_email") or "",
    }
    if cfg_id:
        execute(
            """
            UPDATE qd_consult_config
            SET qd_name=%(qd_name)s, service_mobile=%(service_mobile)s, qd_fax=%(qd_fax)s,
                qd_address=%(qd_address)s, qd_email=%(qd_email)s, update_time=NOW()
            WHERE id=%(id)s
            """,
            {**payload, "id": cfg_id},
        )
        return int(cfg_id)
    return execute_insert(
        """
        INSERT INTO qd_consult_config
            (qd_name, delete_status, qd_email, qd_address, add_time, service_mobile, update_time, qd_fax)
        VALUES
            (%(qd_name)s, 0, %(qd_email)s, %(qd_address)s, NOW(), %(service_mobile)s, NOW(), %(qd_fax)s)
        """,
        payload,
    )
