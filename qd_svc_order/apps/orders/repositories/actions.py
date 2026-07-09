from typing import Any

from apps.core.db_utils import execute, fetch_one


def fetch_child_confirm_row(
    *, child_id: int, user_id: int, mobile: str
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT eoc.id, eoc.order_id, poc.purchase_order_id
        FROM experiment_order_child eoc
        JOIN exp_qd_purchase_order_child poc ON poc.order_child_id = eoc.id
        JOIN experiment_order po ON poc.purchase_order_id = po.id
        JOIN experiment_order parent ON po.parent_id = parent.id
        LEFT JOIN qd_user_company quc ON parent.customer_name = quc.id
        WHERE eoc.id = %(cid)s
          AND (
            parent.custom_user_id = %(user_id)s
            OR CAST(parent.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR parent.mobile = %(mobile)s
          )
        LIMIT 1
        """,
        {
            "cid": child_id,
            "user_id": user_id,
            "user_id_str": str(user_id),
            "mobile": mobile,
        },
    )


def mark_child_sure(child_id: int) -> None:
    execute(
        "UPDATE experiment_order_child SET is_sure = 1 WHERE id = %(cid)s",
        {"cid": child_id},
    )


def insert_order_log(*, of_id: int, log_info: str) -> None:
    execute(
        """
        INSERT INTO experiment_order_log (addTime, deleteStatus, log_info, of_id)
        VALUES (NOW(), 0, %(info)s, %(of_id)s)
        """,
        {"info": log_info, "of_id": of_id},
    )


def update_order_evaluate(*, order_id: int, star: int, content: str) -> None:
    execute(
        """
        UPDATE experiment_order
        SET star = %(star)s, content = %(content)s, is_evaluate = 1
        WHERE id = %(oid)s
        """,
        {"star": star, "content": content or "", "oid": order_id},
    )
