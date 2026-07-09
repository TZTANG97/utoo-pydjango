import logging
from typing import Any

from apps.auth_pc.services.customer import CustomerUserService
from apps.core.db_utils import fetch_all, scalar
from apps.core.services.sysconfig import get_config_row, image_web_server
from qd_common.serialize import to_jsonable

logger = logging.getLogger(__name__)

_UNION_SQL = """
    SELECT t.id, t.addTime, t.deleteStatus, t.money, qb.bill_date AS invoice_date,
           t.of_id, t.user_id, a.name, a.path, a.info, t.type,
           eo.order_id AS orderId, eo.id AS eid, eo.order_type
    FROM user_invoice_log t
    LEFT JOIN accessory a ON t.accessory_id = a.id
    LEFT JOIN qd_bill qb ON t.qd_bill_id = qb.id
    LEFT JOIN experiment_order eo ON t.of_id = eo.id
    WHERE t.deleteStatus = 0 AND t.type = 0 AND t.user_id = %(user_id)s
    UNION ALL
    SELECT t.id, t.addTime, t.deleteStatus, t.money, qb.bill_date AS invoice_date,
           t.of_id, t.company_id AS user_id, a.name, a.path, a.info, '0' AS type,
           eo.order_id AS orderId, eo.id AS eid, eo.order_type
    FROM company_invoice_log t
    LEFT JOIN accessory a ON t.accessory_id = a.id
    LEFT JOIN qd_bill qb ON t.qd_bill_id = qb.id
    LEFT JOIN qd_user_company quc ON t.company_id = quc.id
    LEFT JOIN experiment_order eo ON t.of_id = eo.id
    WHERE t.deleteStatus = 0 AND quc.contract_phone = %(mobile)s
    UNION ALL
    SELECT t.id, t.addTime, t.deleteStatus, t.money, qb.bill_date AS invoice_date,
           t.of_id, t.user_id, a.name, a.path, a.info, t.type,
           off.recharge_num AS orderId, off.id AS eid, '' AS order_type
    FROM user_invoice_log t
    LEFT JOIN accessory a ON t.accessory_id = a.id
    LEFT JOIN qd_bill qb ON t.qd_bill_id = qb.id
    LEFT JOIN exp_offline_recharge off ON t.of_id = off.id
    WHERE t.deleteStatus = 0 AND t.type = 1 AND t.user_id = %(user_id)s
"""


def get_invoice_log_list_page(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    order_id_kw: str = "",
) -> dict[str, Any]:
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    draw_n = int(draw) if draw.isdigit() else 1

    user = CustomerUserService.get_by_id(user_id)
    mobile = (user.mobile or "") if user else ""
    order_filter = ""
    params: dict[str, Any] = {
        "user_id": user_id,
        "mobile": mobile,
        "offset": offset,
        "limit": limit,
    }
    if order_id_kw and order_id_kw.strip() not in ("", "null"):
        order_filter = " AND tab.orderId LIKE %(oid_kw)s"
        params["oid_kw"] = f"%{order_id_kw.strip()}%"

    try:
        total = int(
            scalar(
                f"SELECT COUNT(1) FROM ({_UNION_SQL}) tab WHERE 1=1 {order_filter}",
                params,
                0,
            )
            or 0
        )
        rows = fetch_all(
            f"""
            SELECT * FROM ({_UNION_SQL}) tab
            WHERE 1=1 {order_filter}
            ORDER BY tab.invoice_date DESC, tab.addTime DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        cfg = get_config_row()
        image_base = image_web_server(cfg).rstrip("/")
        data = []
        for d in rows:
            d = dict(d)
            if d.get("path") and d.get("name"):
                d["path"] = f"{image_base}/{str(d['path']).strip('/')}"
            d.setdefault("status", 0)
            data.append(to_jsonable(d))
        return {
            "data": data,
            "draw": draw_n,
            "recordsTotal": total,
            "recordsFiltered": total,
        }
    except Exception as exc:
        logger.warning("get_invoice_log_list_page failed: %s", exc)
        return {
            "data": [],
            "draw": draw_n,
            "recordsTotal": 0,
            "recordsFiltered": 0,
        }
