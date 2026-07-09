from apps.core.db_utils import execute, fetch_one


def get_child_order(child_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT id FROM experiment_order_child
        WHERE id = %(cid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"cid": child_id},
    )


def get_pending_retest(*, user_id: int, order_id: str) -> dict | None:
    return fetch_one(
        """
        SELECT id FROM retest_application
        WHERE userId = %(uid)s AND orderId = %(oid)s AND applyStatus = 0
        LIMIT 1
        """,
        {"uid": str(user_id), "oid": str(order_id)},
    )


def get_latest_fc_order_id(like_prefix: str) -> dict | None:
    return fetch_one(
        """
        SELECT order_id FROM retest_application
        WHERE order_id LIKE %(like)s
        ORDER BY order_id DESC
        LIMIT 1
        """,
        {"like": like_prefix},
    )


def insert_retest_application(
    *,
    user_id: int,
    order_id: str,
    mark: str,
    remeasurement_require: str,
    fc_no: str,
) -> None:
    execute(
        """
        INSERT INTO retest_application (
            addTime, deleteStatus, userId, applyStatus, mark,
            orderId, remeasurement_require, order_id
        ) VALUES (
            NOW(), 0, %(user_id)s, 0, %(mark)s,
            %(order_id)s, %(remeasurement_require)s, %(fc_no)s
        )
        """,
        {
            "user_id": str(user_id),
            "mark": mark,
            "order_id": str(order_id),
            "remeasurement_require": remeasurement_require,
            "fc_no": fc_no,
        },
    )
