"""预约单 PDF 数据 — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any, Optional

from apps.orders.repositories import print_pdf as print_pdf_repo
from apps.orders.repositories import orders as repo
from qd_common.serialize import to_jsonable


def print_pdf_info(*, user_id: int, order_id: int) -> Optional[dict[str, Any]]:
    _, mobile = repo.user_context(user_id)
    if not repo.get_sale_order_for_user(
        order_id=order_id, user_id=user_id, mobile=mobile
    ):
        return None

    rows = print_pdf_repo.fetch_print_pdf_rows(order_id)
    if not rows:
        return None

    first = dict(rows[0])
    address = first.get("send_address") or first.get("sc_send_address") or ""
    test_addr_id = first.get("test_address_id")
    if test_addr_id:
        ta = print_pdf_repo.get_test_address(int(test_addr_id))
        if ta and ta.get("address"):
            address = ta["address"]

    reverso = first.get("reverso_context") or first.get("sc_reverso_context")
    recovery: int | None = None
    if reverso is not None and str(reverso).strip() != "":
        try:
            recovery = int(reverso)
        except (TypeError, ValueError):
            recovery = 1 if str(reverso) == "1" else 2

    child_list: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row in rows:
        r = dict(row)
        cid = r.get("cid")
        if not cid or int(cid) in seen:
            continue
        seen.add(int(cid))
        child_list.append(
            to_jsonable(
                {
                    "id": cid,
                    "experiment_class_name": r.get("experiment_class_name") or "",
                    "orderId": r.get("ordc_id") or "",
                    "goodsName": r.get("goods_name") or "",
                    "goodsNums": r.get("goods_nums"),
                    "experiment_project_name": r.get("experiment_project_name") or "",
                    "sample_id": r.get("sample_id"),
                    "main_component": r.get("main_component") or "",
                    "is_magnetic": r.get("is_magnetic"),
                    "is_gold_spraying": r.get("is_gold_spraying"),
                    "attribute_id": r.get("attribute_id") or "",
                    "gold_desc": r.get("gold_desc") or "",
                }
            )
        )

    return {
        "id": first.get("eid"),
        "order_id": first.get("ord_id") or "",
        "addTime": to_jsonable(first.get("addTime")),
        "userName": first.get("userName") or "",
        "mobile": first.get("sc_mobile") or "",
        "sampleDelivery": {
            "address": address,
            "recovery": recovery,
        },
        "childList": child_list,
    }
