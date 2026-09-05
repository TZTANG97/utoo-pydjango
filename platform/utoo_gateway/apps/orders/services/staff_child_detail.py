"""员工端实验子订单详情 — 对齐小程序 staff/child_detail。"""
from __future__ import annotations

from typing import Any

from apps.admin_experiment.repositories import orders as admin_order_repo
from apps.admin_experiment.repositories import sample_flow as sample_flow_repo
from apps.core.db_utils import fetch_all, fetch_one
from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.constants import STATUS_STR, purchase_order_status_str
from apps.orders.repositories import accessory_list as acc_repo
from apps.orders.repositories import orders as repo
from apps.orders.services import enrichment as child_enrich
from apps.orders.services import sale_detail_enrich as enrich
from apps.orders.services.staff_sale_detail import (
    _load_supplier_user,
    ensure_mp_of_fields,
)
from qd_common.serialize import to_jsonable


def _empty() -> dict[str, Any]:
    return {
        "of": None,
        "logs": [],
        "childs": [],
        "files": [],
        "testFiles": [],
        "obj": None,
        "line": None,
        "reverso": 0,
        "isshqx": False,
        "isDisabled": False,
        "is_video": 0,
        "video_show": False,
        "testUser": None,
        "addUser": None,
        "saleManaUser": None,
        "saleUser": None,
        "usersadmin": None,
        "ypdhShow": False,
        "yplyShow": False,
        "kscsShow": False,
        "cswcShow": False,
        "ypghShow": False,
        "ypjhShow": False,
        "yplcShow": False,
        "ypfcShow": False,
        "order_type": 10,
        "isAskPay": False,
        "viewReciveBtn": False,
        "viewKpBtn": False,
        "collectionTimes": [],
        "openBills": [],
    }


def _get_order_raw(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT t.* FROM experiment_order t
        WHERE t.id = %(oid)s
          AND IFNULL(t.deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"oid": order_id},
    )


def _enrich_logs(order_id: int) -> list[dict[str, Any]]:
    logs = repo.load_logs(order_id)
    user_ids = {
        int(lg["log_user"]["id"])
        for lg in logs
        if isinstance(lg.get("log_user"), dict) and str(lg["log_user"].get("id") or "").isdigit()
    }
    names: dict[int, str] = {}
    if user_ids:
        rows = fetch_all(
            f"""
            SELECT id, true_name, user_name
            FROM sy_users
            WHERE id IN ({",".join(str(i) for i in user_ids)})
            """
        )
        for r in rows:
            names[int(r["id"])] = str(r.get("true_name") or r.get("user_name") or "")
    for lg in logs:
        lu = lg.get("log_user") or {}
        uid = lu.get("id")
        try:
            uid_i = int(uid) if uid is not None else None
        except (TypeError, ValueError):
            uid_i = None
        lg["log_user"] = {
            "id": uid,
            "trueName": names.get(uid_i, "") if uid_i is not None else "",
            "userName": names.get(uid_i, "") if uid_i is not None else "",
        }
    return logs


def _attach_parent(of: dict[str, Any]) -> None:
    parent_id = of.get("parent_id")
    if not parent_id:
        of["parentOf"] = None
        return
    try:
        pid = int(parent_id)
    except (TypeError, ValueError):
        of["parentOf"] = None
        return
    parent = _get_order_raw(pid)
    if not parent:
        of["parentOf"] = None
        return
    try:
        pst = int(parent.get("order_status") or 0)
    except (TypeError, ValueError):
        pst = 0
    of["parentOf"] = {
        "id": parent.get("id"),
        "order_id": parent.get("order_id"),
        "order_status": parent.get("order_status"),
        "order_statusstr": STATUS_STR.get(pst, "处理中"),
        "is_online": parent.get("is_online"),
        "reverso_context": parent.get("reverso_context"),
        "is_video": parent.get("is_video"),
    }
    try:
        of["_parent_reverso"] = int(parent.get("reverso_context") or 0)
    except (TypeError, ValueError):
        of["_parent_reverso"] = 0

    # 子单常缺人员/公司/类目，从父单补齐供 Vue 绑定
    for field in (
        "sale_manager",
        "sale_user",
        "addUser",
        "add_user_id",
        "test_user_id",
        "test_manager",
        "customer_name",
        "stock_company_name",
        "supplier_name",
        "class_id",
        "custom_user_id",
        "is_video",
        "pay_way",
    ):
        if of.get(field) in (None, "", 0, "0") and parent.get(field) not in (None, "", 0, "0"):
            of[field] = parent.get(field)


def order_detail_dpt(*, order_id: int) -> dict[str, Any]:
    """员工端子订单详情：按 id 查询，不按客户归属过滤；返回 Java Ajax obj 形状。"""
    empty = _empty()
    if order_id <= 0:
        return empty

    of = _get_order_raw(order_id)
    if not of:
        return empty

    oid = int(of["id"])
    try:
        status = int(of.get("order_status") or 0)
    except (TypeError, ValueError):
        status = 0
    of["order_statusstr"] = purchase_order_status_str(status)
    of["totalPrice"] = to_jsonable(of.get("totalPrice") or of.get("total_price") or 0)

    _attach_parent(of)
    enrich.enrich_pc_order_detail(of, order_id=oid)
    of["supplierUser"] = _load_supplier_user(of.get("supplier_name"))
    ensure_mp_of_fields(of)

    childs: list[dict[str, Any]] = []
    raw_childs = repo.load_purchase_line_children(oid)
    if raw_childs:
        childs = [child_enrich.enrich_experiment_child_row(dict(c)) for c in raw_childs]
        child_enrich.resolve_child_project_names(childs)

    config = get_config_row()
    image_base = image_web_server(config) or ""
    files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, file_type=3),
        image_base,
    )
    test_files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, file_type=4),
        image_base,
    )

    admin_row = admin_order_repo.get_order(oid) or {}
    flag_row = {
        "id": oid,
        "orderType": str(of.get("order_type") or admin_row.get("orderType") or "10"),
        "orderStatus": status,
        "parentId": of.get("parent_id"),
        "isVideo": of.get("is_video"),
    }
    sample_flow_repo.attach_sample_action_flags(flag_row)

    try:
        reverso = int(of.pop("_parent_reverso", 0) or of.get("reverso_context") or 0)
    except (TypeError, ValueError):
        reverso = 0
    try:
        is_video = int(of.get("is_video") or 0)
    except (TypeError, ValueError):
        is_video = 0
    if of.get("parentOf") and int(of["parentOf"].get("is_video") or 0) == 1:
        is_video = 1

    sale_manager = of.get("saleManagerUser")
    sale_user = of.get("saleUser")
    add_user = of.get("addUser") if isinstance(of.get("addUser"), dict) else None
    test_user = of.get("testUser")

    open_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 1)]
    receive_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 2)]
    collection_times = enrich.build_collection_times(of, receive_bills)

    return {
        **empty,
        "of": to_jsonable(of),
        "childs": [to_jsonable(c) for c in childs],
        "logs": _enrich_logs(oid),
        "files": files,
        "testFiles": test_files,
        "obj": None,
        "line": None,
        "reverso": reverso,
        "isshqx": bool(admin_row.get("canAudit")),
        "isDisabled": bool(admin_row.get("canEdit")),
        "is_video": is_video,
        "video_show": bool(flag_row.get("videoShow")),
        "testUser": to_jsonable(test_user) if test_user else None,
        "addUser": to_jsonable(add_user) if add_user else None,
        "saleManaUser": to_jsonable(sale_manager) if sale_manager else None,
        "saleUser": to_jsonable(sale_user) if sale_user else None,
        "usersadmin": None,
        "ypdhShow": bool(flag_row.get("ypdhShow")),
        "yplyShow": bool(flag_row.get("yplyShow")),
        "kscsShow": bool(flag_row.get("kscsShow")),
        "cswcShow": bool(flag_row.get("cswcShow")),
        "ypghShow": bool(flag_row.get("ypghShow")),
        "ypjhShow": bool(flag_row.get("ypjhShow")),
        "yplcShow": bool(flag_row.get("yplcShow")),
        "ypfcShow": bool(flag_row.get("ypfcShow")),
        "order_type": int(of.get("order_type") or 10),
        "isAskPay": bool(admin_row.get("canAskPay") or admin_row.get("canReAskPay")),
        "viewReciveBtn": bool(
            admin_row.get("canReceiveBill") or admin_row.get("canUploadPay")
        ),
        "viewKpBtn": bool(admin_row.get("canInvoice") or admin_row.get("canUploadInvoice")),
        "collectionTimes": collection_times,
        "openBills": [to_jsonable(b) for b in open_bills],
        "isFlag": True,
    }


def edit_page_xcx(*, order_id: int) -> dict[str, Any]:
    """编辑页头：复用详情 of。"""
    body = order_detail_dpt(order_id=order_id)
    return {"of": body.get("of"), "mainData": body.get("of")}


def sel_goods_list_dpt(
    *,
    of_id: str = "",
    order_status: str = "",
    is_meeting: str = "",
    start: str = "0",
    length: str = "10",
    draw: str = "1",
) -> dict[str, Any]:
    """预约云视频可选子行 — 顶层 DataTables。"""
    draw_n = int(draw) if str(draw).isdigit() else 1
    empty = {"data": [], "draw": draw_n, "recordsTotal": 0, "recordsFiltered": 0}
    if not str(of_id).isdigit():
        return empty
    oid = int(of_id)
    rows = admin_order_repo.list_order_children(oid)
    out: list[dict[str, Any]] = []
    for r in rows:
        try:
            st = int(r.get("orderStatus") or 0)
        except (TypeError, ValueError):
            st = 0
        if order_status and str(order_status).isdigit() and st != int(order_status):
            continue
        if is_meeting != "" and str(is_meeting).isdigit():
            try:
                meet = int(r.get("isMeeting") or 0)
            except (TypeError, ValueError):
                meet = 0
            if meet != int(is_meeting):
                continue
        item = dict(r)
        item["id"] = r.get("id")
        item["checked"] = False
        out.append(to_jsonable(item))
    offset = int(start) if str(start).isdigit() else 0
    limit = int(length) if str(length).isdigit() else 10
    if str(length) == "-1" or limit >= 999:
        page_rows = out
    else:
        page_rows = out[offset : offset + limit]
    return {
        "data": page_rows,
        "draw": draw_n,
        "recordsTotal": len(out),
        "recordsFiltered": len(out),
    }
