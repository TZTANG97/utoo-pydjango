from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.db import transaction

from apps.core.services.sysconfig import get_config_row, integral_convert_ratio
from apps.payments.repositories import order_lookup as order_repo
from apps.payments.repositories import pay_info as pay_repo
from apps.payments.services.wx_native_client import native_prepay
from apps.payments.services.wx_settings import wx_pay_configured, wx_pay_not_configured_message

logger = logging.getLogger(__name__)


class WechatPrepayService:
    @staticmethod
    def not_configured() -> tuple[bool, str]:
        if wx_pay_configured():
            return True, ""
        return False, wx_pay_not_configured_message()

    @staticmethod
    def _calc_integral_deduction(use_integral: str) -> Decimal:
        cfg = get_config_row()
        ratio = Decimal(str(integral_convert_ratio(cfg)))
        try:
            pts = Decimal(str(use_integral or "0").strip() or "0")
        except Exception:
            pts = Decimal("0")
        return (pts / Decimal("100") * ratio).quantize(Decimal("0.01"))

    @classmethod
    def pre_pay(
        cls, *, user_id: int, of_id: str, use_integral: str = "0"
    ) -> tuple[bool, str, dict[str, Any] | None]:
        ok_cfg, msg = cls.not_configured()
        if not ok_cfg:
            return False, msg, None

        uid, mobile = order_repo.user_context(user_id)
        try:
            oid = int(of_id)
        except ValueError:
            return False, "参数错误", None

        order = order_repo.get_sale_order_for_user(order_id=oid, user_id=uid, mobile=mobile)
        if not order:
            return False, "订单不存在或无权操作", None

        total = Decimal(str(order.get("totalPrice") or 0))
        paid = Decimal(str(order_repo.sum_bill(oid, 2)))
        money = (total - paid - cls._calc_integral_deduction(use_integral)).quantize(
            Decimal("0.01")
        )
        if money <= 0:
            return False, "无需支付", None

        try:
            with transaction.atomic():
                log_id = pay_repo.create_pay_info_log(
                    user_id=uid,
                    money=money,
                    pay_type=3,
                    order_id=str(oid),
                    use_integral=Decimal(str(use_integral or "0")),
                    integral_money=cls._calc_integral_deduction(use_integral),
                )
                out_no = pay_repo.new_out_trade_no(log_id, gen_type=1)
        except Exception as exc:
            logger.exception("pre_pay save log failed: %s", exc)
            return False, f"创建支付单失败：{exc}", None

        ok, err, data = native_prepay(
            callback_path="/pc/pay.ajax",
            description="愉兔检测实验订单",
            out_trade_no=out_no,
            total_fen=int(money * 100),
        )
        return (True, "ok", data) if ok else (False, err, None)

    @classmethod
    def recharge_pre_pay(cls, *, user_id: int, money: str) -> tuple[bool, str, dict[str, Any] | None]:
        ok_cfg, msg = cls.not_configured()
        if not ok_cfg:
            return False, msg, None
        try:
            amount = Decimal(str(money or "0").strip())
        except Exception:
            return False, "金额无效", None
        if amount <= 0:
            return False, "金额无效", None

        try:
            with transaction.atomic():
                log_id = pay_repo.create_pay_info_log(
                    user_id=user_id, money=amount, pay_type=1
                )
                out_no = pay_repo.new_out_trade_no(log_id, gen_type=2)
        except Exception as exc:
            logger.exception("recharge_pre_pay failed: %s", exc)
            return False, f"创建充值单失败：{exc}", None

        ok, err, data = native_prepay(
            callback_path="/pc/rechargePay.ajax",
            description="愉兔检测充值",
            out_trade_no=out_no,
            total_fen=int(amount * 100),
        )
        if not ok:
            return False, err, None
        pay_repo.cache_pay_native_payload(log_id, data)
        pi_row = pay_repo.get_pay_info_log(log_id)
        if pi_row:
            ca = pay_repo.pay_log_close_at(pi_row.get("addTime"))
            if ca:
                data["closeAt"] = ca.strftime("%Y-%m-%d %H:%M:%S")
                data["remainingSeconds"] = pay_repo.pay_log_remaining_seconds(
                    pi_row.get("addTime")
                )
        data["payLogId"] = log_id
        return True, "ok", data

    @classmethod
    def continue_recharge_pay(
        cls, *, user_id: int, pay_log_id: int
    ) -> tuple[bool, str, dict[str, Any] | None]:
        ok_cfg, msg = cls.not_configured()
        if not ok_cfg:
            return False, msg, None
        pi = pay_repo.get_pay_info_log(pay_log_id)
        if not pi or int(pi.get("user_id") or 0) != int(user_id):
            return False, "记录不存在或无权操作", None
        if int(pi.get("status") or 0) != 1:
            return False, "该订单不可继续支付", None
        rem = pay_repo.pay_log_remaining_seconds(pi.get("addTime"))
        if rem <= 0:
            return False, "订单已超时关闭，请重新发起充值", None
        if int(pi.get("pay_way") or 0) != 2:
            return False, "仅支持微信支付的待支付单", None

        cached = pay_repo.get_cached_pay_native_payload(pay_log_id)
        if cached and cached.get("codeUrl"):
            cached["payLogId"] = pay_log_id
            cached["remainingSeconds"] = rem
            ca = pay_repo.pay_log_close_at(pi.get("addTime"))
            if ca:
                cached["closeAt"] = ca.strftime("%Y-%m-%d %H:%M:%S")
            return True, "ok", cached

        amount = Decimal(str(pi.get("money") or 0))
        out_no = pay_repo.get_out_trade_no_for_pay_log(pay_log_id) or pay_repo.refresh_out_trade_no(
            pay_log_id, gen_type=2
        )
        ok, err, data = native_prepay(
            callback_path="/pc/rechargePay.ajax",
            description="愉兔检测充值",
            out_trade_no=out_no,
            total_fen=int(amount * 100),
        )
        if not ok:
            out_no = pay_repo.refresh_out_trade_no(pay_log_id, gen_type=2)
            ok, err, data = native_prepay(
                callback_path="/pc/rechargePay.ajax",
                description="愉兔检测充值",
                out_trade_no=out_no,
                total_fen=int(amount * 100),
            )
        if not ok:
            return False, err or "获取支付二维码失败", None
        pay_repo.cache_pay_native_payload(pay_log_id, data)
        data["payLogId"] = pay_log_id
        data["remainingSeconds"] = rem
        ca = pay_repo.pay_log_close_at(pi.get("addTime"))
        if ca:
            data["closeAt"] = ca.strftime("%Y-%m-%d %H:%M:%S")
        return True, "ok", data

    @classmethod
    def pre_amount_pay(
        cls, *, user_id: int, of_id: str, use_integral: str = "0"
    ) -> tuple[bool, str, dict[str, Any] | None]:
        ok_cfg, msg = cls.not_configured()
        if not ok_cfg:
            return False, msg, None

        uid, mobile = order_repo.user_context(user_id)
        raw = (of_id or "").strip()
        if not raw:
            return False, "参数为空!", None

        total_price = Decimal("0")
        fkjes_parts: list[str] = []
        for sid in raw.split(","):
            sid = sid.strip()
            if not sid:
                continue
            try:
                oid = int(sid)
            except ValueError:
                return False, f"无效订单 id: {sid}", None
            order = order_repo.get_sale_order_for_user(
                order_id=oid, user_id=uid, mobile=mobile
            )
            if not order:
                return False, "订单不存在或无权操作", None
            total = Decimal(str(order.get("totalPrice") or 0))
            sk = Decimal(str(order_repo.sum_bill(oid, 2)))
            due = (total - sk).quantize(Decimal("0.01"))
            fkjes_parts.append(str(due))
            total_price += due

        jfdh = cls._calc_integral_deduction(use_integral)
        total_price = (total_price - jfdh).quantize(Decimal("0.01"))
        if total_price <= 0:
            return False, "无需支付", None

        try:
            with transaction.atomic():
                log_id = pay_repo.create_pay_info_log(
                    user_id=uid,
                    money=total_price,
                    pay_type=2,
                    order_id=raw,
                    use_integral=Decimal(str(use_integral or "0")),
                    integral_money=jfdh,
                    fkjes=",".join(fkjes_parts),
                )
                out_no = pay_repo.new_out_trade_no(log_id, gen_type=3)
        except Exception as exc:
            logger.exception("pre_amount_pay failed: %s", exc)
            return False, f"创建支付单失败：{exc}", None

        ok, err, data = native_prepay(
            callback_path="/pc/amountPayBack.ajax",
            description="愉兔检测实验订单还款",
            out_trade_no=out_no,
            total_fen=int(total_price * 100),
        )
        return (True, "ok", data) if ok else (False, err, None)
