from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_adverts(
    *,
    ad_title: str = "",
    mark: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE a.deleteStatus = 0"
    params: dict[str, Any] = {}
    if ad_title:
        where += " AND a.ad_title LIKE %(ad_title)s"
        params["ad_title"] = f"%{ad_title}%"
    if mark not in (None, ""):
        where += " AND a.mark = %(mark)s"
        params["mark"] = mark
    total = int(scalar(f"SELECT COUNT(*) FROM advert a {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            a.*,
            p.ap_title AS ap_title,
            p.ap_type AS ap_type
        FROM advert a
        LEFT JOIN adv_pos p ON a.ad_ap_id = p.id
        {where}
        ORDER BY a.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total

def get_advert(advert_id: int) -> dict[str, Any] | None:
    row = fetch_one("SELECT * FROM advert WHERE id = %(id)s LIMIT 1", {"id": advert_id})
    from apps.admin_ops.helpers import normalize_row

    return normalize_row(row)


def insert_advert(fields: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO advert
            (addTime, deleteStatus, ad_title, ad_ap_id, ad_begin_time, ad_end_time,
             ad_url, ad_text, ad_slide_sequence, mark, ad_type, ad_type_value,
             ad_status, ad_acc_id)
        VALUES
            (NOW(), 0, %(ad_title)s, %(ad_ap_id)s, %(ad_begin_time)s, %(ad_end_time)s,
             %(ad_url)s, %(ad_text)s, %(ad_slide_sequence)s, %(mark)s, %(ad_type)s, %(ad_type_value)s,
             1, %(ad_acc_id)s)
        """,
        fields,
    )


def update_advert(advert_id: int, fields: dict[str, Any]) -> None:
    execute(
        """
        UPDATE advert
        SET ad_title = %(ad_title)s,
            ad_ap_id = %(ad_ap_id)s,
            ad_begin_time = %(ad_begin_time)s,
            ad_end_time = %(ad_end_time)s,
            ad_url = %(ad_url)s,
            ad_text = %(ad_text)s,
            ad_slide_sequence = %(ad_slide_sequence)s,
            mark = %(mark)s,
            ad_type = %(ad_type)s,
            ad_type_value = %(ad_type_value)s,
            ad_acc_id = %(ad_acc_id)s
        WHERE id = %(id)s
        """,
        {**fields, "id": advert_id},
    )


def delete_adverts(ids: list[int]) -> int:
    if not ids:
        return 0
    placeholders = ", ".join([f"%({i})s" for i in range(len(ids))])
    params = {str(i): v for i, v in enumerate(ids)}
    return execute(f"DELETE FROM advert WHERE id IN ({placeholders})", params)


def list_adv_pos(
    *,
    ap_title: str = "",
    mark: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE deleteStatus = 0"
    params: dict[str, Any] = {}
    if ap_title:
        where += " AND ap_title LIKE %(ap_title)s"
        params["ap_title"] = f"%{ap_title}%"
    if mark not in (None, ""):
        where += " AND mark = %(mark)s"
        params["mark"] = mark
    total = int(scalar(f"SELECT COUNT(*) FROM adv_pos {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT *
        FROM adv_pos
        {where}
        ORDER BY addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_adv_pos(pos_id: int) -> dict[str, Any] | None:
    from apps.admin_ops.helpers import normalize_row

    row = fetch_one("SELECT * FROM adv_pos WHERE id = %(id)s LIMIT 1", {"id": pos_id})
    return normalize_row(row)


def insert_adv_pos(fields: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO adv_pos
            (addTime, deleteStatus, ap_title, ap_content, ap_type, ap_status,
             ap_use_status, ap_width, ap_height, ap_price, ap_sys_type,
             ap_show_type, ap_acc_url, ap_text, ap_code, mark)
        VALUES
            (NOW(), 0, %(ap_title)s, %(ap_content)s, %(ap_type)s, %(ap_status)s,
             %(ap_use_status)s, %(ap_width)s, %(ap_height)s, %(ap_price)s, %(ap_sys_type)s,
             %(ap_show_type)s, %(ap_acc_url)s, %(ap_text)s, %(ap_code)s, %(mark)s)
        """,
        fields,
    )


def update_adv_pos(pos_id: int, fields: dict[str, Any]) -> None:
    execute(
        """
        UPDATE adv_pos
        SET ap_title = %(ap_title)s,
            ap_content = %(ap_content)s,
            ap_type = %(ap_type)s,
            ap_status = %(ap_status)s,
            ap_use_status = %(ap_use_status)s,
            ap_width = %(ap_width)s,
            ap_height = %(ap_height)s,
            ap_price = %(ap_price)s,
            ap_sys_type = %(ap_sys_type)s,
            ap_show_type = %(ap_show_type)s,
            ap_acc_url = %(ap_acc_url)s,
            ap_text = %(ap_text)s,
            ap_code = %(ap_code)s,
            mark = %(mark)s
        WHERE id = %(id)s
        """,
        {**fields, "id": pos_id},
    )


def delete_adv_pos(ids: list[int]) -> int:
    if not ids:
        return 0
    placeholders = ", ".join([f"%({i})s" for i in range(len(ids))])
    params = {str(i): v for i, v in enumerate(ids)}
    return execute(
        f"DELETE FROM adv_pos WHERE id IN ({placeholders}) AND IFNULL(ap_sys_type, 1) <> 0",
        params,
    )


def list_adv_pos_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, ap_title AS apTitle, ap_type AS apType, mark
        FROM adv_pos
        WHERE deleteStatus = 0
        ORDER BY id DESC
        """
    )
    return rows
