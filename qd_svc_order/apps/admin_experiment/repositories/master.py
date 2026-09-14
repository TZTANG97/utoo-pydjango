from __future__ import annotations

import logging
from typing import Any

from apps.admin_experiment.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

logger = logging.getLogger(__name__)


def _nd(alias: str = "t") -> str:
    return f"IFNULL({alias}.deleteStatus, 0) = 0"


# ---------- experiment_manage (业务一/二/三级类) ----------
def list_manages(
    *,
    type_: int,
    name: str = "",
    parent_id: str = "",
    first_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_nd('t')} AND t.type = %(type)s"
    params: dict[str, Any] = {"type": type_}
    if name:
        where += " AND t.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if parent_id:
        where += " AND t.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id
    if first_id and type_ == 3:
        where += " AND p1.id = %(first_id)s"
        params["first_id"] = first_id

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_manage t
            LEFT JOIN experiment_manage p ON t.parent_id = p.id
            LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
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
            t.id, t.addTime, t.name, t.sequence, t.type, t.parent_id AS parentId,
            t.pt_type AS ptType, t.enname, t.special_type AS specialType,
            t.syuser_id AS syuserId, t.head_user_id AS headUserId,
            t.intro, t.deleteStatus, pt.name AS ptName,
            p.name AS parentName, p1.name AS firstName, p1.id AS firstId
        FROM experiment_manage t
        LEFT JOIN experiment_manage p ON t.parent_id = p.id
        LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
        LEFT JOIN pt_type pt ON t.pt_type = pt.id
        {where}
        ORDER BY CASE WHEN IFNULL(t.sequence, 0) = 0 THEN 1 ELSE 0 END,
                 t.sequence ASC, t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def _parent_clause(parent_id: int | None) -> tuple[str, dict[str, Any]]:
    if parent_id:
        return "AND IFNULL(t.parent_id, 0) = %(pid)s", {"pid": int(parent_id)}
    return "AND IFNULL(t.parent_id, 0) = 0", {}


def manage_name_exists(
    *, name: str, type_: int, parent_id: int | None, exclude_id: int | None = None
) -> bool:
    """同级分类名称不可重复（对齐 Java addClassName.ajax）。"""
    extra, params = _parent_clause(parent_id)
    params.update({"name": name, "type": type_})
    where = f"WHERE {_nd('t')} AND t.type = %(type)s AND t.name = %(name)s {extra}"
    if exclude_id:
        where += " AND t.id <> %(xid)s"
        params["xid"] = int(exclude_id)
    return int(scalar(f"SELECT COUNT(*) FROM experiment_manage t {where}", params) or 0) > 0


def manage_sequence_exists(
    *, sequence: int, type_: int, parent_id: int | None, exclude_id: int | None = None
) -> bool:
    """同级排序序号不可重复（对齐 Java ynexist / upynexist）。"""
    extra, params = _parent_clause(parent_id)
    params.update({"seq": int(sequence), "type": type_})
    where = f"WHERE {_nd('t')} AND t.type = %(type)s AND t.sequence = %(seq)s {extra}"
    if exclude_id:
        where += " AND t.id <> %(xid)s"
        params["xid"] = int(exclude_id)
    return int(scalar(f"SELECT COUNT(*) FROM experiment_manage t {where}", params) or 0) > 0


def list_manage_album(row_id: int, *, exclude_ids: set[int] | None = None) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, path, name FROM accessory
        WHERE IFNULL(deleteStatus, 0) = 0
          AND CAST(exp_of_id AS CHAR) = CAST(%(id)s AS CHAR)
        ORDER BY id ASC
        """,
        {"id": row_id},
    )
    skip = exclude_ids or set()
    out: list[dict[str, Any]] = []
    for r in rows or []:
        try:
            if int(r.get("id") or 0) in skip:
                continue
        except (TypeError, ValueError):
            pass
        out.append(dict(r))
    return out


def list_manage_test_users(row_id: int) -> list[dict[str, Any]]:
    """三级编辑只读：sy_user_expmanage 关联测试账号（对齐 Java suemList）。"""
    try:
        rows = fetch_all(
            """
            SELECT
                sue.id, sue.user_id AS userId, sue.addTime,
                IFNULL(u.true_name, IFNULL(u.user_name, '')) AS userName,
                u.user_name AS loginName
            FROM sy_user_expmanage sue
            LEFT JOIN sy_users u ON CAST(u.id AS CHAR) = CAST(sue.user_id AS CHAR)
            WHERE CAST(sue.exp_manage_id AS CHAR) = CAST(%(id)s AS CHAR)
              AND IFNULL(sue.deleteStatus, 0) = 0
            ORDER BY sue.id ASC
            """,
            {"id": row_id},
        )
        return [dict(r) for r in (rows or [])]
    except Exception:
        return []


def list_manage_logs(row_id: int) -> list[dict[str, Any]]:
    """三级编辑操作记录（表字段：manage_id / info，非 em_id / content）。"""
    try:
        rows = fetch_all(
            """
            SELECT
                l.id, l.addTime, l.info AS content,
                IFNULL(su.true_name, IFNULL(su.user_name, '')) AS addusername
            FROM experiment_manage_log l
            LEFT JOIN sy_users su ON CAST(su.id AS CHAR) = CAST(l.user_id AS CHAR)
            WHERE CAST(l.manage_id AS CHAR) = CAST(%(id)s AS CHAR)
              AND IFNULL(l.deleteStatus, 0) = 0
            ORDER BY l.id DESC
            LIMIT 200
            """,
            {"id": row_id},
        )
        return [dict(r) for r in (rows or [])]
    except Exception:
        logger.exception("list_manage_logs failed row_id=%s", row_id)
        return []


def write_manage_log(*, row_id: int, user_id: str, content: str) -> None:
    if not row_id or not content:
        return
    try:
        execute_insert(
            """
            INSERT INTO experiment_manage_log
                (addTime, deleteStatus, manage_id, user_id, info)
            VALUES (NOW(), 0, %(em)s, %(uid)s, %(ct)s)
            """,
            {"em": int(row_id), "uid": str(user_id or "")[:64], "ct": content[:500]},
        )
    except Exception:
        logger.exception("write_manage_log failed row_id=%s", row_id)


def bind_manage_album(row_id: int, image_ids: list[int]) -> None:
    ids = [int(x) for x in image_ids if x]
    if not ids:
        return
    placeholders = ",".join(str(i) for i in ids)
    try:
        execute(
            f"""
            UPDATE accessory
            SET exp_of_id = %(em)s
            WHERE id IN ({placeholders})
              AND (exp_of_id IS NULL OR exp_of_id = 0 OR CAST(exp_of_id AS CHAR) = CAST(%(em)s AS CHAR))
            """,
            {"em": int(row_id)},
        )
    except Exception:
        pass


def get_manage(row_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.name, t.sequence, t.type, t.parent_id AS parentId,
            t.pt_type AS ptType, t.enname, t.special_type AS specialType,
            t.syuser_id AS syuserId, t.head_user_id AS headUserId,
            IFNULL(syu.true_name, IFNULL(syu.user_name, '')) AS syuserName,
            syu.user_name AS syuserLoginName,
            IFNULL(hu.true_name, IFNULL(hu.user_name, '')) AS headUserName,
            hu.user_name AS headUserLoginName,
            t.intro, t.project_details AS projectDetails,
            t.app_project_details AS appProjectDetails,
            t.manage_main_photo_id AS photoId,
            t.app_manage_main_photo_id AS appPhotoId,
            acc.path AS photoPath, acc.name AS photoName,
            appacc.path AS appPhotoPath, appacc.name AS appPhotoName,
            pt.name AS ptName,
            p.name AS parentName, p1.name AS firstName, p1.id AS firstId
        FROM experiment_manage t
        LEFT JOIN experiment_manage p ON t.parent_id = p.id
        LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
        LEFT JOIN pt_type pt ON t.pt_type = pt.id
        LEFT JOIN accessory acc ON t.manage_main_photo_id = acc.id
        LEFT JOIN accessory appacc ON t.app_manage_main_photo_id = appacc.id
        LEFT JOIN sy_users syu ON CAST(syu.id AS CHAR) = CAST(t.syuser_id AS CHAR)
        LEFT JOIN sy_users hu ON CAST(hu.id AS CHAR) = CAST(t.head_user_id AS CHAR)
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )
    if not row:
        return None
    exclude: set[int] = set()
    for key in ("photoId", "appPhotoId"):
        try:
            if row.get(key):
                exclude.add(int(row[key]))
        except (TypeError, ValueError):
            pass
    row["albumPhotos"] = list_manage_album(row_id, exclude_ids=exclude)
    row["testUsers"] = list_manage_test_users(row_id)
    row["logs"] = list_manage_logs(row_id)
    return row


def save_manage(data: dict[str, Any], *, row_id: int | None = None) -> int:
    payload = {
        **data,
        "photo_id": data.get("photo_id") or None,
        "app_photo_id": data.get("app_photo_id") or None,
    }
    if row_id:
        execute(
            """
            UPDATE experiment_manage
            SET name=%(name)s, sequence=%(sequence)s, parent_id=%(parent_id)s,
                pt_type=%(pt_type)s, enname=%(enname)s, special_type=%(special_type)s,
                syuser_id=%(syuser_id)s, head_user_id=%(head_user_id)s,
                intro=%(intro)s, project_details=%(project_details)s,
                app_project_details=%(app_project_details)s,
                manage_main_photo_id=%(photo_id)s,
                app_manage_main_photo_id=%(app_photo_id)s,
                addTime=IFNULL(addTime, NOW())
            WHERE id=%(id)s
            """,
            {**payload, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO experiment_manage
            (addTime, deleteStatus, name, sequence, type, parent_id, pt_type,
             enname, special_type, syuser_id, head_user_id, intro,
             project_details, app_project_details,
             manage_main_photo_id, app_manage_main_photo_id)
        VALUES
            (NOW(), 0, %(name)s, %(sequence)s, %(type)s, %(parent_id)s, %(pt_type)s,
             %(enname)s, %(special_type)s, %(syuser_id)s, %(head_user_id)s, %(intro)s,
             %(project_details)s, %(app_project_details)s,
             %(photo_id)s, %(app_photo_id)s)
        """,
        payload,
    )


def count_manage_children(parent_id: int, child_type: int | None = None) -> int:
    where = f"WHERE {_nd('t')} AND t.parent_id = %(pid)s"
    params: dict[str, Any] = {"pid": parent_id}
    if child_type is not None:
        where += " AND t.type = %(type)s"
        params["type"] = child_type
    return int(scalar(f"SELECT COUNT(*) FROM experiment_manage t {where}", params) or 0)


def set_manage_status(row_id: int, status: int) -> str | None:
    # 表无独立 status：启用=恢复，禁用=软删；禁用时若有下级则拦截
    if int(status) != 1 and count_manage_children(row_id) > 0:
        return "当前类型还有下级，请删除下级后再操作！"
    delete_status = 0 if int(status) == 1 else 1
    execute(
        "UPDATE experiment_manage SET deleteStatus = %(ds)s WHERE id = %(id)s",
        {"id": row_id, "ds": delete_status},
    )
    return None


def soft_delete_manage(row_id: int) -> str | None:
    """软删；一级/二级有下级时返回错误文案。"""
    row = fetch_one(
        "SELECT type FROM experiment_manage WHERE id = %(id)s LIMIT 1",
        {"id": row_id},
    )
    if not row:
        return "记录不存在"
    type_ = int(row.get("type") or 0)
    if type_ in (1, 2) and count_manage_children(row_id) > 0:
        return "当前类型还有下级，请删除下级后再操作！"
    execute(
        "UPDATE experiment_manage SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )
    return None


def list_pt_types() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT t.id AS value, t.name AS label, t.id, t.name
        FROM pt_type t
        WHERE IFNULL(t.deleteStatus, 0) = 0
        ORDER BY t.addTime DESC, t.id ASC
        LIMIT 500
        """
    )


def list_manage_options(type_: int, parent_id: str = "") -> list[dict[str, Any]]:
    where = f"WHERE {_nd('t')} AND t.type = %(type)s"
    params: dict[str, Any] = {"type": type_}
    if parent_id:
        where += " AND t.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id
    return fetch_all(
        f"""
        SELECT t.id AS value, t.name AS label, t.parent_id AS parentId
        FROM experiment_manage t
        {where}
        ORDER BY t.sequence ASC, t.name ASC
        LIMIT 1000
        """,
        params,
    )


def query_all_manages(type_: int) -> list[dict[str, Any]]:
    """对齐 Java experimentManage/queryAll.ajax。"""
    return fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.name, t.sequence, t.type,
            t.parent_id AS parentId, t.pt_type AS ptType, t.intro
        FROM experiment_manage t
        WHERE {_nd('t')} AND t.type = %(type)s
        ORDER BY t.sequence ASC, t.id ASC
        LIMIT 2000
        """,
        {"type": type_},
    )


def list_manages_by_parent(parent_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.name, t.sequence, t.type,
            t.parent_id AS parentId, t.pt_type AS ptType, t.intro
        FROM experiment_manage t
        WHERE {_nd('t')} AND t.parent_id = %(pid)s
        ORDER BY t.sequence ASC, t.id ASC
        LIMIT 2000
        """,
        {"pid": parent_id},
    )


# ---------- experiment_project ----------
def list_projects(
    *,
    name: str = "",
    first_id: str = "",
    sec_id: str = "",
    third_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_nd('t')}"
    params: dict[str, Any] = {}
    if name:
        where += " AND t.project_name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if third_id:
        where += " AND t.class_id = %(third_id)s"
        params["third_id"] = third_id
    elif sec_id:
        where += " AND m.parent_id = %(sec_id)s"
        params["sec_id"] = sec_id
    elif first_id:
        where += " AND m2.parent_id = %(first_id)s"
        params["first_id"] = first_id

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_project t
            LEFT JOIN experiment_manage m ON t.class_id = m.id
            LEFT JOIN experiment_manage m2 ON m.parent_id = m2.id
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
            t.id, t.addTime, t.project_name AS projectName, t.class_id AS classId,
            t.test_price AS testPrice, t.country,
            m.name AS className, m2.name AS secName, m3.name AS firstName
        FROM experiment_project t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        LEFT JOIN experiment_manage m2 ON m.parent_id = m2.id
        LEFT JOIN experiment_manage m3 ON m2.parent_id = m3.id
        {where}
        ORDER BY t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_project(row_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.project_name AS projectName, t.class_id AS classId,
            t.test_price AS testPrice, t.country,
            m.name AS className, m.parent_id AS secId, m2.parent_id AS firstId
        FROM experiment_project t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        LEFT JOIN experiment_manage m2 ON m.parent_id = m2.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )


def save_project(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        execute(
            """
            UPDATE experiment_project
            SET project_name=%(project_name)s,
                class_id=%(class_id)s,
                test_price=%(test_price)s,
                country=%(country)s
            WHERE id=%(id)s
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO experiment_project
            (addTime, deleteStatus, project_name, class_id, test_price, country)
        VALUES
            (NOW(), 0, %(project_name)s, %(class_id)s, %(test_price)s, %(country)s)
        """,
        data,
    )


def soft_delete_project(row_id: int) -> None:
    execute(
        "UPDATE experiment_project SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )


# ---------- experiment_goods ----------
def list_goods(
    *,
    name: str = "",
    brand_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_nd('t')}"
    params: dict[str, Any] = {}
    if name:
        where += " AND t.goods_name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if brand_id:
        where += " AND t.goods_brand_id = %(brand_id)s"
        params["brand_id"] = brand_id
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_goods t
            LEFT JOIN goodsbrand b ON t.goods_brand_id = b.id
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
            t.id, t.addTime, t.goods_name AS goodsName, t.goods_model AS goodsModel,
            t.goods_brand_id AS brandId, b.name AS brandName
        FROM experiment_goods t
        LEFT JOIN goodsbrand b ON t.goods_brand_id = b.id
        {where}
        ORDER BY t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_goods(row_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.goods_name AS goodsName, t.goods_model AS goodsModel,
            t.goods_brand_id AS brandId, b.name AS brandName
        FROM experiment_goods t
        LEFT JOIN goodsbrand b ON t.goods_brand_id = b.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )


def goods_name_exists(
    *, name: str, brand_id: int | None, exclude_id: int | None = None
) -> bool:
    """同品牌产品名称不可重复（对齐 Java addGoodsName.ajax）。"""
    params: dict[str, Any] = {"name": name}
    where = f"WHERE {_nd('t')} AND t.goods_name = %(name)s"
    if brand_id:
        where += " AND t.goods_brand_id = %(bid)s"
        params["bid"] = int(brand_id)
    else:
        where += " AND IFNULL(t.goods_brand_id, 0) = 0"
    if exclude_id:
        where += " AND t.id <> %(xid)s"
        params["xid"] = int(exclude_id)
    return int(scalar(f"SELECT COUNT(*) FROM experiment_goods t {where}", params) or 0) > 0


def save_goods(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        execute(
            """
            UPDATE experiment_goods
            SET goods_name=%(goods_name)s, goods_brand_id=%(goods_brand_id)s,
                goods_model=%(goods_model)s
            WHERE id=%(id)s
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO experiment_goods
            (addTime, deleteStatus, goods_name, goods_brand_id, goods_model)
        VALUES (NOW(), 0, %(goods_name)s, %(goods_brand_id)s, %(goods_model)s)
        """,
        data,
    )


def soft_delete_goods(row_id: int) -> None:
    execute(
        "UPDATE experiment_goods SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )


# ---------- goodsbrand type=2 (实验产品品牌) ----------
def list_exp_brands(
    *,
    name: str = "",
    add_time: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java experiment_goods_brand_list（type=2）。"""
    where = f"WHERE {_nd('b')} AND b.type = 2 AND IFNULL(b.audit, 1) = 1"
    params: dict[str, Any] = {}
    if name:
        where += " AND b.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if add_time:
        # Java 单日创建时间筛选
        where += " AND DATE(b.addTime) = %(add_time)s"
        params["add_time"] = add_time[:10]
    total = int(scalar(f"SELECT COUNT(*) FROM goodsbrand b {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            b.id, b.addTime, b.name, b.first_word AS firstWord, b.sequence,
            b.en_name AS enName
        FROM goodsbrand b
        {where}
        ORDER BY b.sequence ASC, b.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        at = r.get("addTime")
        r["addTime"] = str(at)[:19] if at else ""
    return rows, total


def get_exp_brand(row_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, addTime, name, first_word AS firstWord, sequence, en_name AS enName, type
        FROM goodsbrand
        WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": row_id},
    )


def exp_brand_name_exists(*, name: str, exclude_id: int | None = None) -> bool:
    """实验品牌名称不可重复（对齐 Java goods_brand_verify.htm）。"""
    params: dict[str, Any] = {"name": name}
    where = f"WHERE {_nd('b')} AND b.type = 2 AND b.name = %(name)s"
    if exclude_id:
        where += " AND b.id <> %(xid)s"
        params["xid"] = int(exclude_id)
    return int(scalar(f"SELECT COUNT(*) FROM goodsbrand b {where}", params) or 0) > 0


def save_exp_brand(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        execute(
            """
            UPDATE goodsbrand
            SET name=%(name)s, first_word=%(first_word)s, sequence=%(sequence)s,
                en_name=%(en_name)s
            WHERE id=%(id)s AND type=2
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO goodsbrand
            (addTime, deleteStatus, audit, name, recommend, sequence, userStatus,
             first_word, type, en_name)
        VALUES
            (NOW(), 0, 1, %(name)s, 0, %(sequence)s, 0, %(first_word)s, 2, %(en_name)s)
        """,
        data,
    )


def soft_delete_exp_brand(row_id: int) -> None:
    execute(
        "UPDATE goodsbrand SET deleteStatus = 1 WHERE id = %(id)s AND type = 2",
        {"id": row_id},
    )


def list_exp_brand_options() -> list[dict[str, Any]]:
    """对齐 Java goodsbrand/queryBrand.ajax?type=2 → getAllByType。"""
    return fetch_all(
        """
        SELECT id AS value, name AS label
        FROM goodsbrand
        WHERE IFNULL(deleteStatus, 0) = 0
          AND CAST(IFNULL(type, 0) AS SIGNED) = 2
          AND IFNULL(audit, 1) = 1
        ORDER BY IFNULL(sequence, 0) ASC, id DESC, name ASC
        LIMIT 5000
        """
    )


# ---------- sample_attribute_manage ----------
def list_sample_attrs(
    *,
    type_: int,
    name: str = "",
    parent_id: str = "",
    first_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = f"WHERE {_nd('t')} AND t.type = %(type)s"
    params: dict[str, Any] = {"type": type_}
    if name:
        where += " AND t.sttribute_name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if parent_id:
        where += " AND t.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id
    if first_id and type_ == 3:
        where += " AND p2.id = %(first_id)s"
        params["first_id"] = first_id

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM sample_attribute_manage t
            LEFT JOIN sample_attribute_manage p ON t.parent_id = p.id
            LEFT JOIN sample_attribute_manage p2 ON p.parent_id = p2.id
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
            t.id, t.addTime, t.sttribute_name AS name, t.type, t.parent_id AS parentId,
            t.special_id AS specialId, t.selection, t.deleteStatus,
            p.sttribute_name AS parentName, p2.sttribute_name AS firstName, p2.id AS firstId
        FROM sample_attribute_manage t
        LEFT JOIN sample_attribute_manage p ON t.parent_id = p.id
        LEFT JOIN sample_attribute_manage p2 ON p.parent_id = p2.id
        {where}
        ORDER BY t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        sel = str(r.get("selection") or "")
        r["selectionLabel"] = {"1": "单选", "2": "多选"}.get(sel, sel or "-")
    return rows, total


def get_sample_attr(row_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.sttribute_name AS name, t.type, t.parent_id AS parentId,
            t.special_id AS specialId, t.selection,
            p.parent_id AS firstId, p.sttribute_name AS parentName
        FROM sample_attribute_manage t
        LEFT JOIN sample_attribute_manage p ON t.parent_id = p.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )


def special_id_exists(special_id: int, *, exclude_id: int | None = None) -> bool:
    """对齐 Java sampleAttributeManageList815：一级特殊字段编号唯一。"""
    where = f"WHERE {_nd('t')} AND t.type = 1 AND t.special_id = %(sid)s"
    params: dict[str, Any] = {"sid": special_id}
    if exclude_id:
        where += " AND t.id <> %(eid)s"
        params["eid"] = exclude_id
    return int(scalar(f"SELECT COUNT(*) FROM sample_attribute_manage t {where}", params) or 0) > 0


def count_sample_attr_children(parent_id: int) -> int:
    return int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM sample_attribute_manage t
            WHERE {_nd('t')} AND t.parent_id = %(pid)s
            """,
            {"pid": parent_id},
        )
        or 0
    )


def save_sample_attr(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        sets = [
            "sttribute_name=%(name)s",
            "parent_id=%(parent_id)s",
            "special_id=%(special_id)s",
        ]
        if "selection" in data:
            sets.append("selection=%(selection)s")
        execute(
            f"""
            UPDATE sample_attribute_manage
            SET {', '.join(sets)}
            WHERE id=%(id)s
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO sample_attribute_manage
            (addTime, deleteStatus, sttribute_name, type, parent_id, special_id, selection)
        VALUES
            (NOW(), 0, %(name)s, %(type)s, %(parent_id)s, %(special_id)s, %(selection)s)
        """,
        {**data, "selection": data.get("selection")},
    )


def set_sample_attr_status(row_id: int, status: int) -> None:
    delete_status = 0 if int(status) == 1 else 1
    execute(
        "UPDATE sample_attribute_manage SET deleteStatus = %(ds)s WHERE id = %(id)s",
        {"id": row_id, "ds": delete_status},
    )


def soft_delete_sample_attr(row_id: int) -> str | None:
    """删除；有下级时返回错误文案（对齐 Java deltwo）。"""
    if count_sample_attr_children(row_id) > 0:
        return "该属性下存在子属性，请先删除子属性！"
    execute(
        "UPDATE sample_attribute_manage SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )
    return None


def list_sample_attr_options(type_: int, parent_id: str = "") -> list[dict[str, Any]]:
    where = f"WHERE {_nd('t')} AND t.type = %(type)s"
    params: dict[str, Any] = {"type": type_}
    if parent_id:
        where += " AND t.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id
    return fetch_all(
        f"""
        SELECT t.id AS value, t.sttribute_name AS label, t.parent_id AS parentId
        FROM sample_attribute_manage t
        {where}
        ORDER BY t.id ASC
        LIMIT 1000
        """,
        params,
    )
