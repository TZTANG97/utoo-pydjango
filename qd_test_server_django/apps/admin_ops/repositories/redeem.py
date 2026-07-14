from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def list_redeem_logs(
    *,
    order_startime: str = "",
    order_endtime: str = "",
    status: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE rgl.deleteStatus = 0 AND rgl.rtype = 2"
    params: dict[str, Any] = {}
    if order_startime:
        where += " AND rgl.redeem_time >= %(order_startime)s"
        params["order_startime"] = order_startime
    if order_endtime:
        where += " AND rgl.redeem_time <= %(order_endtime)s"
        params["order_endtime"] = order_endtime
    if status not in (None, ""):
        where += " AND rgl.fhstatus = %(status)s"
        params["status"] = status
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM redeem_goods_log rgl
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            rgl.id,
            rgl.addTime,
            rgl.rgId,
            rgl.user_id AS userId,
            rgl.redeem_time AS redeemTime,
            rgl.redeem_num AS redeemNum,
            rgl.exp_user_id AS expUserId,
            rgl.rtype,
            rgl.info,
            rgl.order_id AS orderId,
            rgl.fh_time AS fhTime,
            rgl.integralsum AS Integralsum,
            rgl.fhstatus,
            rgl.express_company AS expressCompany,
            rgl.express_num AS expressNum,
            rgl.user_name AS userName,
            rgl.mobile,
            rgl.address,
            rg.good_name AS goodName
        FROM redeem_goods_log rgl
        LEFT JOIN redeem_goods rg ON rgl.rgId = rg.id
        {where}
        ORDER BY rgl.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_redeem_log(log_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            rgl.id,
            rgl.addTime,
            rgl.rgId,
            rgl.user_id AS userId,
            rgl.redeem_time AS redeemTime,
            rgl.redeem_num AS redeemNum,
            rgl.exp_user_id AS expUserId,
            rgl.rtype,
            rgl.info,
            rgl.order_id AS orderId,
            rgl.fh_time AS fhTime,
            rgl.integralsum AS Integralsum,
            rgl.fhstatus,
            rgl.express_company AS expressCompany,
            rgl.express_num AS expressNum,
            rgl.user_name AS userName,
            rgl.mobile,
            rgl.address,
            rg.good_name AS goodName
        FROM redeem_goods_log rgl
        LEFT JOIN redeem_goods rg ON rgl.rgId = rg.id
        WHERE rgl.id = %(id)s
        LIMIT 1
        """,
        {"id": log_id},
    )


def ship_redeem_log(*, log_id: int, mark: str, number: str) -> bool:
    affected = execute(
        """
        UPDATE redeem_goods_log
        SET fhstatus = 2,
            express_company = %(mark)s,
            express_num = %(number)s,
            fh_time = NOW()
        WHERE id = %(id)s
        """,
        {"id": log_id, "mark": mark, "number": number},
    )
    return affected > 0
