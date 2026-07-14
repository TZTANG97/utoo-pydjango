from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.admin_auth.repositories import billing as billing_repo
from apps.core.db_utils import execute, execute_insert, fetch_one
from apps.payments.repositories import user_account as ua_repo
from apps.payments.repositories.pay_order_code import payment_pa_num_generate
from apps.payments.repositories.qd_bill import insert_receive_bill

logger = logging.getLogger(__name__)


@transaction.atomic
def reject_invoice(*, apply_id: int, staff_user_id: str) -> tuple[bool, str]:
    row = billing_repo.get_invoice_apply(apply_id)
    if not row:
        return False, "发票申请不存在"
    if int(row.get("status") or 0) != 1:
        return False, "仅开票中的申请可驳回"

    execute(
        "UPDATE invoice_apply_log SET status = 5 WHERE id = %(id)s",
        {"id": apply_id},
    )
    money = Decimal(str(row.get("invoice_money") or 0))
    if money > 0:
        ua_repo.get_or_create(int(row["user_id"]))
        execute(
            """
            UPDATE user_account
            SET invoicing_amount = GREATEST(COALESCE(invoicing_amount, 0) - %(m)s, 0),
                update_time = NOW()
            WHERE delete_status = 0 AND user_id = %(uid)s
            """,
            {"m": float(money), "uid": int(row["user_id"])},
        )

    order_ids = str(row.get("order_ids") or "").split(",")
    for of_id in order_ids:
        of_id = of_id.strip()
        if not of_id.isdigit():
            continue
        eo = fetch_one(
            "SELECT id, is_online FROM experiment_order WHERE id = %(id)s LIMIT 1",
            {"id": int(of_id)},
        )
        if not eo:
            continue
        if int(eo.get("is_online") or 0) == 1:
            execute(
                """
                UPDATE qd_bill SET is_apply = 0
                WHERE exp_of_id = %(oid)s AND type = 2
                """,
                {"oid": int(of_id)},
            )
        else:
            execute(
                "UPDATE experiment_order SET is_apply = 0 WHERE id = %(id)s",
                {"id": int(of_id)},
            )

    execute_insert(
        """
        INSERT INTO invoice_record_log
            (content, invoice_apply_id, user_id, addTime, deleteStatus)
        VALUES ('驳回开票申请', %(aid)s, %(uid)s, NOW(), 0)
        """,
        {"aid": apply_id, "uid": staff_user_id},
    )
    return True, "驳回成功"


@transaction.atomic
def agree_payment(*, apply_id: int, staff_user_id: str) -> tuple[bool, str]:
    row = billing_repo.get_payment_application(apply_id)
    if not row:
        return False, "付款申请不存在"
    if str(row.get("applyStatus")) != "1":
        return False, "仅待审核申请可操作"

    order_type = str(row.get("orderType") or "")
    user_id = int(row["userId"])
    money = Decimal(str(row.get("money") or 0))

    if order_type in ("2", "3"):
        order_id = str(row.get("orderId") or "")
        if order_id.isdigit():
            execute(
                "UPDATE experiment_order SET isUploadReceipt = 2 WHERE id = %(id)s",
                {"id": int(order_id)},
            )
            insert_receive_bill(
                order_id=int(order_id),
                money=money,
                user_id=int(staff_user_id),
                log_info="同意付款申请",
            )
        pay_type = 3
    elif order_type == "1":
        account = ua_repo.get_or_create(user_id)
        execute(
            """
            UPDATE user_account
            SET amount = COALESCE(amount, 0) + %(m)s, update_time = NOW()
            WHERE id = %(id)s
            """,
            {"m": float(money), "id": int(account["id"])},
        )
        pay_type = 1
    elif order_type == "4":
        pay_type = 4
    else:
        return False, f"暂不支持的申请类型: {order_type}"

    pa_num = payment_pa_num_generate(str(pay_type))
    pay_log_id = execute_insert(
        """
        INSERT INTO pay_info_log
            (addTime, deleteStatus, user_id, money, status, order_id,
             pay_type, pay_way, pa_num, pa_id)
        VALUES
            (NOW(), 0, %(uid)s, %(money)s, 2, %(order_id)s,
             %(pay_type)s, 3, %(pa_num)s, %(pa_id)s)
        """,
        {
            "uid": user_id,
            "money": float(money),
            "order_id": str(row.get("orderId") or ""),
            "pay_type": pay_type,
            "pa_num": pa_num,
            "pa_id": apply_id,
        },
    )
    execute(
        "UPDATE payment_application SET applyStatus = '2' WHERE id = %(id)s",
        {"id": apply_id},
    )
    execute_insert(
        """
        INSERT INTO payment_application_log
            (content, payment_application_id, user_id, addTime, deleteStatus)
        VALUES ('同意付款申请', %(pid)s, %(uid)s, NOW(), 0)
        """,
        {"pid": apply_id, "uid": staff_user_id},
    )
    logger.info("agree payment apply=%s pay_log=%s", apply_id, pay_log_id)
    return True, "确认付款成功"


@transaction.atomic
def refuse_payment(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_payment_application(apply_id)
    if not row:
        return False, "付款申请不存在"
    if str(row.get("applyStatus")) != "1":
        return False, "仅待审核申请可操作"

    order_type = str(row.get("orderType") or "")
    if order_type in ("2", "3"):
        order_id = str(row.get("orderId") or "")
        if order_id.isdigit():
            execute(
                "UPDATE experiment_order SET isUploadReceipt = 3 WHERE id = %(id)s",
                {"id": int(order_id)},
            )
    elif order_type == "4":
        money = Decimal(str(row.get("money") or 0))
        ua_repo.get_or_create(int(row["userId"]))
        execute(
            """
            UPDATE user_account
            SET amount = COALESCE(amount, 0) + %(m)s, update_time = NOW()
            WHERE delete_status = 0 AND user_id = %(uid)s
            """,
            {"m": float(money), "uid": int(row["userId"])},
        )

    execute(
        """
        UPDATE payment_application
        SET applyStatus = '3', mark = %(mark)s
        WHERE id = %(id)s
        """,
        {"id": apply_id, "mark": mark or ""},
    )
    execute_insert(
        """
        INSERT INTO payment_application_log
            (content, payment_application_id, user_id, addTime, deleteStatus)
        VALUES ('拒绝付款申请', %(pid)s, %(uid)s, NOW(), 0)
        """,
        {"pid": apply_id, "uid": staff_user_id},
    )
    return True, "拒绝付款成功"


@transaction.atomic
def agree_retest(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_retest_application(apply_id)
    if not row:
        return False, "复测申请不存在"
    if int(row.get("applyStatus") or -1) != 0:
        return False, "仅待审核申请可操作"

    child_id = str(row.get("orderId") or "")
    execute(
        """
        UPDATE retest_application
        SET applyStatus = 1, remeasurement_require = %(mark)s
        WHERE id = %(id)s
        """,
        {"id": apply_id, "mark": mark or ""},
    )
    if child_id.isdigit():
        child = fetch_one(
            """
            SELECT id, orderStatus FROM experiment_order_child
            WHERE id = %(id)s LIMIT 1
            """,
            {"id": int(child_id)},
        )
        if child:
            status = int(child.get("orderStatus") or 0)
            new_status = status
            if status == 38:
                new_status = 35
            elif status == 40:
                new_status = 36
            execute(
                """
                UPDATE experiment_order_child
                SET fcsq = 0, orderStatus = %(status)s
                WHERE id = %(id)s
                """,
                {"id": int(child_id), "status": new_status},
            )
    execute_insert(
        """
        INSERT INTO retest_application_log
            (retest_application_id, content, user_id, addTime, deleteStatus)
        VALUES (%(aid)s, '同意复测申请', %(uid)s, NOW(), 0)
        """,
        {"aid": apply_id, "uid": staff_user_id},
    )
    return True, "同意复测成功"


@transaction.atomic
def refuse_retest(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_retest_application(apply_id)
    if not row:
        return False, "复测申请不存在"
    if int(row.get("applyStatus") or -1) != 0:
        return False, "仅待审核申请可操作"

    execute(
        """
        UPDATE retest_application
        SET applyStatus = 2, remeasurement_require = %(mark)s
        WHERE id = %(id)s
        """,
        {"id": apply_id, "mark": mark or ""},
    )
    execute_insert(
        """
        INSERT INTO retest_application_log
            (retest_application_id, content, user_id, addTime, deleteStatus)
        VALUES (%(aid)s, '复测申请驳回', %(uid)s, NOW(), 0)
        """,
        {"aid": apply_id, "uid": staff_user_id},
    )
    return True, "拒绝复测成功"
