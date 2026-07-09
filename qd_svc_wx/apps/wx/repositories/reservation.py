from typing import Any

from apps.core.db_utils import fetch_all, fetch_one
from qd_common.serialize import to_jsonable


def get_consult_row(*, user_id: int, consult_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT t.*, m.name AS className,
               COALESCE(su.user_name, su.true_name, '') AS syUserName
        FROM service_consult t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        LEFT JOIN sy_users su ON su.id = m.head_user_id
        WHERE t.id = %(cid)s AND t.deleteStatus = 0 AND t.user_id = %(uid)s
        LIMIT 1
        """,
        {"cid": consult_id, "uid": user_id},
    )


def get_order_brief(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT order_id, order_type, order_status
        FROM experiment_order WHERE id = %(oid)s LIMIT 1
        """,
        {"oid": order_id},
    )


def list_consult_children(consult_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        "SELECT * FROM service_consult_child WHERE consult_id = %(cid)s",
        {"cid": consult_id},
    )
    return [to_jsonable(r) for r in rows]


def list_consult_files(consult_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, path, name, info, ext FROM accessory
        WHERE deleteStatus = 0 AND sc_id = %(cid)s
        """,
        {"cid": consult_id},
    )


def list_sample_rows(consult_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT osi.*, ast.attribute_name
        FROM order_sample_information osi
        LEFT JOIN attribute_state ast ON ast.id = osi.attribute_state
        WHERE osi.consult_id = %(cid)s
        ORDER BY osi.addTime DESC
        """,
        {"cid": consult_id},
    )


def get_sample_attribute(attr_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, sttribute_name, parent_id FROM sample_attribute_manage
        WHERE id = %(id)s LIMIT 1
        """,
        {"id": attr_id},
    )


def find_user_by_wx_openid(openid: str) -> int | None:
    row = fetch_one(
        """
        SELECT id FROM exp_user
        WHERE deleteStatus = 0 AND wx_openid = %(oid)s LIMIT 1
        """,
        {"oid": openid},
    )
    return int(row["id"]) if row else None
