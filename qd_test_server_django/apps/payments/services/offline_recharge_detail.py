"""线下充值详情 — offlineRecharge/rechargeDetail.ajax"""
from __future__ import annotations

from typing import Any

from qd_common.serialize import to_jsonable

from apps.core.db_utils import fetch_all, fetch_one


def get_recharge_detail(*, user_id: int, recharge_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT * FROM exp_offline_recharge
        WHERE id = %(id)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"id": recharge_id},
    )
    if not row:
        return None
    if int(row.get("user_id") or 0) != int(user_id):
        return None

    files = fetch_all(
        """
        SELECT id, path, name, info, ext FROM accessory
        WHERE deleteStatus = 0 AND off_recharge_id = %(rid)s
        """,
        {"rid": recharge_id},
    )
    logs = fetch_all(
        """
        SELECT id, content, addTime, log_user_id
        FROM exp_offline_recharge_log
        WHERE recharge_id = %(rid)s AND deleteStatus = 0
        ORDER BY addTime ASC
        """,
        {"rid": recharge_id},
    )
    bills = fetch_all(
        """
        SELECT id, money, bill_date, type FROM qd_bill
        WHERE deleteStatus = 0 AND exp_of_id = %(rid)s AND type = 1
        """,
        {"rid": recharge_id},
    )
    return {
        "obj": to_jsonable(row),
        "files": [to_jsonable(f) for f in files],
        "logs": [to_jsonable(l) for l in logs],
        "openBills": [to_jsonable(b) for b in bills],
        "viewKpBtn": len(bills) == 0,
        "syUser": {},
    }
