from typing import Any

from apps.core.db_utils import fetch_all, fetch_one
from qd_common.serialize import to_jsonable


def get_online_parent_order(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, is_online, custom_user_id FROM experiment_order
        WHERE id = %(oid)s LIMIT 1
        """,
        {"oid": order_id},
    )


def list_eligible_children(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, order_id AS orderId, goods_name AS goodsName,
               goods_spec AS goodsSpec, goods_brand_name AS goodsBrandName
        FROM experiment_order_child
        WHERE delete_status = 2 AND order_form_id = %(oid)s
          AND IFNULL(fcsq, 0) = 0 AND is_sure IS NULL
          AND order_status IN (39, 41)
        """,
        {"oid": order_id},
    )
    return [to_jsonable(r) for r in rows]
