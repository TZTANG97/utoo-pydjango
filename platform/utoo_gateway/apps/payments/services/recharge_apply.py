from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.payments.repositories import payment_application as pa_repo
from apps.payments.repositories.pay_info import save_exp_user_log


@transaction.atomic
def add_recharge(
    *, user_id: int, money: str, file_id: str = "", pay_way: str = "3"
) -> tuple[bool, str]:
    try:
        amount = Decimal(str(money).strip())
    except (InvalidOperation, ValueError):
        return False, "金额无效"
    if amount <= 0:
        return False, "金额必须大于0"

    pa_num = pa_repo.generate_pa_num()
    pa_id = pa_repo.insert_application(
        user_id=user_id,
        amount=amount,
        pay_way=int(pay_way or 3),
        pa_num=pa_num,
    )
    if file_id:
        pa_repo.link_accessories(pa_id=pa_id, file_ids=file_id)
    pa_repo.insert_submitted_log(pa_id=pa_id, user_id=user_id)
    save_exp_user_log(user_id, f"充值成功,金额为{amount}")
    return True, "审核已提交!"
