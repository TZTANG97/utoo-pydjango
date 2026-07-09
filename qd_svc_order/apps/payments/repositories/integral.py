from __future__ import annotations

from typing import Any

from apps.core.db_utils import scalar


def sum_integral(
    *, user_id: int, mobile: str, start=None, end=None
) -> float:
    clauses = ["t.deleteStatus = 0"]
    params: dict[str, Any] = {"user_id": user_id, "mobile": mobile}
    if start:
        clauses.append("t.addTime >= %(start)s")
        params["start"] = start
    if end:
        clauses.append("t.addTime <= %(end)s")
        params["end"] = end
    sql = f"""
        SELECT IFNULL(SUM(t.integral), 0)
        FROM integrallog t
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        WHERE {' AND '.join(clauses)}
          AND (t.user_id = %(user_id)s OR quc.contract_phone = %(mobile)s)
    """
    try:
        return float(scalar(sql, params, 0) or 0)
    except Exception:
        return 0.0
