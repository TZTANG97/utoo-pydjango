from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction

from apps.core import redis_client
from apps.payments.repositories import integral_log as integral_log_repo
from apps.payments.repositories import order_lookup as order_repo
from apps.payments.repositories import pay_info as pay_repo
from apps.payments.services.asset import AssetService
from apps.payments.services.balance_pay import BalancePayService
from apps.payments.services.pay_locks import (
    lock_pay_info_log_for_update,
    lock_user_account_for_update,
    pay_notify_redis_lock,
)

logger = logging.getLogger(__name__)


def handle_recharge_notify(resource: dict) -> None:
    out_trade_no = resource.get("out_trade_no") or ""
    if not out_trade_no:
        return

    with pay_notify_redis_lock(out_trade_no):
        transaction_id = resource.get("transaction_id") or ""
        total = int((resource.get("amount") or {}).get("total") or 0)
        money = Decimal(total) / Decimal("100")

        epo = pay_repo.find_pay_order_by_out_trade_no(out_trade_no)
        if not epo:
            return

        try:
            with transaction.atomic():
                pi = lock_pay_info_log_for_update(int(epo["order_id"]))
                if not pi or int(pi.get("pay_type") or 0) != 1:
                    return
                status = int(pi.get("status") or 0)
                if status in (2, 3):
                    return

                pay_repo.update_pay_order_transaction(int(epo["id"]), transaction_id)
                uid = int(pi["user_id"])
                lock_user_account_for_update(uid)
                AssetService.apply_recharge_credit(uid, money, int(pi["id"]))
                if not pay_repo.mark_pay_info_paid_if_pending(int(pi["id"])):
                    raise RuntimeError("recharge mark paid race")
                pay_repo.save_exp_user_log(uid, f"(充值方式:微信)充值成功，金额{money}")
                redis_client.set_string(out_trade_no, "true", ex=900)
        except Exception as exc:
            logger.exception("handle_recharge_notify failed: %s", exc)


def handle_single_order_pay_notify(resource: dict) -> None:
    out_trade_no = resource.get("out_trade_no") or ""
    if not out_trade_no:
        return

    with pay_notify_redis_lock(out_trade_no):
        transaction_id = resource.get("transaction_id") or ""
        total = int((resource.get("amount") or {}).get("total") or 0)
        wx_money = Decimal(total) / Decimal("100")

        epo = pay_repo.find_pay_order_by_out_trade_no(out_trade_no)
        if not epo:
            return

        try:
            with transaction.atomic():
                pi = lock_pay_info_log_for_update(int(epo["order_id"]))
                if not pi:
                    return
                status = int(pi.get("status") or 0)
                if status == 2:
                    return
                if status == 3:
                    return

                pay_repo.update_pay_order_transaction(int(epo["id"]), transaction_id)
                uid = int(pi["user_id"])
                jfdh = Decimal(str(pi.get("integral_money") or 0))
                jf = Decimal(str(pi.get("use_integral") or 0))
                pay_type = int(pi.get("pay_type") or 0)
                log_info = "线上支付-微信支付"

                if pay_type == 3:
                    of_id = int(str(pi.get("order_id") or "0"))
                    order = order_repo.get_sale_order_for_user(
                        order_id=of_id, user_id=uid, mobile=""
                    )
                    if order:
                        money = wx_money + jfdh
                        BalancePayService.insert_receive_bill(
                            order_id=of_id,
                            money=money,
                            user_id=uid,
                            log_info=log_info,
                        )
                        integral_log_repo.deduct_integral_for_order(order, jf)
                        pay_repo.save_exp_user_log(
                            uid,
                            f"(支付方式:微信)支付成功，关联单号{order.get('order_id')}",
                        )
                elif pay_type == 2:
                    ids = [
                        x.strip()
                        for x in str(pi.get("order_id") or "").split(",")
                        if x.strip()
                    ]
                    fkjes = [
                        x.strip()
                        for x in str(pi.get("fkjes") or "").split(",")
                        if x.strip()
                    ]
                    for i, sid in enumerate(ids):
                        try:
                            oid = int(sid)
                        except ValueError:
                            continue
                        order = order_repo.get_sale_order_for_user(
                            order_id=oid, user_id=uid, mobile=""
                        )
                        if not order:
                            continue
                        part = Decimal(fkjes[i]) if i < len(fkjes) else wx_money
                        BalancePayService.insert_receive_bill(
                            order_id=oid,
                            money=part,
                            user_id=uid,
                            log_info=log_info,
                        )
                        if jf > 0 and ids:
                            share = (jf / Decimal(len(ids))).quantize(Decimal("0.01"))
                            integral_log_repo.deduct_integral_for_order(order, share)
                        pay_repo.save_exp_user_log(
                            uid,
                            f"（支付方式：微信）支付成功，关联单号{order.get('order_id')}",
                        )

                if not pay_repo.mark_pay_info_paid_if_pending(int(pi["id"])):
                    raise RuntimeError("order pay mark paid race")
                redis_client.set_string(out_trade_no, "true", ex=900)
        except Exception as exc:
            logger.exception("handle_single_order_pay_notify failed: %s", exc)
