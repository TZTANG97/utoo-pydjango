from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.admin_auth.repositories import billing as billing_repo
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one
from apps.payments.repositories import user_account as ua_repo
from apps.payments.repositories.pay_order_code import payment_pa_num_generate
from apps.payments.repositories.qd_bill import insert_receive_bill

logger = logging.getLogger(__name__)

# 对齐 Java ChildOrderStatusEnum
ST_ARRIVE = 36  # 样品到货 YPDH
ST_PICK = 37  # 样品领用 YPLY
ST_TEST_DONE = 39  # 测试完成 CSWC
ST_RETURN = 41  # 样品归还 YPGH


def _safe_staff_uid(staff_user_id: str | int | None) -> int | None:
    text = str(staff_user_id or "").strip()
    if text.isdigit():
        return int(text)
    return None


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
    # 对齐 Java bohuiInvoice：驳回后 ADD 回可开票金额
    money = Decimal(str(row.get("invoice_money") or 0))
    if money > 0:
        ua_repo.get_or_create(int(row["user_id"]))
        execute(
            """
            UPDATE user_account
            SET invoicing_amount = COALESCE(invoicing_amount, 0) + %(m)s,
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
        {"aid": apply_id, "uid": str(staff_user_id or "").strip() or "0"},
    )
    return True, "驳回成功"


def get_invoice_open_preview(apply_id: int) -> dict[str, Any] | None:
    """开票弹窗：返回申请 + 关联订单金额行。"""
    row = billing_repo.get_invoice_apply(apply_id)
    if not row:
        return None
    order_ids = [x.strip() for x in str(row.get("order_ids") or "").split(",") if x.strip()]
    moneys = [x.strip() for x in str(row.get("moneys") or "").split(",") if x.strip()]
    related = {str(o.get("id")): o for o in billing_repo.list_invoice_related_orders(str(row.get("order_ids") or ""))}
    lines: list[dict[str, Any]] = []
    for i, oid in enumerate(order_ids):
        if not oid.isdigit():
            continue
        eo = related.get(oid) or fetch_one(
            """
            SELECT id, order_id AS orderNo, totalPrice, order_type AS orderType
            FROM experiment_order WHERE id = %(id)s LIMIT 1
            """,
            {"id": int(oid)},
        )
        if not eo:
            continue
        if i < len(moneys):
            amt = moneys[i]
        elif len(order_ids) == 1:
            amt = str(row.get("invoice_money") or 0)
        else:
            amt = "0"
        lines.append(
            {
                "of_id": int(oid),
                "orderNo": eo.get("orderId") or eo.get("orderNo") or eo.get("order_id") or "",
                "totalPrice": eo.get("totalPrice"),
                "orderType": eo.get("orderType") or eo.get("order_type"),
                "companyName": eo.get("companyName") or eo.get("company_name") or "",
                "amount": amt,
                "mark": "",
            }
        )
    return {**row, "orderLines": lines}


def _write_invoice_member_log(
    *,
    order: dict[str, Any],
    bill_id: int,
    money: Decimal,
) -> None:
    """对齐 Java：线上/线下写入 user_invoice_log 或 company_invoice_log。"""
    of_id = int(order["id"])
    is_online = int(order.get("is_online") or order.get("isOnline") or 0)
    custom_uid = order.get("custom_user_id") or order.get("customUserId")
    company_id = order.get("customer_name") or order.get("customerName")
    try:
        if is_online == 1:
            if custom_uid not in (None, ""):
                execute_insert(
                    """
                    INSERT INTO user_invoice_log
                        (addTime, deleteStatus, of_id, money, user_id, invoice_date, qd_bill_id, type)
                    VALUES
                        (NOW(), 0, %(oid)s, %(money)s, %(uid)s, NOW(), %(bid)s, 0)
                    """,
                    {
                        "oid": of_id,
                        "money": float(money),
                        "uid": int(custom_uid),
                        "bid": bill_id,
                    },
                )
            elif company_id not in (None, ""):
                execute_insert(
                    """
                    INSERT INTO company_invoice_log
                        (addTime, deleteStatus, of_id, money, company_id, invoice_date, qd_bill_id)
                    VALUES
                        (NOW(), 0, %(oid)s, %(money)s, %(cid)s, NOW(), %(bid)s)
                    """,
                    {
                        "oid": of_id,
                        "money": float(money),
                        "cid": int(company_id) if str(company_id).isdigit() else company_id,
                        "bid": bill_id,
                    },
                )
        else:
            if company_id not in (None, ""):
                execute_insert(
                    """
                    INSERT INTO company_invoice_log
                        (addTime, deleteStatus, of_id, money, company_id, invoice_date, qd_bill_id)
                    VALUES
                        (NOW(), 0, %(oid)s, %(money)s, %(cid)s, NOW(), %(bid)s)
                    """,
                    {
                        "oid": of_id,
                        "money": float(money),
                        "cid": int(company_id) if str(company_id).isdigit() else company_id,
                        "bid": bill_id,
                    },
                )
            elif custom_uid not in (None, ""):
                execute_insert(
                    """
                    INSERT INTO user_invoice_log
                        (addTime, deleteStatus, of_id, money, user_id, invoice_date, qd_bill_id, type)
                    VALUES
                        (NOW(), 0, %(oid)s, %(money)s, %(uid)s, NOW(), %(bid)s, 0)
                    """,
                    {
                        "oid": of_id,
                        "money": float(money),
                        "uid": int(custom_uid),
                        "bid": bill_id,
                    },
                )
    except Exception:
        logger.exception("write invoice member log failed of_id=%s bill_id=%s", of_id, bill_id)


@transaction.atomic
def agree_invoice(
    *,
    apply_id: int,
    staff_user_id: str,
    items: list[dict[str, Any]] | None = None,
    mark: str = "",
) -> tuple[bool, str]:
    """对齐 Java addBillDataInvoice：按订单写入开票 qd_bill(type=1)，申请 status=4。"""
    from django.db import DatabaseError

    row = billing_repo.get_invoice_apply(apply_id)
    if not row:
        return False, "发票申请不存在"
    if int(row.get("status") or 0) != 1:
        return False, "仅开票中的申请可开票"

    order_ids = [x.strip() for x in str(row.get("order_ids") or "").split(",") if x.strip()]
    moneys = [x.strip() for x in str(row.get("moneys") or "").split(",") if x.strip()]
    bill_items: list[tuple[int, Decimal, str]] = []

    if items:
        for it in items:
            if not isinstance(it, dict):
                continue
            oid = it.get("of_id") or it.get("orderId") or it.get("id")
            if oid is None or not str(oid).isdigit():
                continue
            try:
                amt = Decimal(str(it.get("amount") or it.get("money") or 0))
            except Exception:
                amt = Decimal("0")
            if amt <= 0:
                return False, "请填写有效开票金额"
            bill_items.append((int(oid), amt, str(it.get("mark") or mark or "")[:500]))
    else:
        if not order_ids:
            return False, "申请未关联订单"
        for i, oid in enumerate(order_ids):
            if not oid.isdigit():
                continue
            if i < len(moneys):
                try:
                    amt = Decimal(str(moneys[i] or 0))
                except Exception:
                    amt = Decimal("0")
            else:
                amt = (
                    Decimal(str(row.get("invoice_money") or 0))
                    if len(order_ids) == 1
                    else Decimal("0")
                )
            if amt <= 0 and len(order_ids) == 1:
                amt = Decimal(str(row.get("invoice_money") or 0))
            if amt <= 0:
                return False, "开票金额无效"
            bill_items.append((int(oid), amt, (mark or "")[:500]))

    if not bill_items:
        return False, "没有可开票的订单"

    staff = _safe_staff_uid(staff_user_id)
    staff_log_uid = str(staff_user_id or "").strip() or (str(staff) if staff else "0")

    try:
        for oid, amt, mk in bill_items:
            eo = fetch_one(
                """
                SELECT id, order_id, is_online, custom_user_id, customer_name
                FROM experiment_order WHERE id = %(id)s LIMIT 1
                """,
                {"id": oid},
            )
            if not eo:
                return False, f"订单不存在: {oid}"
            bill_id = execute_insert(
                """
                INSERT INTO qd_bill
                    (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark)
                VALUES
                    (NOW(), %(uid)s, %(oid)s, %(money)s, 1, 0, NOW(), %(mark)s)
                """,
                {
                    "uid": str(staff) if staff is not None else staff_log_uid,
                    "oid": oid,
                    "money": float(amt),
                    "mark": mk or "同意开票申请",
                },
            )
            _write_invoice_member_log(order=eo, bill_id=int(bill_id), money=amt)
            try:
                execute(
                    "UPDATE experiment_order SET is_apply = 1 WHERE id = %(id)s",
                    {"id": oid},
                )
            except Exception:
                pass
            # 对齐 Java uploadInvoice → saveBillAndAccessory：开票落库后判定主单是否完成
            try:
                from apps.admin_experiment.repositories import orders as order_repo

                order_repo._write_order_log(
                    oid,
                    f"开票 {float(amt)}：同意开票申请",
                    user_id=staff_log_uid,
                )
                order_repo.try_finish_main_order(
                    order_id=oid, staff_user_id=staff_log_uid
                )
            except Exception:
                logger.exception("try_finish after agree_invoice order=%s", oid)

        execute(
            "UPDATE invoice_apply_log SET status = 4 WHERE id = %(id)s",
            {"id": apply_id},
        )
        try:
            execute(
                "UPDATE invoice_apply_log SET wk_order_ids = '' WHERE id = %(id)s",
                {"id": apply_id},
            )
        except Exception:
            pass

        execute_insert(
            """
            INSERT INTO invoice_record_log
                (content, invoice_apply_id, user_id, addTime, deleteStatus)
            VALUES ('同意开票申请', %(aid)s, %(uid)s, NOW(), 0)
            """,
            {"aid": apply_id, "uid": staff_log_uid},
        )
    except DatabaseError as exc:
        logger.exception("agree_invoice db error apply=%s", apply_id)
        return False, f"开票失败：{exc}"
    return True, "开票成功"


def _fill_receive_bills_for_payment(
    *, order_id: int, money: Decimal, staff_user_id: int | None
) -> None:
    """对齐 Java agreepayment：按 collection_time 档位补齐 type=2 收款单。"""
    order = fetch_one(
        """
        SELECT id, collection_time AS collectionTime, pay_way AS payWay, totalPrice
        FROM experiment_order WHERE id = %(id)s LIMIT 1
        """,
        {"id": order_id},
    )
    if not order:
        insert_receive_bill(
            order_id=order_id,
            money=money,
            user_id=staff_user_id or 0,
            log_info="同意付款申请",
        )
        return

    coll = str(order.get("collectionTime") or "").strip()
    slots = [x for x in coll.split(",") if x.strip()] if coll else []
    cnt_row = fetch_one(
        """
        SELECT COUNT(*) AS c FROM qd_bill
        WHERE exp_of_id = %(oid)s AND type = 2
        """,
        {"oid": order_id},
    ) or {}
    try:
        existing_n = int(cnt_row.get("c") or 0)
    except (TypeError, ValueError):
        existing_n = 0

    target = max(len(slots), 1)
    for i in range(existing_n, target):
        amt = money if i == existing_n else Decimal("0")
        insert_receive_bill(
            order_id=order_id,
            money=amt,
            user_id=staff_user_id or 0,
            log_info="同意付款申请" if amt > 0 else "补齐收款档位",
        )


def _resolve_experiment_order_pk(order_ref: str) -> int | None:
    """payment_application.orderId 可能是 experiment_order.id 或业务单号 order_id。"""
    text = str(order_ref or "").strip()
    if not text:
        return None
    if text.isdigit():
        by_pk = fetch_one(
            "SELECT id FROM experiment_order WHERE id = %(id)s LIMIT 1",
            {"id": int(text)},
        )
        if by_pk:
            return int(by_pk["id"])
    by_no = fetch_one(
        "SELECT id FROM experiment_order WHERE order_id = %(no)s LIMIT 1",
        {"no": text},
    )
    if by_no:
        return int(by_no["id"])
    return int(text) if text.isdigit() else None


@transaction.atomic
def agree_payment(*, apply_id: int, staff_user_id: str) -> tuple[bool, str]:
    row = billing_repo.get_payment_application(apply_id)
    if not row:
        return False, "付款申请不存在"
    apply_status = row.get("applyStatus")
    if apply_status is None:
        apply_status = row.get("apply_status")
    if str(apply_status) != "1":
        return False, "仅待审核申请可操作"

    order_type = str(row.get("orderType") if row.get("orderType") is not None else row.get("order_type") or "")
    uid_raw = row.get("userId") if row.get("userId") is not None else row.get("user_id")
    if uid_raw is None:
        return False, "申请缺少用户"
    user_id = int(uid_raw)
    money = Decimal(str(row.get("money") or 0))
    staff = _safe_staff_uid(staff_user_id)
    order_ref = str(row.get("orderId") if row.get("orderId") is not None else row.get("order_id") or "")

    if order_type in ("2", "3"):
        order_pk = _resolve_experiment_order_pk(order_ref)
        if order_pk:
            execute(
                "UPDATE experiment_order SET is_upload_receipt = 2 WHERE id = %(id)s",
                {"id": order_pk},
            )
            try:
                _fill_receive_bills_for_payment(
                    order_id=order_pk,
                    money=money,
                    staff_user_id=staff,
                )
            except Exception:
                logger.exception("fill receive bills failed apply=%s", apply_id)
                insert_receive_bill(
                    order_id=order_pk,
                    money=money,
                    user_id=staff or 0,
                    log_info="同意付款申请",
                )
        pay_type = 3
        pay_way = 3
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
        pay_way = 3
    elif order_type == "4":
        pay_type = 4
        pay_way = 4  # 对齐 Java 提现 pay_way=4
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
             %(pay_type)s, %(pay_way)s, %(pa_num)s, %(pa_id)s)
        """,
        {
            "uid": user_id,
            "money": float(money),
            "order_id": order_ref,
            "pay_type": pay_type,
            "pay_way": pay_way,
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
        {"pid": apply_id, "uid": str(staff_user_id or "") or None},
    )
    logger.info("agree payment apply=%s pay_log=%s", apply_id, pay_log_id)
    return True, "确认付款成功"


@transaction.atomic
def refuse_payment(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_payment_application(apply_id)
    if not row:
        return False, "付款申请不存在"
    apply_status = row.get("applyStatus")
    if apply_status is None:
        apply_status = row.get("apply_status")
    if str(apply_status) != "1":
        return False, "仅待审核申请可操作"

    order_type = str(row.get("orderType") if row.get("orderType") is not None else row.get("order_type") or "")
    if order_type in ("2", "3"):
        order_ref = str(row.get("orderId") if row.get("orderId") is not None else row.get("order_id") or "")
        order_pk = _resolve_experiment_order_pk(order_ref)
        if order_pk:
            execute(
                "UPDATE experiment_order SET is_upload_receipt = 3 WHERE id = %(id)s",
                {"id": order_pk},
            )
    elif order_type == "4":
        money = Decimal(str(row.get("money") or 0))
        uid_raw = row.get("userId") if row.get("userId") is not None else row.get("user_id")
        ua_repo.get_or_create(int(uid_raw))
        execute(
            """
            UPDATE user_account
            SET amount = COALESCE(amount, 0) + %(m)s, update_time = NOW()
            WHERE delete_status = 0 AND user_id = %(uid)s
            """,
            {"m": float(money), "uid": int(uid_raw)},
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
        {"pid": apply_id, "uid": str(staff_user_id or "") or None},
    )
    return True, "拒绝付款成功"


@transaction.atomic
def agree_retest(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_retest_application(apply_id)
    if not row:
        return False, "复测申请不存在"
    try:
        st = int(row.get("applyStatus") if row.get("applyStatus") is not None else -1)
    except (TypeError, ValueError):
        st = -1
    if st != 0:
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
            SELECT id, order_status AS orderStatus
            FROM experiment_order_child
            WHERE id = %(id)s LIMIT 1
            """,
            {"id": int(child_id)},
        )
        if child:
            status = int(child.get("orderStatus") or 0)
            # Java: YPGH(41)->YPDH(36)；CSWC(39)->YPLY(37)
            if status == ST_RETURN:
                new_status = ST_ARRIVE
            elif status == ST_TEST_DONE:
                new_status = ST_PICK
            else:
                new_status = status
            execute(
                """
                UPDATE experiment_order_child
                SET fcsq = 0, order_status = %(status)s
                WHERE id = %(id)s
                """,
                {"id": int(child_id), "status": new_status},
            )
            try:
                parent_links = fetch_all(
                    """
                    SELECT DISTINCT poc.purchase_order_id AS oid
                    FROM exp_qd_purchase_order_child poc
                    WHERE poc.order_child_id = %(cid)s
                    """,
                    {"cid": int(child_id)},
                )
                for link in parent_links:
                    oid = link.get("oid")
                    if not oid:
                        continue
                    execute(
                        """
                        UPDATE experiment_order
                        SET order_status = CASE
                            WHEN IFNULL(order_status, 0) > 35 THEN 35
                            ELSE order_status
                        END
                        WHERE id = %(id)s AND order_type IN ('9', '10')
                        """,
                        {"id": int(oid)},
                    )
            except Exception:
                logger.exception("agree_retest parent status update failed child=%s", child_id)

    execute_insert(
        """
        INSERT INTO retest_application_log
            (retest_application_id, content, user_id, addTime, deleteStatus)
        VALUES (%(aid)s, '同意复测申请', %(uid)s, NOW(), 0)
        """,
        {"aid": apply_id, "uid": str(staff_user_id or "") or None},
    )
    return True, "同意复测成功"


@transaction.atomic
def refuse_retest(*, apply_id: int, staff_user_id: str, mark: str = "") -> tuple[bool, str]:
    row = billing_repo.get_retest_application(apply_id)
    if not row:
        return False, "复测申请不存在"
    try:
        st = int(row.get("applyStatus") if row.get("applyStatus") is not None else -1)
    except (TypeError, ValueError):
        st = -1
    if st != 0:
        return False, "仅待审核申请可操作"

    execute(
        """
        UPDATE retest_application
        SET applyStatus = 2, remeasurement_require = %(mark)s
        WHERE id = %(id)s
        """,
        {"id": apply_id, "mark": mark or ""},
    )
    child_id = str(row.get("orderId") or "")
    if child_id.isdigit():
        execute(
            "UPDATE experiment_order_child SET fcsq = 0 WHERE id = %(id)s",
            {"id": int(child_id)},
        )
    execute_insert(
        """
        INSERT INTO retest_application_log
            (retest_application_id, content, user_id, addTime, deleteStatus)
        VALUES (%(aid)s, '复测申请驳回', %(uid)s, NOW(), 0)
        """,
        {"aid": apply_id, "uid": str(staff_user_id or "") or None},
    )
    return True, "拒绝复测成功"
