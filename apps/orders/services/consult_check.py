"""业务咨询查询 — isServiceConsult.ajax"""
from __future__ import annotations

from apps.core.db_utils import fetch_one


def is_service_consult(order_id: str) -> tuple[bool, str]:
    if not order_id or not str(order_id).strip().isdigit():
        return False, "参数错误"
    row = fetch_one(
        """
        SELECT id FROM service_consult
        WHERE deleteStatus = 0 AND order_id = %(oid)s
        LIMIT 1
        """,
        {"oid": int(order_id)},
    )
    if row:
        return True, "有用户业务咨询"
    return False, "没有用户业务咨询"
