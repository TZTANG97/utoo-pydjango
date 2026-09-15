from typing import Any

from apps.orders.repositories import orders as repo
from apps.orders.repositories import sale_list as sale_list_repo
from apps.orders.services import enrichment as enrich


def _list_orders(
    *,
    user_id: int,
    start: str,
    length: str,
    draw: str,
    extra_where: str,
    keywords: str,
    join_sql: str = "",
) -> dict[str, Any]:
    _, mobile = repo.user_context(user_id)
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    total, orders = repo.count_and_list(
        user_id=user_id,
        mobile=mobile,
        extra_where=extra_where,
        keywords=keywords,
        join_sql=join_sql,
        offset=offset,
        limit=limit,
    )
    enrich.enrich_orders(orders)
    return {
        "data": orders,
        "draw": int(draw) if draw.isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def my_experiment_order_list(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    tab_type: str = "0",
    keywords: str = "",
    order_id: str = "",
) -> dict[str, Any]:
    kw = keywords or order_id
    extra = ""
    join_sql = ""
    t = (tab_type or "0").strip()
    if t == "1":
        extra = sale_list_repo.RECEIVE_PLAN_PC_EXTRA
        join_sql = sale_list_repo.RECEIVE_PLAN_PC_JOINS
    elif t == "2":
        extra = sale_list_repo.WAITING_EXPERIMENT_EXTRA
    elif t == "3":
        extra = sale_list_repo.EXPERIMENTING_EXTRA
    elif t == "5":
        extra = sale_list_repo.BILLABLE_EXTRA
    elif t == "4":
        extra = " AND t.order_status = 50"
    elif t == "7":
        extra = sale_list_repo.AFTER_SALE_EXTRA
    return _list_orders(
        user_id=user_id,
        start=start,
        length=length,
        draw=draw,
        extra_where=extra,
        keywords=kw,
        join_sql=join_sql,
    )


def experiment_order_list(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    tab_type: str = "",
    keywords: str = "",
    order_status: str = "",
    order_id: str = "",
) -> dict[str, Any]:
    kw = keywords or order_id
    extra = ""
    join_sql = ""
    t = (tab_type or "").strip()
    if t == "1":
        extra = sale_list_repo.BILLABLE_EXTRA
    elif t == "2":
        extra = sale_list_repo.RECEIVE_PLAN_PC_EXTRA
        join_sql = sale_list_repo.RECEIVE_PLAN_PC_JOINS
    elif t == "5":
        extra = " AND t.order_status = 5"
    if order_status and order_status.strip().isdigit():
        extra += f" AND t.order_status = {int(order_status.strip())}"
    return _list_orders(
        user_id=user_id,
        start=start,
        length=length,
        draw=draw,
        extra_where=extra,
        keywords=kw,
        join_sql=join_sql,
    )
