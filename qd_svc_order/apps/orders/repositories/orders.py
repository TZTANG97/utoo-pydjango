import logging
from typing import Any

from apps.auth_support.services.customer import CustomerUserService
from apps.core.db_utils import fetch_all, fetch_one, scalar

logger = logging.getLogger(__name__)


def base_user_filter() -> str:
    return """
        (t.order_type IN ('6', '8') OR CAST(t.order_type AS UNSIGNED) IN (6, 8))
        AND t.order_status > 0
        AND t.order_status >= 30
        AND (
            t.custom_user_id = %(user_id)s
            OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR t.mobile = %(mobile)s
        )
    """


def user_context(user_id: int) -> tuple[int, str]:
    user = CustomerUserService.get_by_id(user_id)
    return user_id, (user.mobile or "") if user else ""


def count_and_list(
    *,
    user_id: int,
    mobile: str,
    extra_where: str = "",
    keywords: str = "",
    join_sql: str = "",
    offset: int,
    limit: int,
) -> tuple[int, list[dict[str, Any]]]:
    kw_join = ""
    kw_where = ""
    params: dict[str, Any] = {
        "user_id": user_id,
        "user_id_str": str(user_id),
        "mobile": mobile,
        "limit": limit,
        "offset": offset,
    }
    if keywords:
        kw_join = "LEFT JOIN experiment_order_child ocf ON t.id = ocf.order_form_id"
        kw_where = " AND (ocf.goods_name LIKE %(kw)s OR t.order_id LIKE %(kw)s)"
        params["kw"] = f"%{keywords}%"

    base = base_user_filter()
    count_sql = f"""
        SELECT COUNT(DISTINCT t.id) AS cnt
        FROM experiment_order t
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        {join_sql}
        {kw_join}
        WHERE {base} {extra_where} {kw_where}
    """
    list_sql = f"""
        SELECT t.* FROM experiment_order t
        WHERE t.id IN (
            SELECT DISTINCT t.id FROM experiment_order t
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
            {join_sql}
            {kw_join}
            WHERE {base} {extra_where} {kw_where}
        )
        ORDER BY t.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    total = int(scalar(count_sql, params, 0))
    rows = fetch_all(list_sql, params)
    return total, rows


def load_children(order_ids: list[int]) -> dict[int, list[dict]]:
    if not order_ids:
        return {}
    placeholders = ", ".join(str(i) for i in order_ids)
    rows = fetch_all(
        f"""
        SELECT * FROM experiment_order_child
        WHERE order_form_id IN ({placeholders})
          AND delete_status = 2 AND order_status > 0
        ORDER BY id ASC
        """
    )
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        oid = int(row.get("order_form_id") or 0)
        grouped.setdefault(oid, []).append(row)
    return grouped


def get_sale_order_for_user(
    *, order_id: int, user_id: int, mobile: str
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT t.* FROM experiment_order t
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        WHERE t.id = %(oid)s
          AND (t.order_type IN ('6', '8') OR CAST(t.order_type AS UNSIGNED) IN (6, 8))
          AND (
            t.custom_user_id = %(user_id)s
            OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR t.mobile = %(mobile)s
          )
        LIMIT 1
        """,
        {
            "oid": order_id,
            "user_id": user_id,
            "user_id_str": str(user_id),
            "mobile": mobile,
        },
    )


def load_bills(order_id: int, bill_type: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM qd_bill
        WHERE exp_of_id = %(oid)s AND type = %(tp)s
        ORDER BY id ASC
        """,
        {"oid": order_id, "tp": bill_type},
    )


def load_logs(order_id: int) -> list[dict[str, Any]]:
    try:
        rows = fetch_all(
            """
            SELECT id, addTime, deleteStatus, log_info, type, state_info,
                   log_user_id, of_id
            FROM experiment_order_log
            WHERE of_id = %(oid)s AND (deleteStatus = 0 OR deleteStatus IS NULL)
            ORDER BY addTime DESC
            LIMIT 200
            """,
            {"oid": order_id},
        )
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            d["log_info"] = d.get("log_info") or ""
            d["log_user"] = {"id": d.pop("log_user_id", None)}
            d["of"] = {"id": d.get("of_id")}
            out.append(d)
        return out
    except Exception as exc:
        logger.warning("load logs failed: %s", exc)
        return []


def has_unapplied_bill(order_id: int) -> bool:
    return bool(
        fetch_one(
            """
            SELECT 1 AS ok FROM qd_bill
            WHERE exp_of_id = %(oid)s AND is_apply = 0 LIMIT 1
            """,
            {"oid": order_id},
        )
    )


def get_purchase_order_for_user(
    *, order_id: int, user_id: int, mobile: str
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT po.* FROM experiment_order po
        LEFT JOIN experiment_order parent ON po.parent_id = parent.id
        LEFT JOIN qd_user_company quc ON parent.customer_name = quc.id
        WHERE po.id = %(oid)s
          AND (
            parent.custom_user_id = %(user_id)s
            OR CAST(parent.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR parent.mobile = %(mobile)s
          )
        LIMIT 1
        """,
        {
            "oid": order_id,
            "user_id": user_id,
            "user_id_str": str(user_id),
            "mobile": mobile,
        },
    )


def list_child_forms_by_sale(
    *,
    of_id: int,
    order_id_kw: str,
    offset: int,
    limit: int,
) -> tuple[int, list[dict[str, Any]]]:
    params: dict[str, Any] = {
        "of_id": of_id,
        "offset": offset,
        "limit": limit,
    }
    extra = ""
    if order_id_kw.strip():
        extra = " AND c.order_id LIKE %(oid_kw)s"
        params["oid_kw"] = f"%{order_id_kw.strip()}%"
    total = int(
        scalar(
            f"""
            SELECT COUNT(1) FROM experiment_order_child c
            WHERE c.order_form_id = %(of_id)s
              AND c.delete_status = 2 AND c.order_status > 0
              {extra}
            """,
            params,
            0,
        )
        or 0
    )
    rows = fetch_all(
        f"""
        SELECT c.* FROM experiment_order_child c
        WHERE c.order_form_id = %(of_id)s
          AND c.delete_status = 2 AND c.order_status > 0
          {extra}
        ORDER BY c.add_time DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )
    return total, rows


def list_purchase_orders_by_sale(
    *,
    parent_id: int,
    order_id_kw: str,
    offset: int,
    limit: int,
) -> tuple[int, list[dict[str, Any]]]:
    params: dict[str, Any] = {
        "parent_id": parent_id,
        "offset": offset,
        "limit": limit,
    }
    extra = ""
    if order_id_kw.strip():
        extra = " AND t.order_id LIKE %(oid_kw)s"
        params["oid_kw"] = f"%{order_id_kw.strip()}%"
    total = int(
        scalar(
            f"""
            SELECT COUNT(1) FROM experiment_order t
            WHERE t.parent_id = %(parent_id)s AND t.order_status > 0 {extra}
            """,
            params,
            0,
        )
        or 0
    )
    rows = fetch_all(
        f"""
        SELECT t.* FROM experiment_order t
        WHERE t.parent_id = %(parent_id)s AND t.order_status > 0 {extra}
        ORDER BY t.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )
    return total, rows


def load_purchase_line_children(purchase_order_id: int) -> list[dict[str, Any]]:
    try:
        return fetch_all(
            """
            SELECT eoc.*
            FROM exp_qd_purchase_order_child poc
            JOIN experiment_order_child eoc ON poc.order_child_id = eoc.id
            WHERE poc.purchase_order_id = %(pid)s
              AND eoc.delete_status = 2
            ORDER BY eoc.id ASC
            """,
            {"pid": purchase_order_id},
        )
    except Exception:
        return []


def get_experiment_manage(em_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT * FROM experiment_manage
        WHERE id = %(id)s AND deleteStatus = 0 LIMIT 1
        """,
        {"id": em_id},
    )


def customer_orders(user_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM experiment_order
        WHERE deleteStatus = 0
          AND custom_user_id = %(uid)s
          AND order_type = 6
        ORDER BY id DESC
        """,
        {"uid": user_id},
    )


def sum_bill(order_id: int, bill_type: int) -> float:
    return float(
        scalar(
            """
            SELECT COALESCE(SUM(money), 0) FROM qd_bill
            WHERE exp_of_id = %(oid)s AND type = %(tp)s
            """,
            {"oid": order_id, "tp": bill_type},
            0,
        )
        or 0
    )
