from __future__ import annotations

from typing import Any

from apps.admin_member.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_applies(
    *,
    company_name: str = "",
    state: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE 1=1"
    params: dict[str, Any] = {}
    if company_name:
        where += " AND a.company_name LIKE %(company_name)s"
        params["company_name"] = f"%{company_name}%"
    if state not in (None, ""):
        where += " AND a.state = %(state)s"
        params["state"] = state
    total = int(scalar(f"SELECT COUNT(*) FROM apply_vip_user a {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            a.id, a.addTime, a.apply_user AS applyUser, a.phone,
            a.company_name AS companyName, a.state,
            a.last_operator_id AS lastOperatorId,
            su.user_name AS lastOperatorName
        FROM apply_vip_user a
        LEFT JOIN sy_users su ON a.last_operator_id = su.id
        {where}
        ORDER BY a.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_apply(apply_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            id, addTime, apply_user AS applyUser, phone,
            company_name AS companyName, state, last_operator_id AS lastOperatorId
        FROM apply_vip_user
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": apply_id},
    )


def set_state(apply_id: int, *, state: int, operator_id: str | None) -> None:
    execute(
        """
        UPDATE apply_vip_user
        SET state = %(state)s, last_operator_id = %(operator_id)s
        WHERE id = %(id)s
        """,
        {"id": apply_id, "state": state, "operator_id": operator_id},
    )


def insert_apply(*, apply_user: str, phone: str, company_name: str) -> int:
    return execute_insert(
        """
        INSERT INTO apply_vip_user (addTime, apply_user, phone, company_name, state)
        VALUES (NOW(), %(apply_user)s, %(phone)s, %(company_name)s, 3)
        """,
        {"apply_user": apply_user, "phone": phone, "company_name": company_name},
    )
