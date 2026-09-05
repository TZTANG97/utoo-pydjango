from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_row, page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def list_buyback(
    *,
    state: str = "",
    device_name: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if state:
        where += " AND apb.state = %(state)s"
        params["state"] = int(state)
    if device_name:
        where += " AND apb.device_name LIKE %(device_name)s"
        params["device_name"] = f"%{device_name}%"
    total = int(scalar(f"SELECT COUNT(*) FROM apply_buy_back apb {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT apb.*, su.true_name AS last_operator_name
        FROM apply_buy_back apb
        LEFT JOIN sy_users su ON su.id = apb.last_operator_id
        {where}
        ORDER BY apb.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_buyback(row) for row in rows], total


def _normalize_buyback(row: dict[str, Any]) -> dict[str, Any]:
    base = normalize_row(row) or {}
    return {
        **base,
        "userName": row.get("apply_user"),
        "mobile": row.get("phone"),
        "lastOperatorName": row.get("last_operator_name"),
    }


def update_buyback(*, record_id: int, state: int, operator_id: str) -> None:
    execute(
        """
        UPDATE apply_buy_back
        SET state = %(state)s, last_operator_id = %(operator_id)s
        WHERE id = %(id)s
        """,
        {"id": record_id, "state": state, "operator_id": operator_id},
    )
