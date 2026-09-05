from decimal import Decimal
from typing import Any

from apps.orders.services import enrichment as enrich
from apps.orders.repositories import orders as repo
from apps.payments.repositories import user_account as user_account_repo
from qd_common.serialize import to_jsonable


def _page_slice(
    items: list[Any], start: str, length: str, draw: str
) -> dict[str, Any]:
    total = len(items)
    start_i = int(start) if str(start).isdigit() else 0
    length_i = int(length) if str(length).isdigit() else 10
    if length_i <= 0:
        length_i = 10
    begin = max(start_i, 0)
    end = begin + length_i
    page_data = items[begin:end] if begin < total else []
    d = int(draw) if str(draw).isdigit() else 1
    return {
        "draw": d,
        "recordsTotal": total,
        "recordsFiltered": total,
        "error": None,
        "data": page_data,
    }


def get_center_order_data(
    *,
    user_id: int,
    tab_type: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
) -> dict[str, Any]:
    uid, _mobile = repo.user_context(user_id)
    account = user_account_repo.get_or_create(uid)
    stay_apply = Decimal(str(account.get("invoicing_amount") or 0))

    all_orders = repo.customer_orders(uid)
    stay_spent_list: list[dict[str, Any]] = []
    stay_apply_list: list[dict[str, Any]] = []
    stay_repay_list: list[dict[str, Any]] = []

    for order in all_orders:
        st = int(order.get("order_status") or 0)
        oid = int(order["id"])
        if st == 5:
            stay_spent_list.append(order)
            continue
        if st == 41:
            stay_repay_list.append(order)
            continue
        if repo.has_unapplied_bill(oid):
            stay_apply_list.append(order)

    enrich.enrich_orders(stay_spent_list)
    enrich.enrich_orders(stay_apply_list)
    enrich.enrich_orders(stay_repay_list)

    if tab_type == 1:
        page_map = _page_slice(
            [to_jsonable(o) for o in stay_spent_list], start, length, draw
        )
    elif tab_type == 2:
        page_map = _page_slice(
            [to_jsonable(o) for o in stay_apply_list], start, length, draw
        )
    elif tab_type == 3:
        page_map = _page_slice(
            [to_jsonable(o) for o in stay_repay_list], start, length, draw
        )
    else:
        page_map = _page_slice([], start, length, draw)

    return {
        "staySpent": len(stay_spent_list),
        "stayApply": float(stay_apply),
        "stayRepay": len(stay_repay_list),
        "amount": float(account.get("amount") or 0),
        "dataList": page_map,
    }
