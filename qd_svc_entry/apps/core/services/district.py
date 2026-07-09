from typing import Any

from apps.core.db_utils import fetch_all
from qd_common.serialize import to_jsonable


def _row_item(row: dict[str, Any]) -> dict[str, Any]:
    d = to_jsonable(row)
    return {
        "id": d.get("id"),
        "superId": d.get("super_id") or d.get("superId"),
        "disName": d.get("dis_name") or d.get("disName"),
        "disSort": d.get("dis_sort") or d.get("disSort"),
        "type": d.get("type"),
    }


def list_by_super_id(super_id: str) -> list[dict[str, Any]]:
    if super_id in ("-1", ""):
        rows = fetch_all(
            """
            SELECT id, super_id, dis_name, dis_sort, type
            FROM sy_district WHERE type = '1'
            ORDER BY dis_sort ASC
            """
        )
    else:
        rows = fetch_all(
            """
            SELECT id, super_id, dis_name, dis_sort, type
            FROM sy_district WHERE super_id = %(sid)s
            ORDER BY dis_sort ASC
            """,
            {"sid": super_id},
        )
    return [_row_item(dict(r)) for r in rows]


def provinces_cities_tree() -> dict[str, Any]:
    provinces = list_by_super_id("-1")
    first_list: list[dict[str, Any]] = []
    for p in provinces:
        pid = str(p.get("id") or "")
        cities = list_by_super_id(pid)
        sec_list = []
        for c in cities:
            cid = str(c.get("id") or "")
            areas_raw = list_by_super_id(cid)
            areas = [{"id": a.get("id"), "name": a.get("disName")} for a in areas_raw]
            sec_list.append(
                {"id": c.get("id"), "name": c.get("disName"), "areas": areas}
            )
        first_list.append(
            {"id": p.get("id"), "name": p.get("disName"), "citys": sec_list}
        )
    return {"provinces": first_list}
