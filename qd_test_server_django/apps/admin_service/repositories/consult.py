from __future__ import annotations

from datetime import date, datetime
from typing import Any

from apps.admin_service.helpers import normalize_rows, page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar
from qd_common.serialize import to_jsonable


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


def _fmt_date(val: Any) -> str:
    if val is None or val == "":
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    text = str(val).strip()
    return text[:10] if text else ""


def get_consult_detail(consult_id: int) -> dict[str, Any] | None:
    """对齐 Java ServiceConsultAction.consultDetail.ajax 的 obj 形状。"""
    row = fetch_one(
        """
        SELECT t.*, em.name AS className, em.head_user_id AS headUserId
        FROM service_consult t
        LEFT JOIN experiment_manage em ON t.class_id = em.id
        WHERE t.id = %(id)s AND IFNULL(t.deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": consult_id},
    )
    if not row:
        return None

    consult = dict(row)
    class_name = consult.pop("className", None) or ""
    head_user_id = consult.pop("headUserId", None)
    try:
        class_id = int(consult.get("class_id") or 0)
    except (TypeError, ValueError):
        class_id = 0

    consult["collection_time_str"] = _fmt_date(consult.get("collection_time"))
    consult["delivery_time_str"] = _fmt_date(consult.get("delivery_time"))
    try:
        consult["status"] = int(consult.get("status") if consult.get("status") is not None else -1)
    except (TypeError, ValueError):
        consult["status"] = -1

    sy_user_name = ""
    if head_user_id not in (None, ""):
        su = fetch_one(
            """
            SELECT user_name, true_name
            FROM sy_users
            WHERE id = %(id)s
            LIMIT 1
            """,
            {"id": str(head_user_id)},
        )
        if su:
            sy_user_name = str(su.get("user_name") or su.get("true_name") or "")
    consult["syUserName"] = sy_user_name

    children = fetch_all(
        """
        SELECT *
        FROM service_consult_child
        WHERE consult_id = %(cid)s
          AND IFNULL(deleteStatus, 0) = 0
        ORDER BY id ASC
        """,
        {"cid": consult_id},
    )
    childs: list[dict[str, Any]] = []
    for ch in children:
        item = dict(ch)
        goods_id = item.get("goods_id")
        exp_goods = None
        if goods_id not in (None, ""):
            exp_goods = fetch_one(
                """
                SELECT id, goods_name, goods_model, goods_brand_id
                FROM experiment_goods
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": goods_id},
            )
        item["expGoods"] = exp_goods
        childs.append(item)

    files = fetch_all(
        """
        SELECT id, info, name, path, ext, size, addTime
        FROM accessory
        WHERE IFNULL(deleteStatus, 0) = 0 AND sc_id = %(sid)s
        ORDER BY id ASC
        """,
        {"sid": consult_id},
    )

    childsyp: list[dict[str, Any]] = []
    try:
        childsyp = fetch_all(
            """
            SELECT *
            FROM order_sample_information
            WHERE consult_id = %(cid)s
            ORDER BY id ASC
            """,
            {"cid": consult_id},
        )
    except Exception:
        childsyp = []

    zc_mobile = ""
    isxg = True
    user_id = consult.get("user_id")
    if user_id not in (None, ""):
        user = fetch_one(
            """
            SELECT mobile
            FROM `user`
            WHERE id = %(id)s
            LIMIT 1
            """,
            {"id": user_id},
        )
        if not user:
            user = fetch_one(
                """
                SELECT mobile
                FROM exp_user
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": user_id},
            )
        if user:
            zc_mobile = str(user.get("mobile") or "")
            if zc_mobile and zc_mobile != str(consult.get("mobile") or ""):
                isxg = False

    return {
        "consult": to_jsonable(consult),
        "className": class_name,
        "classId": class_id,
        "childs": to_jsonable(childs),
        "childsyp": to_jsonable(childsyp),
        "files": to_jsonable(files),
        "sampleList": [],
        "zcMobile": zc_mobile,
        "isxg": isxg,
    }


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
