from typing import Any

from apps.orders.services import enrichment as enrich
from apps.orders.repositories import orders as repo
from qd_common.serialize import to_jsonable


def _parse_page(*, start: str, length: str, draw: str) -> tuple[int, int, int]:
    draw_n = int(draw) if str(draw).isdigit() else 1
    offset = int(start) if str(start).isdigit() else 0
    if str(length) == "-1":
        limit = 1000
    elif str(length).isdigit():
        limit = int(length)
    else:
        limit = 10
    return draw_n, offset, limit


def _enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    children = [enrich.enrich_experiment_child_row(dict(r)) for r in rows]
    enrich.resolve_child_project_names(children)
    for c in children:
        c["reference_price"] = to_jsonable(
            c.get("reference_price") or c.get("referencePrice") or 0
        )
        c["referencePrice"] = c["reference_price"]
    return children


def child_forms_by_sale_order(
    *,
    user_id: int,
    of_id: str = "",
    order_id: str = "",
    start: str = "0",
    length: str = "10",
    draw: str = "1",
) -> dict[str, Any]:
    _, mobile = repo.user_context(user_id)
    draw_n, offset, limit = _parse_page(start=start, length=length, draw=draw)
    empty = {
        "data": [],
        "draw": draw_n,
        "recordsTotal": 0,
        "recordsFiltered": 0,
    }
    if not of_id.isdigit():
        return empty

    parent = repo.get_sale_order_for_user(
        order_id=int(of_id), user_id=user_id, mobile=mobile
    )
    if not parent:
        return empty

    total, rows = repo.list_child_forms_by_sale(
        of_id=int(of_id),
        order_id_kw=order_id,
        offset=offset,
        limit=limit,
    )
    children = _enrich_rows(rows)
    return {
        "data": children,
        "draw": draw_n,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def child_forms_by_sale_order_dpt(
    *,
    of_id: str = "",
    order_id: str = "",
    start: str = "0",
    length: str = "10",
    draw: str = "1",
) -> dict[str, Any]:
    """员工端产品列表 — 不按客户归属过滤，返回顶层 DataTables。"""
    draw_n, offset, limit = _parse_page(start=start, length=length, draw=draw)
    empty = {
        "data": [],
        "draw": draw_n,
        "recordsTotal": 0,
        "recordsFiltered": 0,
    }
    if not str(of_id).isdigit():
        return empty

    total, rows = repo.list_child_forms_by_sale(
        of_id=int(of_id),
        order_id_kw=order_id or "",
        offset=offset,
        limit=limit,
    )
    children = _enrich_rows(rows)
    return {
        "data": children,
        "draw": draw_n,
        "recordsTotal": total,
        "recordsFiltered": total,
    }
