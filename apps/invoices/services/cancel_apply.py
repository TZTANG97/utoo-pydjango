import logging

from django.db import transaction

from apps.core.db_utils import execute, fetch_one

logger = logging.getLogger(__name__)


@transaction.atomic
def cancel_invoice_apply(*, user_id: int, invoice_id: int) -> tuple[bool, str]:
    row = fetch_one(
        """
        SELECT id, user_id, status, order_ids
        FROM invoice_apply_log
        WHERE id = %(iid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"iid": invoice_id},
    )
    if not row:
        return False, "发票申请信息不存在"
    if int(row["user_id"]) != int(user_id):
        return False, "取消失败，发票信息不是您的发票"
    if int(row.get("status") or 0) != 1:
        return False, "取消失败，此发票信息不是开票中状态"

    order_ids = (row.get("order_ids") or "").strip()
    if not order_ids:
        return False, "关联订单为空"

    try:
        execute(
            "UPDATE invoice_apply_log SET status = 3 WHERE id = %(iid)s",
            {"iid": invoice_id},
        )
        for ofid in order_ids.split(","):
            ofid = ofid.strip()
            if not ofid:
                continue
            of_row = fetch_one(
                """
                SELECT id, order_id, is_online FROM experiment_order
                WHERE id = %(oid)s LIMIT 1
                """,
                {"oid": int(ofid)},
            )
            if not of_row:
                continue
            if int(of_row.get("is_online") or 0) == 0:
                execute(
                    "UPDATE experiment_order SET is_apply = 0 WHERE id = %(oid)s",
                    {"oid": int(ofid)},
                )
            if int(of_row.get("is_online") or 0) == 1:
                execute(
                    """
                    UPDATE qd_bill SET is_apply = 0
                    WHERE exp_of_id = %(oid)s AND type = 2
                    """,
                    {"oid": int(ofid)},
                )
            execute(
                """
                INSERT INTO exp_user_log (addTime, deleteStatus, user_id, info)
                VALUES (NOW(), 0, %(uid)s, %(info)s)
                """,
                {
                    "uid": user_id,
                    "info": f"开票申请单已取消，关联单号{of_row.get('order_id')}",
                },
            )
        return True, "取消成功!"
    except Exception as exc:
        logger.exception("cancel_invoice_apply failed: %s", exc)
        return False, f"取消失败：{exc}"
