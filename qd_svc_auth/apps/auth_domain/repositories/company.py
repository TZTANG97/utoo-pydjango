from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_one


def find_company_by_name(name: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id FROM qd_user_company
        WHERE name = %(name)s AND delete_status = 0 LIMIT 1
        """,
        {"name": name},
    )


def insert_company(*, name: str, contract_phone: str = "") -> int:
    return execute_insert(
        """
        INSERT INTO qd_user_company
            (name, type, contract_phone, delete_status, add_time)
        VALUES (%(name)s, 3, %(phone)s, 0, NOW())
        """,
        {"name": name, "phone": contract_phone or ""},
    )


def update_company(
    *,
    company_id: int,
    name: str = "",
    country: str = "",
    area_id: str = "",
    address: str = "",
    tax_num: str = "",
    bank: str = "",
    bank_card_num: str = "",
    contract_phone: str = "",
) -> int:
    return execute(
        """
        UPDATE qd_user_company SET
            name = COALESCE(NULLIF(%(name)s, ''), name),
            country = COALESCE(NULLIF(%(country)s, ''), country),
            area_id = COALESCE(NULLIF(%(area_id)s, ''), area_id),
            address = COALESCE(NULLIF(%(address)s, ''), address),
            taxNum = COALESCE(NULLIF(%(tax_num)s, ''), taxNum),
            bank = COALESCE(NULLIF(%(bank)s, ''), bank),
            bankCardNum = COALESCE(NULLIF(%(bank_card)s, ''), bankCardNum),
            contract_phone = COALESCE(NULLIF(%(phone)s, ''), contract_phone)
        WHERE id = %(cid)s AND delete_status = 0
        """,
        {
            "cid": company_id,
            "name": name or "",
            "country": country or "",
            "area_id": area_id or "",
            "address": address or "",
            "tax_num": tax_num or "",
            "bank": bank or "",
            "bank_card": bank_card_num or "",
            "phone": contract_phone or "",
        },
    )
