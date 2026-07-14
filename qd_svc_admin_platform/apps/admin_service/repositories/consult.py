from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def list_consults(
    *,
    user_name: str = "",
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0 AND t.type = 2"
    params: dict[str, Any] = {}
    if user_name:
        where += " AND t.userName LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if mobile:
        where += " AND t.mobile LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    total = int(
        scalar(
            f"SELECT COUNT(*) FROM service_consult t {where}",
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.*, em.name AS className
        FROM service_consult t
        LEFT JOIN experiment_manage em ON t.class_id = em.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_consult_detail(consult_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT t.*, em.name AS className
        FROM service_consult t
        LEFT JOIN experiment_manage em ON t.class_id = em.id
        WHERE t.id = %(id)s AND t.deleteStatus = 0
        LIMIT 1
        """,
        {"id": consult_id},
    )
    if not row:
        return None
    children = fetch_all(
        "SELECT * FROM service_consult_child WHERE consult_id = %(cid)s ORDER BY id ASC",
        {"cid": consult_id},
    )
    detail = normalize_row(row) or {}
    detail["children"] = normalize_rows(children)
    return detail


def cancel_consult(consult_id: int) -> None:
    execute(
        "UPDATE service_consult SET status = 3 WHERE id = %(id)s",
        {"id": consult_id},
    )


def get_consult_settings() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT gzh_userId_ut, gzh_issend_ut, service_mail_ut, mail_issend_ut
        FROM sysconfig WHERE id = 1 LIMIT 1
        """
    )
    if not row:
        return {}
    return {
        "gzh_userId_ut": row.get("gzh_userId_ut"),
        "gzh_issend_ut": row.get("gzh_issend_ut"),
        "service_mail_ut": row.get("service_mail_ut"),
        "mail_issend_ut": row.get("mail_issend_ut"),
    }


def save_consult_settings(
    *,
    gzh_user_id: str,
    gzh_issend: int,
    service_mail: str,
    mail_issend: int,
) -> None:
    execute(
        """
        UPDATE sysconfig
        SET gzh_userId_ut = %(gzh_user_id)s,
            gzh_issend_ut = %(gzh_issend)s,
            service_mail_ut = %(service_mail)s,
            mail_issend_ut = %(mail_issend)s
        WHERE id = 1
        """,
        {
            "gzh_user_id": gzh_user_id,
            "gzh_issend": gzh_issend,
            "service_mail": service_mail,
            "mail_issend": mail_issend,
        },
    )


def get_is_show() -> dict[str, Any]:
    row = fetch_one("SELECT is_show FROM sysconfig WHERE id = 1 LIMIT 1")
    return {"is_show": row.get("is_show") if row else 0}


def save_is_show(is_show: int) -> None:
    execute(
        "UPDATE sysconfig SET is_show = %(is_show)s WHERE id = 1",
        {"is_show": is_show},
    )
