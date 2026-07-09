from datetime import datetime, timedelta
from typing import Any

from apps.auth_support.services.customer import CustomerUserService
from apps.core.services.sysconfig import get_config_row
from apps.payments.repositories import integral_log as integral_log_repo


def get_integral_list_page(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    log_type: str = "",
) -> dict[str, Any]:
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    draw_n = int(draw) if draw.isdigit() else 1

    user = CustomerUserService.get_by_id(user_id)
    mobile = (user.mobile or "") if user else ""
    config = get_config_row()
    expire_days = config.get("expire_integral_day") if config else None
    start_time = None
    if expire_days and int(expire_days) > 0:
        start_time = datetime.now() - timedelta(days=int(expire_days))

    try:
        total = integral_log_repo.count_union_logs(
            user_id=user_id,
            mobile=mobile,
            log_type=log_type,
            start_time=start_time,
        )
        rows = integral_log_repo.list_union_logs(
            user_id=user_id,
            mobile=mobile,
            offset=offset,
            limit=limit,
            log_type=log_type,
            start_time=start_time,
        )
        integral_log_repo.enrich_redeem_order_nums(rows)
        return {
            "data": rows,
            "draw": draw_n,
            "recordsTotal": total,
            "recordsFiltered": total,
        }
    except Exception:
        return {
            "data": [],
            "draw": draw_n,
            "recordsTotal": 0,
            "recordsFiltered": 0,
        }
