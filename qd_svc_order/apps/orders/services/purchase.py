from typing import Any

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.constants import STATUS_STR, purchase_order_status_str
from apps.orders.repositories import accessory_list as acc_repo
from apps.orders.repositories import orders as repo
from apps.orders.services import enrichment as enrich
from apps.orders.services import sale_detail_enrich as sale_enrich
from qd_common.serialize import to_jsonable


def purchase_order_detail(*, user_id: int, order_id: int) -> dict[str, Any]:
    _, mobile = repo.user_context(user_id)
    empty: dict[str, Any] = {
        "of": None,
        "logs": [],
        "childs": [],
        "files": [],
        "testFiles": [],
        "order_type": 10,
    }
    if order_id <= 0:
        return empty

    of = repo.get_purchase_order_for_user(
        order_id=order_id, user_id=user_id, mobile=mobile
    )
    if not of:
        return empty

    oid = int(of["id"])
    status = int(of.get("order_status") or 0)
    of["order_statusstr"] = purchase_order_status_str(status)
    of["totalPrice"] = to_jsonable(of.get("totalPrice") or of.get("total_price") or 0)

    childs: list[dict[str, Any]] = []
    parent_id = of.get("parent_id")
    if parent_id:
        parent = repo.get_sale_order_for_user(
            order_id=int(parent_id), user_id=user_id, mobile=mobile
        )
        if parent:
            of["parentOf"] = {
                "id": parent.get("id"),
                "order_id": parent.get("order_id"),
                "order_status": parent.get("order_status"),
                "order_statusstr": STATUS_STR.get(
                    int(parent.get("order_status") or 0), "处理中"
                ),
            }
            pcid = parent.get("class_id")
            if pcid:
                em = repo.get_experiment_manage(int(pcid))
                of["testClass"] = {
                    "id": int(pcid),
                    "name": (em.get("name") if em else "") or "实验订单",
                }
        raw_childs = repo.load_purchase_line_children(oid)
        childs = [enrich.enrich_experiment_child_row(dict(c)) for c in raw_childs]
        enrich.resolve_child_project_names(childs)
        for c in childs:
            st = int(c.get("order_status") or 0)
            c["ispcfc"] = False
            c["ispcqr"] = False
            if int(of.get("is_online") or 0) == 1 and st in (39, 41):
                if c.get("is_sure") is None:
                    c["ispcfc"] = True
                    c["ispcqr"] = True

    config = get_config_row()
    image_base = image_web_server(config) or ""
    files = sale_enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, file_type=3),
        image_base,
    )
    test_files = sale_enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, file_type=4),
        image_base,
    )
    return {
        **empty,
        "of": to_jsonable(of),
        "childs": childs,
        "logs": repo.load_logs(oid),
        "files": files,
        "testFiles": test_files,
    }


def purchase_orders_by_sale(
    *,
    user_id: int,
    of_id: str = "",
    order_id: str = "",
    start: str = "0",
    length: str = "10",
    draw: str = "1",
) -> dict[str, Any]:
    _, mobile = repo.user_context(user_id)
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    draw_n = int(draw) if draw.isdigit() else 1
    empty = {
        "data": [],
        "draw": draw_n,
        "recordsTotal": 0,
        "recordsFiltered": 0,
    }
    if not of_id.isdigit():
        return empty

    parent_id = int(of_id)
    parent = repo.get_sale_order_for_user(
        order_id=parent_id, user_id=user_id, mobile=mobile
    )
    if not parent:
        return empty

    total, rows = repo.list_purchase_orders_by_sale(
        parent_id=parent_id,
        order_id_kw=order_id,
        offset=offset,
        limit=limit,
    )
    orders = []
    for r in rows:
        o = dict(r)
        st = int(o.get("order_status") or 0)
        o["order_statusstr"] = purchase_order_status_str(st)
        o["totalPrice"] = to_jsonable(o.get("totalPrice") or o.get("total_price") or 0)
        orders.append(o)
    return {
        "data": orders,
        "draw": draw_n,
        "recordsTotal": total,
        "recordsFiltered": total,
    }
