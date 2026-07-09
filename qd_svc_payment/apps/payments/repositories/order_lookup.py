"""支付域所需的最小订单查询（微服务内不依赖 orders app）。"""
from typing import Any

from apps.auth_support.services.customer import CustomerUserService
from apps.core.db_utils import fetch_one, scalar


def user_context(user_id: int) -> tuple[int, str]:
    user = CustomerUserService.get_by_id(user_id)
    return user_id, (user.mobile or "") if user else ""


def get_sale_order_for_user(
    *, order_id: int, user_id: int, mobile: str
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT t.* FROM experiment_order t
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        WHERE t.id = %(oid)s
          AND (t.order_type IN ('6', '8') OR CAST(t.order_type AS UNSIGNED) IN (6, 8))
          AND (
            t.custom_user_id = %(user_id)s
            OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR t.mobile = %(mobile)s
          )
        LIMIT 1
        """,
        {
            "oid": order_id,
            "user_id": user_id,
            "user_id_str": str(user_id),
            "mobile": mobile,
        },
    )


def sum_bill(order_id: int, bill_type: int) -> float:
    return float(
        scalar(
            """
            SELECT COALESCE(SUM(money), 0) FROM qd_bill
            WHERE exp_of_id = %(oid)s AND type = %(tp)s
            """,
            {"oid": order_id, "tp": bill_type},
            0,
        )
        or 0
    )
