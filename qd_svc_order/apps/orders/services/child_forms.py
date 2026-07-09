from typing import Any

from apps.orders.services import enrichment as enrich
from apps.orders.repositories import orders as repo


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
    draw_n = int(draw) if draw.isdigit() else 1
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

    limit = int(length) if length.isdigit() else 10
    if length == "-1":
        limit = 1000
    offset = int(start) if start.isdigit() else 0

    total, rows = repo.list_child_forms_by_sale(
        of_id=int(of_id),
        order_id_kw=order_id,
        offset=offset,
        limit=limit,
    )
    children = [enrich.enrich_experiment_child_row(dict(r)) for r in rows]
    enrich.resolve_child_project_names(children)
    return {
        "data": children,
        "draw": draw_n,
        "recordsTotal": total,
        "recordsFiltered": total,
    }
