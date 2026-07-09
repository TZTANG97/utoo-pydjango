from datetime import datetime, timedelta
from typing import Any

from apps.auth_support.services.customer import CustomerUserService
from apps.core.services.sysconfig import get_config_row
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
        account = user_account_repo.get_or_create(user_id)
        raw_amount = float(account.get("amount") or 0)
        account["accountBalance"] = to_jsonable(raw_amount)
        account["arrearAmount"] = to_jsonable(0)
        account["invoicingAmount"] = to_jsonable(0)
        account["availableAmount"] = to_jsonable(max(raw_amount, 0))
        account["amount"] = account["availableAmount"]
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
