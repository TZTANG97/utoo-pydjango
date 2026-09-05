"""积分兑换 — redeem/*"""
from __future__ import annotations

import logging
from typing import Any

from qd_common.serialize import to_jsonable

from apps.core.db_utils import fetch_all, fetch_one, scalar

logger = logging.getLogger(__name__)


def user_redeem_log_list(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    status: str = "",
) -> dict[str, Any]:
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    draw_n = int(draw) if draw.isdigit() else 1
    extra = ""
    params: dict[str, Any] = {"uid": user_id, "offset": offset, "limit": limit}
    if status and status.strip() not in ("0", ""):
        extra += " AND rgl.status = %(status)s"
        params["status"] = status.strip()

    base = f"""
        SELECT rgl.id, rgl.addTime, rgl.rgId, rgl.redeem_time AS redeemTime,
               rgl.redeem_num AS redeemNum, rgl.info, rgl.order_id AS orderId,
               rgl.fh_time AS fhTime, rgl.integralsum, rgl.status,
               rg.good_name AS goodName, eu.trueName AS trueName
        FROM redeem_goods_log rgl
        LEFT JOIN redeem_goods rg ON rgl.rgId = rg.id
        LEFT JOIN exp_user eu ON rgl.exp_user_id = eu.id
        WHERE rgl.deleteStatus = 0 AND rgl.rtype = 2 AND rgl.exp_user_id = %(uid)s
        {extra}
    """
    try:
        total = int(
            scalar(f"SELECT COUNT(1) FROM ({base}) tab", params, 0) or 0
        )
        rows = fetch_all(
            f"""
            SELECT * FROM ({base}) tab
            ORDER BY tab.redeemTime DESC, tab.addTime DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )
        return {
            "data": [to_jsonable(r) for r in rows],
            "draw": draw_n,
            "recordsTotal": total,
            "recordsFiltered": total,
        }
    except Exception as exc:
        logger.warning("user_redeem_log_list failed: %s", exc)
        return {
            "data": [],
            "draw": draw_n,
            "recordsTotal": 0,
            "recordsFiltered": 0,
        }


def redeem_goods_log_detail(*, user_id: int, log_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT rgl.*, rg.good_name AS goodName
        FROM redeem_goods_log rgl
        LEFT JOIN redeem_goods rg ON rgl.rgId = rg.id
        WHERE rgl.id = %(id)s AND rgl.deleteStatus = 0
          AND rgl.exp_user_id = %(uid)s
        LIMIT 1
        """,
        {"id": log_id, "uid": user_id},
    )
    if not row:
        return None
    return {"obj": to_jsonable(row)}
