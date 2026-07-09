from apps.core.db_utils import scalar


def has_online_receive_bill(order_id: int) -> bool:
    try:
        count = int(
            scalar(
                """
                SELECT COUNT(1) FROM exp_online_qd_bill
                WHERE exp_of_id = %(oid)s AND type = 2
                """,
                {"oid": order_id},
                0,
            )
            or 0
        )
        return count > 0
    except Exception:
        return False
