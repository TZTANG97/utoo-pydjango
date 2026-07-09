from django.db import transaction

from apps.orders.repositories import actions as actions_repo
from apps.orders.repositories import orders as repo
from apps.payments.repositories.exp_user_log import save_exp_user_log


@transaction.atomic
def confirm_child_complete(*, user_id: int, child_id: int) -> tuple[bool, str]:
    if child_id <= 0:
        return False, "参数错误"
    _, mobile = repo.user_context(user_id)
    row = actions_repo.fetch_child_confirm_row(
        child_id=child_id, user_id=user_id, mobile=mobile
    )
    if not row:
        return False, "无权操作或子订单不存在"

    actions_repo.mark_child_sure(child_id)
    po_id = int(row["purchase_order_id"])
    order_no = row.get("order_id") or ""
    actions_repo.insert_order_log(
        of_id=po_id,
        log_info=f"用户确认子订单{order_no}测试完成",
    )
    return True, "确认成功！"


@transaction.atomic
def write_evaluate(
    *, user_id: int, order_id: int, star: int, content: str
) -> tuple[bool, str]:
    if order_id <= 0:
        return False, "参数错误"
    _, mobile = repo.user_context(user_id)
    of = repo.get_sale_order_for_user(
        order_id=order_id, user_id=user_id, mobile=mobile
    )
    if not of:
        return False, "订单不存在或无权评价"
    if int(of.get("order_status") or 0) != 50:
        return False, "订单未完成，暂不可评价"

    actions_repo.update_order_evaluate(
        order_id=order_id, star=star, content=content
    )
    try:
        save_exp_user_log(user_id, f"完成评价，评价内容{content or ''}")
    except Exception:
        pass
    return True, "评价成功"
