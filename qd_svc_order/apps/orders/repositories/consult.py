from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_reservable_manage_rows() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, name, manage_main_photo_id
        FROM experiment_manage
        WHERE deleteStatus = 0 AND type = 3
        ORDER BY sequence ASC
        """
    )


def count_user_consults(
    *,
    user_id: int,
    startime: str = "",
    endtime: str = "",
) -> int:
    params: dict[str, Any] = {"user_id": user_id}
    where_extra = ""
    if startime:
        where_extra += " AND t.addTime >= %(startime)s"
        params["startime"] = startime
    if endtime:
        where_extra += " AND t.addTime <= %(endtime)s"
        params["endtime"] = endtime
    return int(
        scalar(
            f"""
            SELECT COUNT(1) FROM service_consult t
            WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s {where_extra}
            """,
            params,
            0,
        )
        or 0
    )


def list_user_consults_page(
    *,
    user_id: int,
    offset: int,
    limit: int,
    startime: str = "",
    endtime: str = "",
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "user_id": user_id,
        "offset": offset,
        "limit": limit,
    }
    where_extra = ""
    if startime:
        where_extra += " AND t.addTime >= %(startime)s"
        params["startime"] = startime
    if endtime:
        where_extra += " AND t.addTime <= %(endtime)s"
        params["endtime"] = endtime
    return fetch_all(
        f"""
        SELECT t.id, t.addTime, m.name AS testName, t.status, t.content,
               t.is_urge, t.order_num
        FROM service_consult t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s {where_extra}
        ORDER BY t.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )


def get_consult_owner(consult_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, user_id FROM service_consult
        WHERE id = %(cid)s AND deleteStatus = 0 LIMIT 1
        """,
        {"cid": consult_id},
    )


def mark_consult_cancelled(consult_id: int) -> None:
    execute(
        "UPDATE service_consult SET status = 3 WHERE id = %(cid)s",
        {"cid": consult_id},
    )


def insert_exp_user_log(*, user_id: int, info: str) -> None:
    execute(
        """
        INSERT INTO exp_user_log (addTime, deleteStatus, user_id, info)
        VALUES (NOW(), 0, %(uid)s, %(info)s)
        """,
        {"uid": user_id, "info": info},
    )


def insert_service_consult(params: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO service_consult (
            addTime, deleteStatus, userName, mobile, company_name, content,
            status, class_id, user_id, type, reverso_context, send_address,
            addressee_name, addressee_mobile, is_video, is_arrive, is_on, order_num
        ) VALUES (
            NOW(), 0, %(user_name)s, %(mobile)s, %(company_name)s, %(content)s,
            0, %(class_id)s, %(user_id)s, 2,
            %(reverso)s, %(address)s, %(addressee_name)s, %(addressee_mobile)s,
            %(is_video)s, %(is_arrive)s, %(is_on)s, %(order_num)s
        )
        """,
        params,
    )


def insert_order_sample_row(cols: dict[str, Any]) -> None:
    names = list(cols.keys()) + ["addTime"]
    placeholders = [f"%({k})s" for k in cols] + ["NOW()"]
    sql = (
        f"INSERT INTO order_sample_information ({', '.join(names)}) "
        f"VALUES ({', '.join(placeholders)})"
    )
    execute(sql, cols)


def link_accessory_to_consult(*, consult_id: int, accessory_id: int) -> None:
    execute(
        "UPDATE accessory SET sc_id = %(cid)s WHERE id = %(aid)s",
        {"cid": consult_id, "aid": accessory_id},
    )
