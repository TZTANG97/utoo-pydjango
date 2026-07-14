import logging
from typing import Any

from django.db import transaction

from apps.core.db_utils import execute, fetch_all, fetch_one
from qd_common.serialize import to_jsonable

logger = logging.getLogger(__name__)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    d = to_jsonable(row)
    if d.get("is_default") is not None:
        d["is_default"] = int(d["is_default"]) == 1
    return d


def list_invoice_infos(user_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT * FROM invoice_info
        WHERE user_id = %(uid)s AND deleteStatus = 0
        ORDER BY is_default DESC, addTime DESC
        """,
        {"uid": user_id},
    )
    return [_normalize_row(r) for r in rows]


def get_default_invoice_info(user_id: int) -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT * FROM invoice_info
        WHERE user_id = %(uid)s AND deleteStatus = 0
        ORDER BY is_default DESC, addTime DESC
        LIMIT 1
        """,
        {"uid": user_id},
    )
    if not row:
        return {}
    return _normalize_row(row)


@transaction.atomic
def insert_invoice_info(
    *,
    user_id: int,
    invoice_title: str,
    tax_num: str = "",
    bank: str = "",
    bank_card_num: str = "",
    address: str = "",
    mobile: str = "",
    email: str = "",
) -> tuple[bool, str]:
    if not (invoice_title or "").strip():
        return False, "发票抬头不能为空"
    existing = list_invoice_infos(user_id)
    is_default = 0 if existing else 1
    try:
        execute(
            """
            INSERT INTO invoice_info
                (addTime, deleteStatus, user_id, invoice_title, taxNum,
                 bank, bankCardNum, address, mobile, email, is_default)
            VALUES
                (NOW(), 0, %(uid)s, %(title)s, %(tax)s, %(bank)s, %(card)s,
                 %(addr)s, %(mobile)s, %(email)s, %(is_def)s)
            """,
            {
                "uid": user_id,
                "title": invoice_title.strip(),
                "tax": tax_num or "",
                "bank": bank or "",
                "card": bank_card_num or "",
                "addr": address or "",
                "mobile": mobile or "",
                "email": email or "",
                "is_def": is_default,
            },
        )
        return True, "新增成功"
    except Exception as exc:
        logger.exception("insert_invoice_info failed: %s", exc)
        return False, f"新增失败：{exc}"


@transaction.atomic
def update_invoice_info(
    *,
    user_id: int,
    record_id: int,
    invoice_title: str,
    tax_num: str = "",
    bank: str = "",
    bank_card_num: str = "",
    address: str = "",
    mobile: str = "",
    email: str = "",
    address_info: str = "",
) -> tuple[bool, str]:
    owner = fetch_one(
        """
        SELECT id FROM invoice_info
        WHERE id = %(rid)s AND user_id = %(uid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"rid": record_id, "uid": user_id},
    )
    if not owner:
        return False, "发票信息不存在"
    try:
        execute(
            """
            UPDATE invoice_info SET
                invoice_title = %(title)s,
                taxNum = %(tax)s,
                bank = %(bank)s,
                bankCardNum = %(card)s,
                address = %(addr)s,
                mobile = %(mobile)s,
                email = %(email)s,
                address_info = %(addr_info)s
            WHERE id = %(rid)s AND user_id = %(uid)s
            """,
            {
                "rid": record_id,
                "uid": user_id,
                "title": invoice_title or "",
                "tax": tax_num or "",
                "bank": bank or "",
                "card": bank_card_num or "",
                "addr": address or "",
                "mobile": mobile or "",
                "email": email or "",
                "addr_info": address_info or "",
            },
        )
        return True, "修改成功！"
    except Exception as exc:
        logger.exception("update_invoice_info failed: %s", exc)
        return False, f"修改失败：{exc}"


@transaction.atomic
def delete_or_set_default_invoice(
    *, user_id: int, record_id: int, op_type: str
) -> tuple[bool, str]:
    row = fetch_one(
        """
        SELECT id, is_default FROM invoice_info
        WHERE id = %(rid)s AND user_id = %(uid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"rid": record_id, "uid": user_id},
    )
    if not row:
        return False, "发票信息不存在"

    if op_type == "1":
        if int(row.get("is_default") or 0) == 1:
            return False, "默认地址不能删除！"
        try:
            execute(
                "UPDATE invoice_info SET deleteStatus = 1 WHERE id = %(rid)s",
                {"rid": record_id},
            )
            return True, "删除成功！"
        except Exception as exc:
            return False, f"删除失败：{exc}"

    if op_type == "2":
        try:
            execute(
                """
                UPDATE invoice_info SET is_default = 0
                WHERE user_id = %(uid)s AND deleteStatus = 0 AND is_default = 1
                """,
                {"uid": user_id},
            )
            execute(
                "UPDATE invoice_info SET is_default = 1 WHERE id = %(rid)s",
                {"rid": record_id},
            )
            return True, "设置成功！"
        except Exception as exc:
            return False, f"设置失败：{exc}"

    return False, "无效操作类型"


def upsert_legacy_invoice_info(
    *, user_id: int, payload: dict[str, Any]
) -> tuple[bool, str]:
    existing = list_invoice_infos(user_id)
    fields = {
        "title": payload.get("invoice_title") or payload.get("invoiceTitle") or "",
        "tax": payload.get("taxNum") or payload.get("tax_num") or "",
        "bank": payload.get("bank") or "",
        "card": payload.get("bankCardNum") or payload.get("bank_card_num") or "",
        "addr": payload.get("address") or "",
        "mobile": payload.get("mobile") or "",
        "email": payload.get("email") or "",
        "addr_info": payload.get("address_info") or payload.get("addressInfo") or "",
    }
    if existing:
        rid = int(existing[0]["id"])
        ok_flag, msg = update_invoice_info(
            user_id=user_id,
            record_id=rid,
            invoice_title=fields["title"],
            tax_num=fields["tax"],
            bank=fields["bank"],
            bank_card_num=fields["card"],
            address=fields["addr"],
            mobile=fields["mobile"],
            email=fields["email"],
            address_info=fields["addr_info"],
        )
        return ok_flag, "修改成功!" if ok_flag else msg
    ok_flag, msg = insert_invoice_info(
        user_id=user_id,
        invoice_title=fields["title"],
        tax_num=fields["tax"],
        bank=fields["bank"],
        bank_card_num=fields["card"],
        address=fields["addr"],
        mobile=fields["mobile"],
        email=fields["email"],
    )
    return ok_flag, "添加成功!" if ok_flag else msg
