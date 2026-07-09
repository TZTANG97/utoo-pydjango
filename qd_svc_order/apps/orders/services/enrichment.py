from typing import Any

from apps.orders.constants import STATUS_STR, child_order_status_str
from apps.orders.repositories import catalog as catalog_repo
from apps.orders.repositories import orders as repo
from qd_common.serialize import to_jsonable


def enrich_experiment_child_row(d: dict[str, Any]) -> dict[str, Any]:
    oid = d.get("order_id") or d.get("orderId") or ""
    d["orderId"] = oid
    d["order_id"] = oid
    d["goodsNums"] = to_jsonable(d.get("goods_nums") or d.get("goodsNums") or 0)
    d["goodsPrice"] = to_jsonable(d.get("goods_price") or d.get("goodsPrice") or 0)
    d["goodsName"] = d.get("goods_name") or d.get("goodsName") or ""
    d["goodsSpec"] = d.get("goods_spec") or d.get("goodsSpec") or ""
    d["goodsBrandName"] = d.get("goods_brand_name") or d.get("goodsBrandName") or ""
    st = int(d.get("order_status") or d.get("orderStatus") or 0)
    d["order_status"] = st
    d["orderStautsStr"] = child_order_status_str(st)
    d["experiment_project_name"] = d.get("experiment_project_name") or ""
    d["experiment_class_name"] = d.get("experiment_class_name") or ""
    return d


def resolve_child_project_names(children: list[dict[str, Any]]) -> None:
    ids: list[int] = []
    for c in children:
        pid = c.get("experiment_project_id")
        name = str(c.get("experiment_project_name") or "").strip()
        if pid and (not name or name.isdigit()):
            try:
                ids.append(int(pid))
            except (TypeError, ValueError):
                pass
    if not ids:
        return
    name_map = catalog_repo.fetch_project_name_map(ids)
    for c in children:
        pid = c.get("experiment_project_id")
        if pid is not None:
            try:
                key = int(pid)
                if key in name_map and name_map[key]:
                    c["experiment_project_name"] = name_map[key]
            except (TypeError, ValueError):
                pass


def enrich_child_row(d: dict[str, Any]) -> dict[str, Any]:
    oid = d.get("order_id") or d.get("orderId") or ""
    d["orderId"] = oid
    d["order_id"] = oid
    st = int(d.get("order_status") or d.get("orderStatus") or 0)
    d["order_status"] = st
    d["orderStautsStr"] = child_order_status_str(st)
    d["goodsName"] = d.get("goods_name") or d.get("goodsName") or ""
    return d


def enrich_sale_order_row(d: dict[str, Any]) -> dict[str, Any]:
    oid = d.get("order_id") or d.get("orderId") or ""
    d["order_id"] = oid
    d["orderId"] = oid
    d["totalPrice"] = to_jsonable(d.get("totalPrice") or d.get("total_price") or 0)
    st = int(d.get("order_status") or d.get("orderStatus") or 0)
    d["order_status"] = st
    d["orderStatus"] = st
    return d


def enrich_orders(orders: list[dict[str, Any]]) -> None:
    ids = [int(o["id"]) for o in orders if o.get("id")]
    children_map = repo.load_children(ids)
    for o in orders:
        enrich_sale_order_row(o)
        oid = int(o.get("id") or 0)
        children = [
            enrich_experiment_child_row(dict(c))
            for c in children_map.get(oid, [])
        ]
        o["orderChildForms"] = children
        st = int(o.get("order_status") or 0)
        o["order_statusstr"] = STATUS_STR.get(st, "处理中")
        skje = repo.sum_bill(oid, 2)
        o["xsskje"] = skje
        total = float(o.get("totalPrice") or 0)
        o["isfk"] = "1" if skje >= total and total > 0 else "0"
        o["iskp"] = "2" if int(o.get("invoiceType") or 0) != 1 else "0"
        o["kpShow"] = "0"
        o["dkpje"] = 0
        o["company_account"] = ""
        o["printYydShow"] = False
        o["testFiles"] = []
        o["ispjqx"] = False
        o["fcShow"] = False
        o["wcShow"] = False
        o["isUploadReceipt"] = 0
