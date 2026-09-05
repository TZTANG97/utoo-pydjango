"""员工端实验订单详情 — 对齐小程序 staff/order_detail、orderdetaildptxcx。"""
from __future__ import annotations

from typing import Any

from apps.admin_experiment.repositories import orders as admin_order_repo
from apps.core.db_utils import fetch_one
from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import accessory_list as acc_repo
from apps.orders.repositories import orders as repo
from apps.orders.repositories import qd_bill as qd_bill_repo
from apps.orders.services import jdshow as jdshow_svc
from apps.orders.services import sale_detail_enrich as enrich
from qd_common.serialize import to_jsonable


def _empty() -> dict[str, Any]:
    return {
        "of": None,
        "logs": [],
        "collectionTimes": [],
        "openBills": [],
        "testFiles": [],
        "files": [],
        "hzdFiles": [],
        "jdshow": 0,
        "ispjqx": False,
        "bhyy": "",
        "yydUrl": "",
        "yspAndDhList": [],
        "viewReciveBtn": False,
        "viewKpBtn": False,
        "hzdpath": "",
        "bfb": 0,
        "scaleList": [],
        "salecbscaleList": [],
        "isfcbl": False,
        "isDisabled": False,
        "isyyd": False,
        "isOut": False,
        "isshqx": False,
        "evaluate": False,
    }


def _parse_scale_list(raw: str) -> list[dict[str, Any]]:
    text = (raw or "").strip()
    if not text:
        return []
    out: list[dict[str, Any]] = []
    for part in text.split(","):
        part = part.strip()
        if not part or "_" not in part:
            continue
        uid, val = part.split("_", 1)
        uid = uid.strip()
        val = val.strip().replace("%", "")
        if not uid or val == "":
            continue
        try:
            scale: Any = float(val)
            if scale == int(scale):
                scale = int(scale)
        except (TypeError, ValueError):
            scale = val
        name = admin_order_repo._user_display_name(uid)
        try:
            user_id = int(uid)
        except (TypeError, ValueError):
            user_id = uid
        out.append({"userId": user_id, "userName": name, "scale": scale})
    return out


def _load_supplier_user(supplier_id: Any) -> dict[str, Any]:
    if supplier_id is None or str(supplier_id).strip() == "":
        return {"id": None, "company_name": ""}
    try:
        sid = int(supplier_id)
    except (TypeError, ValueError):
        return {"id": None, "company_name": str(supplier_id)}
    row = fetch_one(
        """
        SELECT id, company_name
        FROM `user`
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": sid},
    )
    if not row:
        return {"id": sid, "company_name": ""}
    return {
        "id": row.get("id"),
        "company_name": row.get("company_name") or "",
    }


def _load_company(customer_id: Any) -> dict[str, Any]:
    if customer_id is None or str(customer_id).strip() == "":
        return {"id": None, "name": ""}
    cid_raw = str(customer_id).strip()
    row = None
    if cid_raw.isdigit():
        row = fetch_one(
            "SELECT id, name FROM qd_user_company WHERE id = %(id)s LIMIT 1",
            {"id": int(cid_raw)},
        )
    if not row:
        row = fetch_one(
            "SELECT id, name FROM qd_user_company WHERE id = %(id)s LIMIT 1",
            {"id": cid_raw},
        )
    if not row:
        return {"id": cid_raw, "name": ""}
    return {"id": row.get("id"), "name": row.get("name") or ""}


def _load_paytype(pay_way: Any) -> dict[str, Any]:
    if pay_way is None or str(pay_way).strip() == "":
        return {"name": ""}
    prow = fetch_one(
        "SELECT pay_type AS payType FROM qd_consume_paytype WHERE id = %(id)s LIMIT 1",
        {"id": pay_way},
    )
    if not prow:
        return {"name": ""}
    return {"name": str(prow.get("payType") or "")}


def _empty_sy_user() -> dict[str, Any]:
    return {"id": None, "userName": "", "trueName": "", "mobile": ""}


def ensure_mp_of_fields(of: dict[str, Any]) -> None:
    """小程序详情模板无防护访问所需的嵌套对象安全桩。"""
    company = of.get("company")
    if not isinstance(company, dict):
        company = _load_company(of.get("customer_name") or of.get("stock_company_name"))
        if not (company.get("name") or "").strip():
            cu = of.get("customUser") or {}
            if isinstance(cu, dict) and cu.get("company_name"):
                company = {"id": cu.get("id"), "name": cu.get("company_name") or ""}
        of["company"] = company
    else:
        company.setdefault("name", "")

    paytype = of.get("paytype")
    if not isinstance(paytype, dict):
        of["paytype"] = _load_paytype(of.get("pay_way"))
    else:
        if not paytype.get("name"):
            paytype["name"] = str(paytype.get("payType") or "")

    for key in ("saleManagerUser", "saleUser", "addUser", "testManagerUser", "testUser"):
        user = of.get(key)
        if not isinstance(user, dict):
            of[key] = _empty_sy_user()
        else:
            user.setdefault("userName", "")
            user.setdefault("trueName", user.get("userName") or "")
            user.setdefault("mobile", "")

    tc = of.get("testClass")
    if not isinstance(tc, dict):
        of["testClass"] = {"id": None, "name": "实验订单"}
    else:
        tc.setdefault("name", "")

    su = of.get("supplierUser")
    if not isinstance(su, dict):
        of["supplierUser"] = {"id": None, "company_name": ""}
    else:
        su.setdefault("company_name", "")

    try:
        of["totalPrice"] = float(of.get("totalPrice") or of.get("total_price") or 0)
    except (TypeError, ValueError):
        of["totalPrice"] = 0.0

    # 小程序 pay_status.find(e => e.key === pay_status) 用严格相等，需为 int
    try:
        if of.get("pay_status") not in (None, ""):
            of["pay_status"] = int(of.get("pay_status"))
    except (TypeError, ValueError):
        of["pay_status"] = 0

    if not of.get("delivery_time"):
        of["delivery_time"] = of.get("order_time") or of.get("addTime") or ""
    if not of.get("order_time"):
        of["order_time"] = of.get("addTime") or ""


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


def order_detail_dpt(*, order_id: int) -> dict[str, Any]:
    """员工端详情：按 id 查询，不按客户归属过滤。"""
    empty = _empty()
    if order_id <= 0:
        return empty

    of = _get_order_raw(order_id)
    if not of:
        return empty

    oid = int(of["id"])
    config = get_config_row()
    image_base = image_web_server(config) or ""

    open_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 1)]
    receive_bills = [enrich.enrich_bill_row(dict(b)) for b in repo.load_bills(oid, 2)]
    skje = sum(float(b.get("money") or 0) for b in receive_bills)
    has_online = qd_bill_repo.has_online_receive_bill(oid)

    enrich.enrich_sale_order(
        of,
        skje,
        kaip_bills=open_bills,
        receive_bills=receive_bills,
        has_online_receive=has_online,
    )
    of["order_statusstr"] = enrich.compute_sale_order_statusstr(of, oid)
    isfk = of.get("isfk", "0")
    jdshow = jdshow_svc.compute_jdshow(oid, str(isfk))
    ispjqx = bool(of.pop("ispjqx", False))

    yyd_url, hzdpath, ysp_and_dh = enrich.enrich_pc_order_detail(of, order_id=oid)
    of["supplierUser"] = _load_supplier_user(of.get("supplier_name"))
    ensure_mp_of_fields(of)

    files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(exp_of_id=oid, exclude_types=(5, 7)),
        image_base,
    )
    hzd_files = enrich.enrich_accessory_rows(
        acc_repo.load_accessories(child_of_id=oid, file_type=7),
        image_base,
    )
    test_files = enrich.enrich_accessory_rows(
        acc_repo.load_all_test_files(oid),
        image_base,
    )

    admin_row = admin_order_repo.get_order(oid) or {}
    # 避免 detail_flags 依赖 invoice_apply_log.order_id（库表列名不一致会 503）
    view_receive = bool(admin_row.get("canReceiveBill"))
    view_kp = bool(admin_row.get("canInvoice"))

    scale_list = _parse_scale_list(
        str(admin_row.get("userScaleInfo") or admin_row.get("scaleInfo") or "")
    )
    salecb_list = _parse_scale_list(str(admin_row.get("salecbUserScaleInfo") or ""))

    try:
        is_yyd = int(admin_row.get("isYyd") or of.get("is_yyd") or 0) == 1
    except (TypeError, ValueError):
        is_yyd = False
    try:
        is_evaluate = int(of.get("is_evaluate") or 0) == 1
    except (TypeError, ValueError):
        is_evaluate = False
    try:
        st = int(of.get("order_status") or 0)
    except (TypeError, ValueError):
        st = 0

    total = float(of.get("totalPrice") or 0)
    bfb = 0
    if total > 0:
        bfb = int(round(min(100.0, skje / total * 100.0)))

    return {
        **empty,
        "of": to_jsonable(of),
        "logs": repo.load_logs(oid),
        "collectionTimes": enrich.build_collection_times(of, receive_bills),
        "openBills": [to_jsonable(b) for b in open_bills],
        "testFiles": test_files,
        "files": files,
        "hzdFiles": hzd_files,
        "jdshow": jdshow,
        "ispjqx": ispjqx,
        "viewReciveBtn": view_receive,
        "viewKpBtn": view_kp,
        "yydUrl": yyd_url,
        "hzdpath": hzdpath,
        "yspAndDhList": ysp_and_dh,
        "bhyy": of.get("bhyy") or "",
        "bfb": bfb,
        "scaleList": scale_list,
        "salecbscaleList": salecb_list,
        "isfcbl": bool(admin_row.get("canShareRatio")),
        "isDisabled": bool(admin_row.get("canEdit")),
        "isyyd": is_yyd,
        "isOut": bool(admin_row.get("canCancel")) or st != 0,
        "isshqx": bool(admin_row.get("canAudit")),
        "evaluate": bool(admin_row.get("canConfirmCustomer")) or is_evaluate,
    }


def sub_edit_page(*, order_id: int) -> dict[str, Any]:
    """对齐 Java experimentSubOrder/editPage.ajax。"""
    detail = order_detail_dpt(order_id=order_id)
    of = detail.get("of")
    if not of:
        return {}
    children = [to_jsonable(r) for r in admin_order_repo.list_order_children(order_id)]
    try:
        st = int(of.get("order_status") or 0)
    except (TypeError, ValueError):
        st = 0
    # 已审核后编辑页直接用本单产品；否则给可选销售子行（精简：同本单行）
    sale_childs = children if st in (20, 30, 35, 45, 50) else children
    paytype = None
    pay_way = of.get("pay_way")
    if pay_way not in (None, ""):
        prow = fetch_one(
            "SELECT pay_type AS payType FROM qd_consume_paytype WHERE id = %(id)s LIMIT 1",
            {"id": pay_way},
        )
        if prow:
            paytype = prow.get("payType")
    receive_cnt = len(repo.load_bills(order_id, 2) or [])
    return {
        "of": of,
        "childs": children,
        "saleChilds": sale_childs,
        "files": detail.get("files") or [],
        "testFiles": detail.get("testFiles") or [],
        "collectionTimes": detail.get("collectionTimes") or [],
        "paytype": paytype,
        # Java editPage：有收款记录则部分字段禁用
        "isDisabled": receive_cnt > 0,
    }
