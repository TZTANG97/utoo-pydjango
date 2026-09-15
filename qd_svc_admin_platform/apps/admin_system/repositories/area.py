from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

# 列表/下拉仅未删除记录；不做硬唯一索引，避免历史脏数据迁移失败
_ACTIVE_WHERE = "deleteStatus = 0"


def list_areas(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar(f"SELECT COUNT(*) FROM trans_area WHERE {_ACTIVE_WHERE}")
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, areaName, addTime, deleteStatus
        FROM trans_area
        WHERE {_ACTIVE_WHERE}
        ORDER BY addTime DESC
        {clause}
        """,
        page_params,
    )
    return [_normalize_area(row) for row in rows], int(total)


def find_by_name(area_name: str, *, exclude_id: int | None = None) -> dict[str, Any] | None:
    """未删除记录中按名称查重；编辑时传 exclude_id 排除自身。"""
    sql = f"""
        SELECT id FROM trans_area
        WHERE areaName = %(name)s AND {_ACTIVE_WHERE}
    """
    params: dict[str, Any] = {"name": area_name}
    if exclude_id is not None:
        sql += " AND id <> %(exclude_id)s"
        params["exclude_id"] = int(exclude_id)
    sql += " LIMIT 1"
    return fetch_one(sql, params)


def insert_area(area_name: str) -> int:
    return execute_insert(
        """
        INSERT INTO trans_area (areaName, addTime, deleteStatus)
        VALUES (%(areaName)s, NOW(), 0)
        """,
        {"areaName": area_name},
    )


def update_area_name(area_id: int, area_name: str) -> None:
    execute(
        "UPDATE trans_area SET areaName = %(areaName)s WHERE id = %(id)s",
        {"id": area_id, "areaName": area_name},
    )


def soft_delete_area(area_id: int) -> None:
    execute(
        "UPDATE trans_area SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": area_id},
    )


def list_area_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        f"""
        SELECT id, areaName
        FROM trans_area
        WHERE {_ACTIVE_WHERE}
        ORDER BY areaName ASC, id ASC
        """
    )
    return [{"id": r["id"], "areaName": r.get("areaName")} for r in rows]


def _normalize_area(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "areaName": row.get("areaName"),
        "addTime": row.get("addTime"),
        "deleteStatus": bool(row.get("deleteStatus")),
    }
