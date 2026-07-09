from apps.auth_support.services.customer import CustomerUserService
from apps.core.db_utils import fetch_one
from apps.invoices.services.finance import get_all_money_dkp


def _us_exchange_rate() -> float:
    try:
        row = fetch_one("SELECT us_exchange_rate FROM account_setting LIMIT 1")
        if row and row.get("us_exchange_rate") is not None:
            return float(row["us_exchange_rate"])
    except Exception:
        pass
    return 1.0


def stay_apply_money(user_id: int) -> float:
    user = CustomerUserService.get_by_id(user_id)
    mobile = (user.mobile or "") if user else ""
    rate = _us_exchange_rate()
    rmb = get_all_money_dkp(user_id=user_id, mobile=mobile, currency_type=1)
    usd = get_all_money_dkp(user_id=user_id, mobile=mobile, currency_type=2)
    return float(rmb or 0) + float(usd or 0) * rate
