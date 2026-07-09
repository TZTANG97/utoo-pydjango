from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.core.services.sysconfig import get_config_row, integral_convert_ratio
from apps.payments.repositories import order_lookup as order_repo
from apps.payments.repositories import qd_bill as qd_bill_repo
from apps.payments.repositories import user_account as user_account_repo
from apps.payments.services.pay_locks import lock_user_account_for_update, user_pay_redis_lock

logger = logging.getLogger(__name__)


class BalancePayService:
    @staticmethod
    def _parse_integral(use_integral: str) -> Decimal:
        try:
            return Decimal(str(use_integral or "0").strip() or "0")
        except Exception:
            return Decimal("0")

    @staticmethod
    def _order_payable(order: dict[str, Any]) -> Decimal:
        total = Decimal(str(order.get("totalPrice") or order.get("total_price") or 0))
        paid = Decimal(str(order_repo.sum_bill(int(order["id"]), 2)))
        return max(total - paid, Decimal("0"))

    @staticmethod
    def insert_receive_bill(
        *, order_id: int, money: Decimal, user_id: int, log_info: str
    ) -> None:
        qd_bill_repo.insert_receive_bill(
            order_id=order_id,
            money=money,
            user_id=user_id,
            log_info=log_info,
        )

    @staticmethod
    def _deduct_balance(user_id: int, amount: Decimal) -> None:
        if user_account_repo.deduct_balance(user_id, amount) < 1:
            raise ValueError("余额不足或扣款失败")
        user_account_repo.insert_account_log(user_id, -amount)

    @classmethod
    def pay_orders(
        cls,
        *,
        user_id: int,
        of_ids: str,
        use_integral: str = "0",
        pay_way: str = "",
    ) -> tuple[bool, str, dict[str, Any] | None]:
        del pay_way
        raw = (of_ids or "").strip()
        if not raw:
            return False, "参数为空!", None

        uid, mobile = order_repo.user_context(user_id)
        id_list = [x.strip() for x in raw.split(",") if x.strip()]
        if not id_list:
            return False, "参数为空!", None

        pay_items: list[tuple[int, Decimal]] = []
        total_due = Decimal("0")

        for sid in id_list:
            try:
                oid = int(sid)
            except ValueError:
                return False, f"无效订单 id: {sid}", None
            order = order_repo.get_sale_order_for_user(
                order_id=oid, user_id=uid, mobile=mobile
            )
            if not order:
                return False, "订单不存在或无权操作", None
            due = cls._order_payable(order)
            if due <= 0:
                return False, f"订单 {order.get('order_id') or oid} 无需支付", None
            pay_items.append((oid, due))
            total_due += due

        cfg = get_config_row()
        ratio = Decimal(str(integral_convert_ratio(cfg)))
        integral_pts = cls._parse_integral(use_integral)
        integral_money = (integral_pts / Decimal("100") * ratio).quantize(Decimal("0.01"))
        pay_amount = max((total_due - integral_money).quantize(Decimal("0.01")), Decimal("0"))

        with user_pay_redis_lock(uid) as acquired:
            if not acquired:
                return False, "支付处理中，请稍后再试", None
            try:
                with transaction.atomic():
                    account_row = lock_user_account_for_update(uid)
                    balance = Decimal(str(account_row.get("amount") or 0))
                    if balance < pay_amount:
                        return False, "余额不足", None
                    for oid, due in pay_items:
                        cls.insert_receive_bill(
                            order_id=oid,
                            money=due,
                            user_id=uid,
                            log_info="线上支付-余额支付",
                        )
                    if pay_amount > 0:
                        cls._deduct_balance(uid, pay_amount)
            except Exception as exc:
                logger.exception("balance pay failed: %s", exc)
                return False, f"支付失败：{exc}", None

        return True, "支付成功!", {"paid": float(pay_amount), "orders": len(pay_items)}
