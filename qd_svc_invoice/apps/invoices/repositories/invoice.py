import logging
from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar
from qd_common.serialize import to_jsonable

logger = logging.getLogger(__name__)


def _enrich_apply_log_order_fields(row: dict[str, Any]) -> dict[str, Any]:
    order_ids_raw = str(row.get("order_ids") or "").strip()
    row["ofid"] = None
    row["eo_id"] = None
    row["order_id"] = ""
    if not order_ids_raw:
        return row
    first = order_ids_raw.split(",")[0].strip()
    if not first.isdigit():
        return row
    of_row = fetch_one(
        "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
        {"oid": int(first)},
    )
    if of_row:
        row["ofid"] = int(of_row["id"])
        row["eo_id"] = int(of_row["id"])
        row["order_id"] = of_row.get("order_id") or ""
    return row


def count_invoice_apply_logs(
    *,
    user_id: int,
    inv_type: int | None = None,
    order_id_kw: str = "",
) -> int:
    extra = ""
    params: dict[str, Any] = {"user_id": user_id}
    if inv_type is not None:
        extra += " AND t.type = %(tp)s"
        params["tp"] = inv_type
    if order_id_kw.strip():
        extra += """
            AND EXISTS (
                SELECT 1 FROM experiment_order eo
                WHERE FIND_IN_SET(eo.id, REPLACE(t.order_ids, ' ', '')) > 0
                  AND eo.order_id LIKE %(oid_kw)s
            )
        """
        params["oid_kw"] = f"%{order_id_kw.strip()}%"

    sql = f"""
        SELECT COUNT(1) FROM invoice_apply_log t
        WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s {extra}
    """
    try:
        return int(scalar(sql, params, 0) or 0)
    except Exception as exc:
        logger.warning("count invoice_apply_log failed: %s", exc)
        return 0


def list_invoice_apply_logs(
    *,
    user_id: int,
    offset: int,
    limit: int,
    inv_type: int | None = None,
    order_id_kw: str = "",
) -> list[dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {
        "user_id": user_id,
        "offset": offset,
        "limit": limit,
    }
    if inv_type is not None:
        extra += " AND t.type = %(tp)s"
        params["tp"] = inv_type
    if order_id_kw.strip():
        extra += """
            AND (
                EXISTS (
                    SELECT 1 FROM experiment_order eo
                    WHERE FIND_IN_SET(eo.id, REPLACE(t.order_ids, ' ', '')) > 0
                      AND eo.order_id LIKE %(oid_kw)s
                )
                OR t.invoice_num LIKE %(oid_kw)s
            )
        """
        params["oid_kw"] = f"%{order_id_kw.strip()}%"

    sql = f"""
        SELECT t.*, u.userName AS userName
        FROM invoice_apply_log t
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s {extra}
        ORDER BY t.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    try:
        rows = fetch_all(sql, params)
        out = []
        for d in rows:
            d["invoice_money"] = to_jsonable(d.get("invoice_money") or 0)
            d = _enrich_apply_log_order_fields(d)
            out.append(to_jsonable(d))
        return out
    except Exception as exc:
        logger.warning("list invoice_apply_log failed: %s", exc)
        return []
