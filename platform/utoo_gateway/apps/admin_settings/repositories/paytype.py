from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return " LIMIT %(limit)s OFFSET %(offset)s", {"limit": page_size, "offset": offset}


def list_paytypes(page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar("SELECT COUNT(*) FROM qd_consume_paytype")
    clause, params = _page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, name, del_status, nums, scale_val, pay_type, jszq, add_time, memo
        FROM qd_consume_paytype
        ORDER BY add_time DESC
        {clause}
        """,
        params,
    )
    return [_normalize_paytype(row) for row in rows], int(total)


def list_all_by_pay_type(pay_type: int) -> list[dict[str, Any]]:
    """对齐 Java getConsumePaytype(payType)：下拉全量。"""
    rows = fetch_all(
        """
        SELECT id, name, del_status, nums, scale_val, pay_type, jszq, add_time, memo
        FROM qd_consume_paytype
        WHERE IFNULL(del_status, 0) = 0 AND pay_type = %(pt)s
        ORDER BY id ASC
        """,
        {"pt": pay_type},
    )
    return [_normalize_paytype(row) for row in rows]


def get_paytype(paytype_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, name, del_status, nums, scale_val, pay_type, jszq, add_time, memo
        FROM qd_consume_paytype WHERE id = %(id)s
        """,
        {"id": paytype_id},
    )
    return _normalize_paytype(row) if row else None


def find_by_name(name: str) -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT id FROM qd_consume_paytype WHERE name = %(name)s",
        {"name": name},
    )


def insert_paytype(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO qd_consume_paytype
            (name, del_status, nums, scale_val, pay_type, jszq, add_time, memo)
        VALUES
            (%(name)s, 0, %(nums)s, %(scale_val)s, %(pay_type)s, %(jszq)s, NOW(), %(memo)s)
        """,
        data,
    )


def update_paytype_status(*, paytype_id: int, disabled: bool) -> None:
    execute(
        """
        UPDATE qd_consume_paytype
        SET del_status = %(del_status)s, update_time = NOW()
        WHERE id = %(id)s
        """,
        {"id": paytype_id, "del_status": 1 if disabled else 0},
    )


def build_scale_val(pay_type: int, nums: int) -> str:
    if pay_type == 3:
        return ""
    if pay_type == 2 and nums > 0:
        parts: list[str] = []
        base, rem = divmod(100, nums)
        for i in range(nums):
            parts.append(str(base if i < nums - 1 else base + rem))
        return ",".join(parts)
    return ""


def _normalize_paytype(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "delStatus": bool(row.get("del_status")),
        "scaleVal": row.get("scale_val"),
        "payType": row.get("pay_type"),
    }
