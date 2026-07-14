from __future__ import annotations

from typing import Any

from apps.admin_experiment.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


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
            t.pt_type AS ptType, t.intro, t.deleteStatus,
            p.name AS parentName, p1.name AS firstName, p1.id AS firstId
        FROM experiment_manage t
        LEFT JOIN experiment_manage p ON t.parent_id = p.id
        LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
        {where}
        ORDER BY t.sequence ASC, t.id DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_manage(row_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.name, t.sequence, t.type, t.parent_id AS parentId,
            t.pt_type AS ptType, t.intro, t.manage_main_photo_id AS photoId,
            p.name AS parentName, p1.name AS firstName, p1.id AS firstId
        FROM experiment_manage t
        LEFT JOIN experiment_manage p ON t.parent_id = p.id
        LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )


def save_manage(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        execute(
            """
            UPDATE experiment_manage
            SET name=%(name)s, sequence=%(sequence)s, parent_id=%(parent_id)s,
                pt_type=%(pt_type)s, intro=%(intro)s
            WHERE id=%(id)s
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO experiment_manage
            (addTime, deleteStatus, name, sequence, type, parent_id, pt_type, intro)
        VALUES
            (NOW(), 0, %(name)s, %(sequence)s, %(type)s, %(parent_id)s, %(pt_type)s, %(intro)s)
        """,
        data,
    )


def set_manage_status(row_id: int, status: int) -> None:
    # 表无独立 status：启用=恢复，禁用=软删
    delete_status = 0 if int(status) == 1 else 1
    execute(
        "UPDATE experiment_manage SET deleteStatus = %(ds)s WHERE id = %(id)s",
        {"id": row_id, "ds": delete_status},
    )


def soft_delete_manage(row_id: int) -> None:
    execute(
        "UPDATE experiment_manage SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
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
            SET project_name=%(project_name)s, class_id=%(class_id)s
            WHERE id=%(id)s
            """,
            {**data, "id": row_id},
        )
        return row_id
    return execute_insert(
        """
        INSERT INTO experiment_project (addTime, deleteStatus, project_name, class_id)
        VALUES (NOW(), 0, %(project_name)s, %(class_id)s)
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
    return fetch_all(
        """
        SELECT id AS value, name AS label
        FROM goodsbrand
        WHERE IFNULL(deleteStatus, 0) = 0 AND type = 2 AND IFNULL(audit, 1) = 1
        ORDER BY sequence ASC, name ASC
        LIMIT 1000
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
            t.special_id AS specialId, t.selection
        FROM sample_attribute_manage t
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": row_id},
    )


def save_sample_attr(data: dict[str, Any], *, row_id: int | None = None) -> int:
    if row_id:
        execute(
            """
            UPDATE sample_attribute_manage
            SET sttribute_name=%(name)s, parent_id=%(parent_id)s,
                special_id=%(special_id)s, selection=%(selection)s
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
        data,
    )


def set_sample_attr_status(row_id: int, status: int) -> None:
    delete_status = 0 if int(status) == 1 else 1
    execute(
        "UPDATE sample_attribute_manage SET deleteStatus = %(ds)s WHERE id = %(id)s",
        {"id": row_id, "ds": delete_status},
    )


def soft_delete_sample_attr(row_id: int) -> None:
    execute(
        "UPDATE sample_attribute_manage SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": row_id},
    )


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
