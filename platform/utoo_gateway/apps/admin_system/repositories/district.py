from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_districts(
    *,
    super_id: str = "",
    dis_name: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # 对齐 Java load.jsp：mustParamNames=superId，根目录为 super_id='0'
    if not super_id:
        super_id = "0"
    where = "WHERE super_id = %(super_id)s"
    params: dict[str, Any] = {"super_id": super_id}
    if dis_name:
        where += " AND dis_name LIKE %(dis_name)s"
        params["dis_name"] = f"%{dis_name}%"
    total = scalar(f"SELECT COUNT(*) FROM sy_district {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, super_id, dis_sort, dis_name, dis_desc, type, area_id
        FROM sy_district
        {where}
        ORDER BY dis_sort ASC, dis_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_district(row) for row in rows], int(total)


def get_district(district_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, super_id, dis_sort, dis_name, dis_desc, type, area_id
        FROM sy_district WHERE id = %(id)s
        """,
        {"id": district_id},
    )
    return _normalize_district(row) if row else None


def list_children(super_id: str) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, super_id, dis_sort, dis_name, dis_desc, type, area_id
        FROM sy_district
        WHERE super_id = %(super_id)s
        ORDER BY dis_sort ASC
        """,
        {"super_id": super_id},
    )
    return [_normalize_district(row) for row in rows]


def insert_district(data: dict[str, Any]) -> str:
    district_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_district
            (id, super_id, dis_sort, dis_name, dis_desc, type, area_id)
        VALUES
            (%(id)s, %(super_id)s, %(dis_sort)s, %(dis_name)s,
             %(dis_desc)s, %(type)s, %(area_id)s)
        """,
        {
            "id": district_id,
            "super_id": data.get("super_id") or "0",
            "dis_sort": int(data.get("dis_sort") or 0),
            "dis_name": data.get("dis_name") or "",
            "dis_desc": data.get("dis_desc"),
            "type": data.get("type"),
            "area_id": data.get("area_id"),
        },
    )
    return district_id


def update_district(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_district
        SET super_id = %(super_id)s,
            dis_sort = %(dis_sort)s,
            dis_name = %(dis_name)s,
            dis_desc = %(dis_desc)s,
            type = %(type)s,
            area_id = %(area_id)s
        WHERE id = %(id)s
        """,
        data,
    )


def delete_district(district_id: str) -> None:
    execute("DELETE FROM sy_district WHERE id = %(id)s", {"id": district_id})


def _normalize_district(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "superId": row.get("super_id"),
        "disSort": row.get("dis_sort"),
        "disName": row.get("dis_name"),
        "disDesc": row.get("dis_desc"),
        "type": row.get("type"),
        "areaId": row.get("area_id"),
    }
