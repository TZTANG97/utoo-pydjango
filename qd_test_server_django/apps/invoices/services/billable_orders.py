import logging
from typing import Any

from apps.core.db_utils import fetch_all, scalar
from qd_common.serialize import to_jsonable

logger = logging.getLogger(__name__)

_KP_LIST_SQL = """
SELECT * FROM (
    SELECT t.id, t.id AS of_id, t.addTime, t.order_id,
           t.totalPrice - IFNULL(qdtab.kpje, 0) AS money, '' AS bill_date
    FROM experiment_order t
    LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
    LEFT JOIN (
        SELECT qb.exp_of_id, COUNT(qb.id) AS num, SUM(qb.money) AS kpje
        FROM qd_bill qb WHERE qb.type = 1 GROUP BY qb.exp_of_id
    ) qdtab ON t.id = qdtab.exp_of_id
    WHERE t.order_status IN (30, 40, 50)
      AND t.order_type IN ('6', '8')
      AND t.invoiceType = 1 AND t.is_online = 0 AND t.is_apply = 0
      AND IFNULL(qdtab.kpje, 0) < t.totalPrice
      AND IFNULL(qdtab.num, 0) < (
          LENGTH(IFNULL(t.collection_time, ''))
          - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', '')) + 1
      )
      AND (t.custom_user_id = %(user_id)s OR quc.contract_phone = %(mobile)s)
    UNION ALL
    SELECT t.id, t.id AS of_id, t.addTime, t.order_id,
           IFNULL(qdtab.kpje, 0) AS money, qdtab.bill_date
    FROM experiment_order t
    LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
    LEFT JOIN (
        SELECT qb.exp_of_id, SUM(qb.money) AS kpje, MAX(qb.bill_date) AS bill_date
        FROM qd_bill qb
        WHERE qb.type = 2 AND qb.is_apply = 0
        GROUP BY qb.exp_of_id
    ) qdtab ON t.id = qdtab.exp_of_id
    WHERE t.invoiceType = 1 AND t.order_type IN ('6', '8')
      AND t.is_online = 1 AND IFNULL(qdtab.kpje, 0) > 0
      AND (t.custom_user_id = %(user_id)s OR quc.contract_phone = %(mobile)s)
) tab
WHERE 1=1
"""


def _filter_params(
    *,
    user_id: int,
    mobile: str,
    order_id_kw: str,
    start_time: str,
    end_time: str,
) -> tuple[str, dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {
        "user_id": user_id,
        "user_id_str": str(user_id),
        "mobile": mobile,
    }
    if order_id_kw.strip():
        extra += " AND tab.order_id LIKE %(oid_kw)s"
        params["oid_kw"] = f"%{order_id_kw.strip()}%"
    if start_time.strip():
        extra += " AND tab.addTime >= %(st)s"
        params["st"] = start_time.strip()
    if end_time.strip():
        extra += " AND tab.addTime <= %(et)s"
        params["et"] = end_time.strip()
    return extra, params


def count_billable_orders(
    *,
    user_id: int,
    mobile: str,
    order_id_kw: str = "",
    start_time: str = "",
    end_time: str = "",
) -> int:
    extra, params = _filter_params(
        user_id=user_id,
        mobile=mobile,
        order_id_kw=order_id_kw,
        start_time=start_time,
        end_time=end_time,
    )
    sql = f"SELECT COUNT(1) FROM ({_KP_LIST_SQL} {extra}) c"
    try:
        return int(scalar(sql, params, 0) or 0)
    except Exception as exc:
        logger.warning("count billable orders failed: %s", exc)
        return 0


def list_billable_orders(
    *,
    user_id: int,
    mobile: str,
    offset: int,
    limit: int,
    order_id_kw: str = "",
    start_time: str = "",
    end_time: str = "",
) -> list[dict[str, Any]]:
    extra, params = _filter_params(
        user_id=user_id,
        mobile=mobile,
        order_id_kw=order_id_kw,
        start_time=start_time,
        end_time=end_time,
    )
    params["offset"] = offset
    params["limit"] = limit
    sql = f"""
        SELECT * FROM ({_KP_LIST_SQL} {extra}) tab
        ORDER BY tab.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    try:
        rows = fetch_all(sql, params)
        out = []
        for d in rows:
            d["money"] = to_jsonable(d.get("money") or 0)
            d["totalPrice"] = d["money"]
            out.append(d)
        return out
    except Exception as exc:
        logger.warning("list billable orders failed: %s", exc)
        return []
