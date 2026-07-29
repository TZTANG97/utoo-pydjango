"""主订单详情字段补齐 — 对齐 FastAPI sale_detail / Java orderDetailAjax"""
from __future__ import annotations

import logging
from typing import Any

from apps.auth_pc.services.customer import CustomerUserService
from apps.core.db_utils import fetch_all, fetch_one, scalar
from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.constants import STATUS_STR
from apps.orders.repositories import accessory_list as acc_repo
from apps.orders.repositories import orders as repo
from qd_common.serialize import to_jsonable

logger = logging.getLogger(__name__)


def accessory_url(base: str, acc: dict[str, Any]) -> str:
    path = (acc.get("path") or "").strip().strip("/")
    name = (acc.get("name") or "").strip()
    if not path and not name:
        return ""
    if path.startswith("http"):
        return f"{path}/{name}" if name else path
    root = (base or "").rstrip("/")
    if not root:
        return f"{path}/{name}" if path else name
    return f"{root}/{path}/{name}".replace("//", "/").replace(":/", "://")


def enrich_bill_row(b: dict[str, Any]) -> dict[str, Any]:
    bd = b.get("bill_date") or b.get("billDate") or b.get("add_time")
    b["billDate"] = to_jsonable(bd)
    b["bill_date"] = b["billDate"]
    return b


def enrich_accessory_rows(
    accs: list[dict[str, Any]], image_base: str
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for acc in accs:
        a = dict(acc)
        path = (a.get("path") or "").strip()
        if path and not path.startswith("http"):
            base = (image_base or "").rstrip("/")
            if base:
                a["path"] = f"{base}/{path.lstrip('/')}"
        out.append(a)
    return out


def enrich_sale_order(
    of: dict[str, Any],
    skje: float,
    *,
    kaip_bills: list[dict[str, Any]] | None = None,
    receive_bills: list[dict[str, Any]] | None = None,
    has_online_receive: bool = False,
) -> None:
    status = int(of.get("order_status") or 0)
    of["totalPrice"] = to_jsonable(of.get("totalPrice") or of.get("total_price") or 0)
    total = float(of.get("totalPrice") or 0)
    of["xsskje"] = skje
    inv = int(of.get("invoiceType") or of.get("invoice_type") or 0)
    of["invoiceType"] = inv
    ct = (of.get("collection_time") or "").strip()
    parts = [p for p in ct.split(",") if p.strip()] if ct else []
    kaip = kaip_bills or []
    recv = receive_bills or []
    kaip_sum = sum(float(b.get("money") or 0) for b in kaip)
    if inv == 1:
        if kaip_sum >= total and total > 0:
            of["iskp"] = "1"
        elif parts and len(kaip) >= len(parts):
            of["iskp"] = "1"
        else:
            of["iskp"] = "0"
    else:
        of["iskp"] = "2"
    if has_online_receive:
        of["isfk"] = "1"
    elif parts and len(recv) >= len(parts):
        of["isfk"] = "1"
    else:
        of["isfk"] = "0"
    of["kpShow"] = "0"
    of["dkpje"] = max(0.0, total - kaip_sum) if inv == 1 else 0.0
    of["company_account"] = of.get("company_account") or ""
    of["isUploadReceipt"] = int(of.get("isUploadReceipt") or 0)
    of["ispjqx"] = status == 50 and int(of.get("is_evaluate") or 0) == 0


def compute_sale_order_statusstr(of: dict[str, Any], order_id: int) -> str:
    status = int(of.get("order_status") or 0)
    if status == 50:
        return "已完成"
    if status == 55:
        return "已评价"

    is_online = int(of.get("is_online") or 0)
    child_rows = fetch_all(
        """
        SELECT order_status FROM experiment_order_child
        WHERE order_form_id = %(oid)s
          AND delete_status = 2 AND order_status > 0
        """,
        {"oid": order_id},
    )
    child_statuses = [int(r["order_status"]) for r in child_rows]

    po_rows = fetch_all(
        """
        SELECT order_status FROM experiment_order
        WHERE parent_id = %(pid)s AND order_status > 0
        """,
        {"pid": order_id},
    )
    po_statuses = [int(r["order_status"]) for r in po_rows]

    order_statusstr = ""
    if is_online == 0 and child_statuses and all(s >= 50 for s in child_statuses):
        order_statusstr = "实验完成"
    if po_statuses and any(37 <= s <= 42 for s in po_statuses):
        order_statusstr = "实验中"
    elif po_statuses and any(35 <= s < 38 for s in po_statuses):
        order_statusstr = "待实验"
    if is_online == 0 and child_statuses and any(s < 36 for s in child_statuses):
        order_statusstr = "待邮寄"
    if is_online == 1 and child_statuses and any(s < 36 for s in child_statuses):
        order_statusstr = "待邮寄"

    ct = (of.get("collection_time") or "").strip()
    if ct:
        parts = [p for p in ct.split(",") if p.strip()]
        try:
            cnt = int(
                scalar(
                    """
                    SELECT COUNT(1) FROM qd_bill
                    WHERE exp_of_id = %(oid)s AND type = 2
                    """,
                    {"oid": order_id},
                    0,
                )
                or 0
            )
        except Exception:
            cnt = 0
        if parts and cnt < len(parts):
            order_statusstr = "待支付"

    if not order_statusstr and status == 30:
        return "已审核"
    return order_statusstr or STATUS_STR.get(status, "处理中")


def load_paytype_scales(pay_way: Any) -> list[str]:
    if pay_way is None or str(pay_way).strip() == "":
        return []
    try:
        pid = int(pay_way)
    except (TypeError, ValueError):
        return []
    try:
        row = fetch_one(
            "SELECT scale_val FROM qd_consume_paytype WHERE id = %(id)s LIMIT 1",
            {"id": pid},
        )
    except Exception:
        return []
    if not row or not row.get("scale_val"):
        return []
    return [p.strip() for p in str(row["scale_val"]).split(",") if p.strip()]


def build_collection_times(
    of: dict[str, Any], receive_bills: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    ct = (of.get("collection_time") or "").strip()
    if not ct:
        return []
    parts = [p.strip() for p in ct.split(",") if p.strip()]
    total = float(of.get("totalPrice") or of.get("total_price") or 0)
    scales = load_paytype_scales(of.get("pay_way"))
    n = len(parts) or 1
    online_bills: list[dict[str, Any]] = []
    try:
        rows = fetch_all(
            """
            SELECT * FROM exp_online_qd_bill
            WHERE exp_of_id = %(oid)s AND type = 2
            ORDER BY id ASC
            """,
            {"oid": int(of["id"])},
        )
        online_bills = [enrich_bill_row(dict(r)) for r in rows]
    except Exception:
        online_bills = []

    result: list[dict[str, Any]] = []
    for i, t in enumerate(parts):
        if i < len(scales):
            try:
                per = round(total * float(scales[i]) / 100.0, 2)
            except (TypeError, ValueError):
                per = round(total / n, 2) if total else 0.0
        else:
            per = round(total / n, 2) if total else 0.0
        item: dict[str, Any] = {"time": t, "price": per}
        if i < len(receive_bills):
            item["bill"] = receive_bills[i]
        if i < len(online_bills):
            item["onlinebill"] = online_bills[i]
        result.append(item)
    return result


def build_ysp_and_dh_list(*, of: dict[str, Any], order_id: int) -> list[dict[str, str]]:
    is_video = int(of.get("is_video") or 0) == 1
    reverso = int(of.get("reverso_context") or 0) == 1
    if not is_video and not reverso:
        return []
    try:
        rows = fetch_all(
            """
            SELECT id, is_meeting, express_no
            FROM experiment_order_child
            WHERE order_form_id = %(oid)s AND delete_status = 2 AND order_status > 0
            ORDER BY id ASC
            """,
            {"oid": order_id},
        )
    except Exception as exc:
        logger.warning("yspAndDhList children failed: %s", exc)
        return []
    out: list[dict[str, str]] = []
    for row in rows:
        hyh = ""
        jhdh = ""
        cid = int(row["id"])
        if is_video:
            if int(row.get("is_meeting") or 0) == 1:
                try:
                    vrow = fetch_one(
                        """
                        SELECT meeting_num FROM experiment_video
                        WHERE child_id = %(cid)s LIMIT 1
                        """,
                        {"cid": cid},
                    )
                    hyh = (vrow.get("meeting_num") if vrow else "") or ""
                except Exception:
                    hyh = ""
            if not hyh:
                hyh = "待预约"
        if reverso:
            express_no = (row.get("express_no") or row.get("expressNo") or "").strip()
            jhdh = express_no or "待寄回"
        item: dict[str, str] = {}
        if is_video:
            item["hyh"] = hyh
        if reverso:
            item["jhdh"] = jhdh
        out.append(item)
    return out


def load_company_account_default() -> str:
    for sql in (
        """
        SELECT company_name, bankCardNum, bank
        FROM company_account_info
        WHERE is_default = 1 AND deleteStatus = 0
        LIMIT 1
        """,
        """
        SELECT company_name, bankCardNum, bank
        FROM company_account_info
        WHERE defaultaccount = 1 AND deleteStatus = 0
        LIMIT 1
        """,
    ):
        try:
            row = fetch_one(sql)
            if row:
                return (
                    f"{row.get('company_name') or ''} "
                    f"{row.get('bankCardNum') or ''} "
                    f"{row.get('bank') or ''}"
                ).strip()
        except Exception:
            continue
    return ""


def load_sy_user_brief(user_id: Any) -> dict[str, Any] | None:
    if user_id is None or str(user_id).strip() == "":
        return None
    uid = str(user_id).strip()
    try:
        row = fetch_one(
            """
            SELECT id, user_name, true_name, mobile_phone_number
            FROM sy_users
            WHERE id = %(uid)s
            LIMIT 1
            """,
            {"uid": uid},
        )
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": row.get("id"),
        "userName": row.get("user_name") or "",
        "trueName": row.get("true_name") or row.get("user_name") or "",
        "mobile": row.get("mobile_phone_number") or "",
    }


def load_custom_user(custom_user_id: Any) -> dict[str, Any] | None:
    if custom_user_id is None or str(custom_user_id).strip() == "":
        return None
    try:
        uid = int(custom_user_id)
    except (TypeError, ValueError):
        return None
    user = CustomerUserService.get_by_id(uid)
    if not user:
        return None
    return {
        "id": user.id,
        "userName": user.userName or "",
        "trueName": user.trueName or user.userName or "",
        "mobile": user.mobile or "",
        "company_name": user.company_name or "",
    }


def enrich_pc_order_detail(of: dict[str, Any], *, order_id: int) -> tuple[str, str, list[dict[str, str]]]:
    """补齐 C 端详情页 of 字段；返回 (yydUrl, hzdpath, yspAndDhList)"""
    config = get_config_row()
    image_base = image_web_server(config) or ""

    cid = of.get("class_id")
    if cid:
        em = repo.get_experiment_manage(int(cid))
        of["testClass"] = {
            "id": int(cid),
            "name": (em.get("name") if em else "") or "实验订单",
        }
    else:
        of["testClass"] = {"id": None, "name": "实验订单"}

    if not of.get("order_time"):
        of["order_time"] = of.get("addTime")

    inv = int(of.get("invoiceType") or of.get("invoice_type") or 0)
    of["invoiceType"] = inv

    yyd_accs = acc_repo.load_accessories(child_of_id=order_id, file_type=6)
    yyd_url = accessory_url(image_base, yyd_accs[0]) if yyd_accs else ""

    hzd_accs = acc_repo.load_accessories(child_of_id=order_id, file_type=7)
    hzdpath = accessory_url(image_base, hzd_accs[0]) if hzd_accs else ""

    kp_show = "0"
    dkpje = float(of.get("dkpje") or 0)
    if inv == 1 and int(of.get("is_online") or 0) == 0:
        if int(of.get("order_status") or 0) in (30, 50) and int(of.get("is_apply") or 0) == 0:
            if dkpje > 0:
                kp_show = "1"
    elif inv == 1 and int(of.get("is_online") or 0) == 1:
        if dkpje > 0:
            kp_show = "1"
    of["kpShow"] = kp_show

    child_rows = fetch_all(
        """
        SELECT order_status FROM experiment_order_child
        WHERE order_form_id = %(oid)s
          AND delete_status = 2 AND order_status > 0
        """,
        {"oid": order_id},
    )
    child_statuses = [int(r["order_status"]) for r in child_rows]
    print_yyd = 0
    if int(of.get("order_status") or 0) >= 30 and int(of.get("is_yyd") or 0) == 1:
        if any(s < 36 for s in child_statuses):
            print_yyd = 1
    of["printYydShow"] = print_yyd

    cu = load_custom_user(of.get("custom_user_id"))
    if cu:
        of["customUser"] = cu
    for field, key in (
        ("sale_manager", "saleManagerUser"),
        ("sale_user", "saleUser"),
        ("test_user_id", "testUser"),
        ("test_manager", "testManagerUser"),
    ):
        brief = load_sy_user_brief(of.get(field))
        if brief:
            of[key] = brief
    if of.get("addUser") or of.get("add_user_id"):
        add_id = of.get("addUser") or of.get("add_user_id")
        brief = load_sy_user_brief(add_id)
        if brief:
            of["addUser"] = brief
    if not of.get("company_account"):
        of["company_account"] = load_company_account_default()

    ysp_list = build_ysp_and_dh_list(of=of, order_id=order_id)
    return yyd_url, hzdpath, ysp_list
