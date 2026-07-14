from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_accounts(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = scalar("SELECT COUNT(*) FROM company_account_info WHERE deleteStatus = 0")
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT id, company_name, bankCardNum, bank, addTime, deleteStatus, defaultaccount
        FROM company_account_info
        WHERE deleteStatus = 0
        ORDER BY addTime DESC
        {clause}
        """,
        page_params,
    )
    return [_normalize_account(row) for row in rows], int(total)


def get_account(account_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, company_name, bankCardNum, bank, addTime, deleteStatus, defaultaccount
        FROM company_account_info WHERE id = %(id)s
        """,
        {"id": account_id},
    )
    return _normalize_account(row) if row else None


def get_default_account() -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, company_name, bankCardNum, bank, defaultaccount
        FROM company_account_info
        WHERE deleteStatus = 0 AND defaultaccount = 1
        LIMIT 1
        """
    )
    return _normalize_account(row) if row else None


def find_by_card_num(bank_card_num: str, exclude_id: int | None = None) -> dict[str, Any] | None:
    params: dict[str, Any] = {"card": bank_card_num}
    sql = """
        SELECT id FROM company_account_info
        WHERE bankCardNum = %(card)s AND deleteStatus = 0
    """
    if exclude_id:
        sql += " AND id != %(exclude_id)s"
        params["exclude_id"] = exclude_id
    return fetch_one(sql + " LIMIT 1", params)


def insert_account(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO company_account_info
            (company_name, bankCardNum, bank, addTime, deleteStatus, defaultaccount)
        VALUES
            (%(company_name)s, %(bankCardNum)s, %(bank)s, NOW(), 0, 0)
        """,
        {
            "company_name": data.get("company_name") or "",
            "bankCardNum": data.get("bankCardNum") or "",
            "bank": data.get("bank") or "",
        },
    )


def update_account(account_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE company_account_info
        SET company_name = %(company_name)s,
            bankCardNum = %(bankCardNum)s,
            bank = %(bank)s
        WHERE id = %(id)s
        """,
        {"id": account_id, **data},
    )


def soft_delete_account(account_id: int) -> None:
    execute(
        "UPDATE company_account_info SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": account_id},
    )


def set_default_account(account_id: int) -> None:
    execute(
        "UPDATE company_account_info SET defaultaccount = 0 WHERE defaultaccount = 1"
    )
    execute(
        "UPDATE company_account_info SET defaultaccount = 1 WHERE id = %(id)s",
        {"id": account_id},
    )


def _normalize_account(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "companyName": row.get("company_name"),
        "bankCardNum": row.get("bankCardNum"),
        "bank": row.get("bank"),
        "addTime": row.get("addTime"),
        "deleteStatus": bool(row.get("deleteStatus")),
        "defaultAccount": row.get("defaultaccount"),
    }
