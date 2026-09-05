from typing import Any

from apps.invoices.repositories import invoice as repo
from apps.invoices.services.summary import stay_apply_money


def get_invoice_list_page(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    inv_type: int | None = 2,
    order_id: str = "",
) -> dict[str, Any]:
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    draw_n = int(draw) if draw.isdigit() else 1
    total = repo.count_invoice_apply_logs(
        user_id=user_id, inv_type=inv_type, order_id_kw=order_id
    )
    rows = repo.list_invoice_apply_logs(
        user_id=user_id,
        offset=offset,
        limit=limit,
        inv_type=inv_type,
        order_id_kw=order_id,
    )
    stay = stay_apply_money(user_id)
    return {
        "stayApplyMoney": stay,
        "data": {
            "data": rows,
            "draw": draw_n,
            "recordsTotal": total,
            "recordsFiltered": total,
        },
    }
