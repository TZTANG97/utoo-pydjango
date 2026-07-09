from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from apps.auth_pc.services.customer import CustomerUserService
from apps.core.services.sysconfig import get_config_row
from apps.invoices.services.finance import (
    exp_receive_sum_pc,
    get_all_money_dkp,
    us_exchange_rate,
)
from apps.payments.repositories import integral as integral_repo
from apps.payments.repositories import user_account as user_account_repo
from qd_common.serialize import to_jsonable


class AssetService:
    @staticmethod
    def get_or_create_account(user_id: int) -> dict[str, Any]:
        return user_account_repo.get_or_create(user_id)

    @staticmethod
    def _get_or_create_account(user_id: int) -> dict[str, Any]:
        return AssetService.get_or_create_account(user_id)

    @staticmethod
    def get_account(user_id: int) -> dict[str, Any]:
        user = CustomerUserService.get_by_id(user_id)
        mobile = (user.mobile or "") if user else ""
        account = user_account_repo.get_or_create(user_id)
        rate = us_exchange_rate()

        rmb_arrear = exp_receive_sum_pc(
            user_id=user_id, mobile=mobile, currency_type=1
        )
        us_arrear = exp_receive_sum_pc(
            user_id=user_id, mobile=mobile, currency_type=2
        )
        arrear = rmb_arrear + us_arrear * rate

        dkp_rmb = get_all_money_dkp(
            user_id=user_id, mobile=mobile, currency_type=1
        )
        dkp_us = get_all_money_dkp(
            user_id=user_id, mobile=mobile, currency_type=2
        )
        invoicing = dkp_rmb + dkp_us * rate

        raw_amount = float(account.get("amount") or 0)
        # amount：账户充值余额，与 Java amountPay.ajax 扣款口径一致（读 user_account.amount）
        # arrearAmount：历史订单待付汇总，用于展示欠款，不从 amount 中扣减
        # netBalance：净头寸 = 余额 - 待支付（可为负，仅作参考）
        net_balance = raw_amount - arrear
        account["accountBalance"] = to_jsonable(raw_amount)
        account["arrearAmount"] = to_jsonable(arrear)
        account["invoicingAmount"] = to_jsonable(invoicing)
        account["availableAmount"] = to_jsonable(raw_amount)
        account["netBalance"] = to_jsonable(net_balance)
        account["amount"] = to_jsonable(raw_amount)
        return account

    @staticmethod
    def get_integral_summary(user_id: int) -> dict[str, Any]:
        user = CustomerUserService.get_by_id(user_id)
        if not user:
            return {"totalIntegral": 0.0, "expireIntegral": 0.0, "expireDate": ""}
        mobile = user.mobile or ""
        config = get_config_row()
        expire_days = config.get("expire_integral_day") if config else None
        start = None
        end = None
        if expire_days and int(expire_days) > 0:
            start = datetime.now() - timedelta(days=int(expire_days))
            end = datetime.now()
        total = integral_repo.sum_integral(
            user_id=user_id, mobile=mobile, start=start, end=None
        )
        expire_total = integral_repo.sum_integral(
            user_id=user_id, mobile=mobile, start=start, end=end
        )
        expire_date = datetime.now().strftime("%Y-%m-%d") if expire_days else ""
        return {
            "totalIntegral": float(total),
            "expireIntegral": float(expire_total),
            "expireDate": expire_date,
        }

    @staticmethod
    def append_account_log(user_id: int, money: Decimal, *, of_id: int | None = None) -> None:
        user_account_repo.insert_account_log(user_id, money, of_id=of_id)

    @staticmethod
    def apply_recharge_credit(user_id: int, money: Decimal, pay_log_id: int) -> None:
        user_account_repo.get_or_create(user_id)
        user_account_repo.add_recharge_credit(user_id, money)
        user_account_repo.insert_account_log(user_id, money, of_id=pay_log_id)
