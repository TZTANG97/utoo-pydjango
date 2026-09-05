"""充值流水 — selRecharge* / selDefaultAccount"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from qd_common.serialize import to_jsonable

from apps.auth_pc.services.customer import CustomerUserService
from apps.core.db_utils import fetch_all, fetch_one, scalar
from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.payments.repositories import pay_info as pay_repo
from apps.payments.services.payment_apply_ops import get_default_account, has_pending_recharge_application

logger = logging.getLogger(__name__)

_LIST_INNER_SQL = """
SELECT
    t.id, t.addTime, t.addTime AS payTime, t.money, t.pay_way, t.orderType,
    t.accessoryId, t.applyStatus, t.mark, '0' AS ptype, t.pa_num, '0' AS type,
    t.orderId, NULL AS order_id_ref
FROM payment_application t
WHERE t.deleteStatus = 0 AND t.orderType != 4
  AND t.userId = %(user_id)s
  {pa_type_clause}
  {pa_time_clause}
UNION ALL
SELECT
    p.id,
    COALESCE(p.payTime, p.addTime) AS addTime,
    p.payTime, p.money, p.pay_way, p.pay_type AS orderType,
    '' AS accessoryId, CAST(p.status AS CHAR) AS applyStatus, '' AS mark,
    '1' AS ptype, p.pa_num, '1' AS type,
    p.order_id AS orderId, p.order_id AS order_id_ref
FROM pay_info_log p
WHERE p.pay_type != 4 AND p.user_id = %(user_id)s
  AND (p.deleteStatus = 0 OR p.status IN (1, 3))
  {pil_type_clause}
  {pil_time_clause}
UNION ALL
SELECT
    l.id,
    l.addTime,
    l.addTime AS payTime,
    ABS(l.money) AS money,
    COALESCE(p.pay_way, 2) AS pay_way,
    CASE WHEN l.money >= 0 THEN '1' ELSE '3' END AS orderType,
    '' AS accessoryId,
    '2' AS applyStatus,
    CASE
        WHEN l.money >= 0 THEN CONCAT('账户入账', COALESCE(CONCAT('·', p.pa_num), ''))
        ELSE '账户出账'
    END AS mark,
    '2' AS ptype,
    COALESCE(p.pa_num, CAST(l.of_id AS CHAR)) AS pa_num,
    '3' AS type,
    CAST(l.of_id AS CHAR) AS orderId,
    CAST(l.of_id AS CHAR) AS order_id_ref
FROM user_account_log l
LEFT JOIN pay_info_log p ON p.id = l.of_id AND p.user_id = l.user_id
WHERE l.deleteStatus = 0 AND l.user_id = %(user_id)s
  {ual_type_clause}
  {ual_time_clause}
UNION ALL
SELECT
    c.id,
    COALESCE(c.payTime, c.addTime) AS addTime,
    c.payTime,
    c.money,
    c.pay_way,
    c.pay_type AS orderType,
    '' AS accessoryId,
    CAST(c.status AS CHAR) AS applyStatus,
    '' AS mark,
    '1' AS ptype,
    c.pa_num,
    '4' AS type,
    c.order_id AS orderId,
    c.order_id AS order_id_ref
FROM company_pay_log c
LEFT JOIN qd_user_company qc ON c.company_id = qc.id
WHERE c.deleteStatus = 0 AND c.pay_type != 4
  AND qc.contract_phone = %(mobile)s
  {cpl_type_clause}
  {cpl_time_clause}
"""


def _normalize_type_filter(type_raw: str) -> str:
    t = (type_raw or "").strip()
    if t == "3":
        return "4"
    if t == "0":
        return ""
    return t


def _type_clause_payment(type_f: str, params: dict[str, Any]) -> str:
    if not type_f:
        return ""
    if type_f == "2":
        return " AND t.orderType IN (2, 3)"
    params["_ot"] = type_f
    return " AND t.orderType = %(_ot)s"


def _type_clause_pay_log(type_f: str, params: dict[str, Any]) -> str:
    if not type_f:
        return ""
    if type_f == "2":
        return " AND p.pay_type IN (2, 3)"
    params["_pt"] = type_f
    return " AND p.pay_type = %(_pt)s"


def _type_clause_account_log(type_f: str) -> str:
    if not type_f:
        return ""
    if type_f == "1":
        return " AND l.money > 0"
    if type_f == "2":
        return " AND l.money < 0"
    if type_f in ("3", "4"):
        return " AND 1=0"
    return ""


def _type_clause_company_pay(type_f: str, params: dict[str, Any]) -> str:
    if not type_f:
        return ""
    if type_f == "2":
        return " AND c.pay_type IN (2, 3)"
    params["_cpt"] = type_f
    return " AND c.pay_type = %(_cpt)s"


def _time_clause(alias: str, start_time: str, end_time: str) -> str:
    parts = []
    if start_time:
        parts.append(f" AND {alias}.addTime >= %(start_time)s")
    if end_time and start_time:
        parts.append(f" AND {alias}.addTime <= %(end_time)s")
    return "".join(parts)


def _status_label(ptype: str, apply_status: str, order_type: str, mark: str = "") -> str:
    if ptype == "2":
        return mark or ("账户入账" if order_type == "1" else "账户出账")
    if ptype == "0":
        if apply_status == "1":
            return "待审核"
        if apply_status == "2":
            return "已审核"
        if apply_status == "3":
            return "已拒绝"
        return apply_status
    if ptype == "1":
        if apply_status == "1":
            return "待支付"
        if apply_status == "2":
            if order_type == "1":
                return "充值成功"
            if order_type in ("2", "3"):
                return "支付成功"
            if order_type == "4":
                return "提现成功"
        if apply_status == "3":
            return "已关闭"
    return apply_status


def _accessory_path(accessory_id: Any, image_base: str) -> str:
    if not accessory_id:
        return ""
    row = fetch_one(
        "SELECT path, name FROM accessory WHERE id = %(aid)s AND deleteStatus = 0 LIMIT 1",
        {"aid": int(accessory_id)},
    )
    if not row or not row.get("path") or not row.get("name"):
        return ""
    base = image_base.rstrip("/")
    return f"{base}/{str(row['path']).strip('/')}/{str(row['name']).strip('/')}"


def _accessory_by_order(order_id: Any, image_base: str) -> str:
    if not order_id:
        return ""
    row = fetch_one(
        """
        SELECT path, name FROM accessory
        WHERE deleteStatus = 0 AND exp_of_id = %(oid)s AND type = 7
        ORDER BY id ASC LIMIT 1
        """,
        {"oid": int(order_id)},
    )
    if not row:
        return ""
    base = image_base.rstrip("/")
    return f"{base}/{str(row['path']).strip('/')}/{str(row['name']).strip('/')}"


def _decorate_row(row: dict[str, Any], image_base: str) -> dict[str, Any]:
    d = to_jsonable(row)
    ptype = str(d.get("ptype") or "")
    order_type = str(d.get("orderType") or "")
    pay_way = d.get("pay_way")
    hzd_path = ""

    if ptype == "0":
        if order_type == "1" and int(pay_way or 0) == 3:
            hzd_path = _accessory_path(d.get("accessoryId"), image_base)
        elif order_type in ("2", "3") and d.get("orderId"):
            hzd_path = _accessory_by_order(d.get("orderId"), image_base)
    elif ptype == "2":
        oid = d.get("orderId") or d.get("order_id_ref")
        if oid:
            try:
                prow = fetch_one(
                    "SELECT pa_num, pay_way FROM pay_info_log WHERE id = %(id)s LIMIT 1",
                    {"id": int(oid)},
                )
                if prow and prow.get("pa_num"):
                    d["pa_num"] = prow["pa_num"]
            except (TypeError, ValueError):
                pass

    order_num = ""
    oid = d.get("orderId") or d.get("order_id_ref")
    if oid:
        try:
            orow = fetch_one(
                "SELECT order_id FROM experiment_order WHERE id = %(id)s LIMIT 1",
                {"id": int(oid)},
            )
            if orow:
                order_num = orow.get("order_id") or ""
        except (TypeError, ValueError):
            pass

    raw_ptype = ptype
    raw_status = str(d.get("applyStatus") or "")
    mark = str(d.get("mark") or "")
    d["payStatusRaw"] = raw_status
    d["hzdPath"] = hzd_path
    d["orderNum"] = order_num
    if raw_ptype == "0":
        d["ptype"] = "申请"
    elif raw_ptype == "2":
        d["ptype"] = "账户"
    else:
        d["ptype"] = "流水"
    d["applyStatus"] = _status_label(raw_ptype, raw_status, order_type, mark)

    if raw_ptype == "1" and raw_status == "1":
        add_time = d.get("addTime") or d.get("payTime")
        rem = pay_repo.pay_log_remaining_seconds(add_time)
        close_dt = pay_repo.pay_log_close_at(add_time)
        d["remainingSeconds"] = rem
        d["closeAt"] = close_dt.strftime("%Y-%m-%d %H:%M:%S") if close_dt else ""
        d["payLogId"] = d.get("id")
        d["canContinuePay"] = rem > 0 and int(pay_way or 0) == 2
        try:
            out_no = pay_repo.get_out_trade_no_for_pay_log(int(d["id"]))
            if out_no:
                d["outTradeNo"] = out_no
        except (TypeError, ValueError):
            pass
        if rem > 0:
            d["applyStatus"] = "待支付"
    return d


def list_recharge_page(
    *,
    user_id: int,
    mobile: str,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    start_time: str = "",
    end_time: str = "",
    type_raw: str = "0",
) -> dict[str, Any]:
    try:
        offset = int(start)
        limit = int(length) or 10
    except ValueError:
        offset, limit = 0, 10

    type_f = _normalize_type_filter(type_raw)
    params: dict[str, Any] = {
        "user_id": user_id,
        "mobile": mobile or "",
        "start_time": start_time or "",
        "end_time": end_time or "",
        "limit": limit,
        "offset": offset,
    }
    inner = _LIST_INNER_SQL.format(
        pa_type_clause=_type_clause_payment(type_f, params),
        pa_time_clause=_time_clause("t", start_time, end_time),
        pil_type_clause=_type_clause_pay_log(type_f, params),
        pil_time_clause=_time_clause("p", start_time, end_time),
        ual_type_clause=_type_clause_account_log(type_f),
        ual_time_clause=_time_clause("l", start_time, end_time),
        cpl_type_clause=_type_clause_company_pay(type_f, params),
        cpl_time_clause=_time_clause("c", start_time, end_time),
    )

    count_sql = f"SELECT COUNT(1) FROM ({inner}) tab"
    try:
        total = int(scalar(count_sql, params, 0) or 0)
    except Exception as exc:
        logger.warning("list_recharge_page count failed: %s", exc)
        total = 0

    list_sql = f"""
        SELECT * FROM ({inner}) tab
        ORDER BY tab.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    rows = fetch_all(list_sql, params)
    config = get_config_row()
    image_base = image_web_server(config)
    data = [_decorate_row(r, image_base) for r in rows]
    try:
        draw_i = int(draw)
    except ValueError:
        draw_i = 1
    return {
        "data": data,
        "draw": draw_i,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def sel_recharge_status(user_id: int) -> bool:
    return has_pending_recharge_application(user_id)


def sel_default_account() -> dict[str, Any]:
    return get_default_account()


def sel_recharge_list_for_user(
    user_id: int,
    *,
    start: str,
    length: str,
    draw: str,
    start_time: str,
    end_time: str,
    type_raw: str,
) -> dict[str, Any]:
    user = CustomerUserService.get_by_id(user_id)
    mobile = (user.mobile or "") if user else ""
    return list_recharge_page(
        user_id=user_id,
        mobile=mobile,
        start=start,
        length=length,
        draw=draw,
        start_time=start_time,
        end_time=end_time,
        type_raw=type_raw,
    )
