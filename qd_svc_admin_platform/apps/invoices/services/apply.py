import logging
from datetime import datetime

from django.db import transaction

from apps.auth_support.services.customer import CustomerUserService
from apps.core.db_utils import execute, fetch_one, scalar
from apps.invoices.services.summary import stay_apply_money

logger = logging.getLogger(__name__)


def _calc_order_invoice_amount(order_id: int) -> tuple[float, dict | None]:
    of = fetch_one(
        """
        SELECT id, order_id, totalPrice, is_online, is_apply, invoiceType
        FROM experiment_order WHERE id = %(oid)s LIMIT 1
        """,
        {"oid": order_id},
    )
    if not of:
        return 0.0, None
    if int(of.get("invoiceType") or 0) != 1:
        return 0.0, of
    if int(of.get("is_apply") or 0) == 1:
        return 0.0, of
    total = float(of.get("totalPrice") or 0)
    if int(of.get("is_online") or 0) == 1:
        val = scalar(
            """
            SELECT COALESCE(SUM(money), 0) FROM qd_bill
            WHERE exp_of_id = %(oid)s AND type = 2 AND IFNULL(is_apply, 0) = 0
            """,
            {"oid": order_id},
            0,
        )
        return float(val or 0), of
    kp = scalar(
        """
        SELECT COALESCE(SUM(money), 0) FROM qd_bill
        WHERE exp_of_id = %(oid)s AND type = 1
        """,
        {"oid": order_id},
        0,
    )
    return max(0.0, total - float(kp or 0)), of


@transaction.atomic
def apply_invoice(
    *,
    user_id: int,
    order_ids: str,
    invoice_title: str,
    inv_type: int = 2,
    is_pay: int = 0,
    notes: str = "",
    bank_name: str = "",
    bank_account: str = "",
    reg_address: str = "",
    reg_mobile: str = "",
) -> tuple[bool, str]:
    ids = [x.strip() for x in (order_ids or "").split(",") if x.strip()]
    if not ids:
        return False, "请至少选择一条数据"
    if not (invoice_title or "").strip():
        return False, "请填写发票抬头"

    user = CustomerUserService.get_by_id(user_id)
    mobile = (user.mobile or "") if user else ""

    total_money = 0.0
    money_parts: list[str] = []
    valid_ids: list[str] = []
    for oid_s in ids:
        try:
            oid = int(oid_s)
        except ValueError:
            return False, f"订单编号({oid_s})无效"
        amt, of = _calc_order_invoice_amount(oid)
        if not of:
            return False, f"订单({oid_s})不存在"
        check = fetch_one(
            """
            SELECT 1 FROM experiment_order t
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
            WHERE t.id = %(oid)s
              AND (
                t.custom_user_id = %(uid)s
                OR CAST(t.custom_user_id AS CHAR) = %(uid_str)s
                OR quc.contract_phone = %(mobile)s
                OR t.mobile = %(mobile)s
              )
            LIMIT 1
            """,
            {"oid": oid, "uid": user_id, "uid_str": str(user_id), "mobile": mobile},
        )
        if not check:
            return False, "无权操作该订单"
        if amt <= 0:
            return False, f"订单{of.get('order_id')}暂无可开票金额"
        total_money += amt
        money_parts.append(str(round(amt, 2)))
        valid_ids.append(str(oid))

    cap = stay_apply_money(user_id)
    if total_money > cap + 0.01:
        return False, f"用户开票金额已达上限,可开票金额({cap:.2f})"

    order_ids_str = ",".join(valid_ids)
    moneys_str = ",".join(money_parts)
    invoice_num = f"FP{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"

    execute(
        """
        INSERT INTO invoice_apply_log
            (addTime, deleteStatus, user_id, invoice_title, invoice_money,
             type, status, order_ids, is_pay, notes, bank_name, bank_account,
             reg_address, reg_mobile, invoice_num, moneys, invoice_type, order_type)
        VALUES
            (NOW(), 0, %(uid)s, %(title)s, %(money)s, %(tp)s, 1, %(oids)s, %(is_pay)s,
             %(notes)s, %(bank_name)s, %(bank_account)s, %(reg_address)s, %(reg_mobile)s,
             %(inum)s, %(moneys)s, %(tp)s, 2)
        """,
        {
            "uid": user_id,
            "title": invoice_title.strip(),
            "money": total_money,
            "tp": inv_type,
            "oids": order_ids_str,
            "is_pay": is_pay,
            "notes": notes or "",
            "bank_name": bank_name or "",
            "bank_account": bank_account or "",
            "reg_address": reg_address or "",
            "reg_mobile": reg_mobile or "",
            "inum": invoice_num,
            "moneys": moneys_str,
        },
    )

    for oid_s in valid_ids:
        oid = int(oid_s)
        _, of = _calc_order_invoice_amount(oid)
        if not of:
            continue
        if int(of.get("is_online") or 0) == 1:
            execute(
                """
                UPDATE qd_bill SET is_apply = 1
                WHERE exp_of_id = %(oid)s AND type = 2 AND IFNULL(is_apply, 0) = 0
                """,
                {"oid": oid},
            )
        else:
            execute(
                "UPDATE experiment_order SET is_apply = 1 WHERE id = %(oid)s",
                {"oid": oid},
            )
        try:
            execute(
                """
                INSERT INTO exp_user_log (user_id, info, addTime, deleteStatus)
                VALUES (%(uid)s, %(info)s, NOW(), 0)
                """,
                {
                    "uid": user_id,
                    "info": f"申请开票成功，关联单号{of.get('order_id')}",
                },
            )
        except Exception as exc:
            logger.warning("exp_user_log insert failed: %s", exc)

    return True, "申请成功"
