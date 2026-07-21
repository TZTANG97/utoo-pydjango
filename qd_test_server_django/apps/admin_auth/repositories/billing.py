from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar
from qd_common.serialize import to_jsonable


def _page_clause(offset: int, limit: int) -> str:
    return " LIMIT %(limit)s OFFSET %(offset)s "


def count_invoice_applies(*, status: str = "", start_time: str = "", end_time: str = "") -> int:
    extra, params = _invoice_filters(status, start_time, end_time)
    return int(
        scalar(
            f"SELECT COUNT(1) FROM invoice_apply_log t WHERE t.deleteStatus = 0 {extra}",
            params,
            0,
        )
        or 0
    )


def list_invoice_applies(
    *, offset: int, limit: int, status: str = "", start_time: str = "", end_time: str = ""
) -> list[dict[str, Any]]:
    extra, params = _invoice_filters(status, start_time, end_time)
    params.update({"offset": offset, "limit": limit})
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.user_id, t.invoice_title, t.invoice_money,
            t.type, t.status, t.order_ids, t.is_pay, t.notes, t.email,
            t.invoice_type, t.credit_code, t.invoice_num,
            u.userName, u.mobile
        FROM invoice_apply_log t
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.deleteStatus = 0 {extra}
        ORDER BY t.addTime DESC
        {_page_clause(offset, limit)}
        """,
        params,
    )
    out = []
    for row in rows:
        item = to_jsonable(row)
        order_ids = str(item.get("order_ids") or "").strip()
        item["order_id"] = ""
        if order_ids:
            first = order_ids.split(",")[0].strip()
            if first.isdigit():
                eo = fetch_one(
                    "SELECT order_id FROM experiment_order WHERE id = %(id)s LIMIT 1",
                    {"id": int(first)},
                )
                if eo:
                    item["order_id"] = eo.get("order_id") or ""
        out.append(item)
    return out


def _invoice_filters(status: str, start_time: str, end_time: str) -> tuple[str, dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {}
    if status:
        extra += " AND t.status = %(status)s"
        params["status"] = int(status)
    if start_time:
        extra += " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    if end_time:
        extra += " AND t.addTime <= %(end_time)s"
        params["end_time"] = end_time
    return extra, params


def get_invoice_apply(apply_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT t.*, u.userName, u.mobile
        FROM invoice_apply_log t
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.id = %(id)s AND t.deleteStatus = 0
        LIMIT 1
        """,
        {"id": apply_id},
    )
    return to_jsonable(row) if row else None


def count_pay_logs(
    *,
    order_num: str = "",
    user_id: str = "",
    pay_type: str = "",
    pay_way: str = "",
) -> int:
    extra, params = _pay_log_filters(order_num, user_id, pay_type, pay_way)
    return int(
        scalar(
            f"""
            SELECT COUNT(1)
            FROM pay_info_log t
            LEFT JOIN experiment_order e ON t.order_id = e.id
            LEFT JOIN exp_user u ON t.user_id = u.id
            WHERE t.deleteStatus = 0 AND t.status = 2 {extra}
            """,
            params,
            0,
        )
        or 0
    )


def list_pay_logs(
    *,
    offset: int,
    limit: int,
    order_num: str = "",
    user_id: str = "",
    pay_type: str = "",
    pay_way: str = "",
) -> list[dict[str, Any]]:
    extra, params = _pay_log_filters(order_num, user_id, pay_type, pay_way)
    params.update({"offset": offset, "limit": limit})
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.user_id, t.money, t.status, t.order_id,
            t.pay_type, t.pay_way, t.pa_num, t.payTime,
            e.order_id AS order_num, e.order_type, u.userName, u.mobile, u.trueName
        FROM pay_info_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.deleteStatus = 0 AND t.status = 2 {extra}
        ORDER BY t.addTime DESC
        {_page_clause(offset, limit)}
        """,
        params,
    )
    return [to_jsonable(r) for r in rows]


def _pay_log_filters(
    order_num: str, user_id: str, pay_type: str, pay_way: str
) -> tuple[str, dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {}
    if user_id:
        extra += " AND t.user_id = %(user_id)s"
        params["user_id"] = int(user_id)
    if pay_type:
        extra += " AND t.pay_type = %(pay_type)s"
        params["pay_type"] = int(pay_type)
    if pay_way:
        pw = int(pay_way)
        if pw == 4:
            extra += " AND t.pay_way IN (4,5,6,7)"
        else:
            extra += " AND t.pay_way = %(pay_way)s"
            params["pay_way"] = pw
    if order_num:
        extra += " AND e.order_id LIKE %(order_num)s"
        params["order_num"] = f"%{order_num}%"
    return extra, params


def count_payment_applications(
    *, status: str = "", start_time: str = "", end_time: str = ""
) -> int:
    extra, params = _payment_apply_filters(status, start_time, end_time)
    return int(
        scalar(
            f"SELECT COUNT(1) FROM payment_application t WHERE t.deleteStatus = 0 {extra}",
            params,
            0,
        )
        or 0
    )


def list_payment_applications(
    *, offset: int, limit: int, status: str = "", start_time: str = "", end_time: str = ""
) -> list[dict[str, Any]]:
    extra, params = _payment_apply_filters(status, start_time, end_time)
    params.update({"offset": offset, "limit": limit})
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.userId, t.money, t.orderType, t.applyStatus,
            t.mark, t.pay_way, t.pa_num, t.orderId,
            u.userName, u.mobile, u.trueName
        FROM payment_application t
        LEFT JOIN exp_user u ON t.userId = u.id
        WHERE t.deleteStatus = 0 {extra}
        ORDER BY t.addTime DESC
        {_page_clause(offset, limit)}
        """,
        params,
    )
    return [to_jsonable(r) for r in rows]


def _payment_apply_filters(
    status: str, start_time: str, end_time: str
) -> tuple[str, dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {}
    if status:
        extra += " AND t.applyStatus = %(status)s"
        params["status"] = str(status)
    if start_time:
        extra += " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    if end_time:
        extra += " AND t.addTime <= %(end_time)s"
        params["end_time"] = end_time
    return extra, params


def get_payment_application(apply_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT t.*, u.userName, u.mobile, u.trueName
        FROM payment_application t
        LEFT JOIN exp_user u ON t.userId = u.id
        WHERE t.id = %(id)s AND t.deleteStatus = 0
        LIMIT 1
        """,
        {"id": apply_id},
    )
    return to_jsonable(row) if row else None


def count_retest_applications(*, status: str = "", start_time: str = "", end_time: str = "") -> int:
    extra, params = _retest_filters(status, start_time, end_time)
    return int(
        scalar(
            f"SELECT COUNT(1) FROM retest_application t WHERE t.deleteStatus = 0 {extra}",
            params,
            0,
        )
        or 0
    )


def list_retest_applications(
    *, offset: int, limit: int, status: str = "", start_time: str = "", end_time: str = ""
) -> list[dict[str, Any]]:
    extra, params = _retest_filters(status, start_time, end_time)
    params.update({"offset": offset, "limit": limit})
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.userId, t.applyStatus, t.mark,
            t.orderId, t.order_id AS fc_no, t.remeasurement_require,
            u.userName, u.mobile, u.trueName
        FROM retest_application t
        LEFT JOIN exp_user u ON t.userId = u.id
        WHERE t.deleteStatus = 0 {extra}
        ORDER BY t.addTime DESC
        {_page_clause(offset, limit)}
        """,
        params,
    )
    return [to_jsonable(r) for r in rows]


def _retest_filters(status: str, start_time: str, end_time: str) -> tuple[str, dict[str, Any]]:
    extra = ""
    params: dict[str, Any] = {}
    if status != "":
        extra += " AND t.applyStatus = %(status)s"
        params["status"] = int(status)
    if start_time:
        extra += " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    if end_time:
        extra += " AND t.addTime <= %(end_time)s"
        params["end_time"] = end_time
    return extra, params


def get_retest_application(apply_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.*, u.userName, u.mobile, u.trueName,
            c.order_status AS child_order_status
        FROM retest_application t
        LEFT JOIN exp_user u ON t.userId = u.id
        LEFT JOIN experiment_order_child c ON CAST(c.id AS CHAR) = CAST(t.orderId AS CHAR)
        WHERE t.id = %(id)s AND t.deleteStatus = 0
        LIMIT 1
        """,
        {"id": apply_id},
    )
    return to_jsonable(row) if row else None


def _related_experiment_order(child_order_id: str) -> dict[str, Any] | None:
    """对齐 Java：经 exp_qd_purchase_order_child 找主单；否则回退子单 order_form_id。"""
    if not child_order_id:
        return None
    row = fetch_one(
        """
        SELECT eo.id, eo.order_id, eo.order_status, eo.order_type
        FROM exp_qd_purchase_order_child poc
        INNER JOIN experiment_order eo ON eo.id = poc.purchase_order_id
        WHERE poc.order_child_id = %(cid)s
          AND IFNULL(eo.order_status, 0) != 0
        ORDER BY eo.id DESC
        LIMIT 1
        """,
        {"cid": child_order_id},
    )
    if row:
        return to_jsonable(row)
    row = fetch_one(
        """
        SELECT eo.id, eo.order_id, eo.order_status, eo.order_type
        FROM experiment_order_child c
        INNER JOIN experiment_order eo ON eo.id = c.order_form_id
        WHERE CAST(c.id AS CHAR) = CAST(%(cid)s AS CHAR)
          AND IFNULL(eo.order_status, 0) != 0
        LIMIT 1
        """,
        {"cid": child_order_id},
    )
    return to_jsonable(row) if row else None


def list_retest_test_files(child_order_id: str) -> list[dict[str, Any]]:
    """对齐 Java accessoryService.getByExpOfId(orderId)。"""
    if not child_order_id:
        return []
    rows = fetch_all(
        """
        SELECT id, path, name, info, ext, type
        FROM accessory
        WHERE IFNULL(deleteStatus, 0) = 0
          AND IFNULL(type, 0) != 5
          AND (
            CAST(exp_of_id AS CHAR) = CAST(%(oid)s AS CHAR)
            OR CAST(child_of_id AS CHAR) = CAST(%(oid)s AS CHAR)
          )
        ORDER BY id ASC
        """,
        {"oid": child_order_id},
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        item = to_jsonable(r)
        path = str(item.get("path") or "").rstrip("/")
        name = str(item.get("name") or "")
        item["url"] = f"{path}/{name}" if path and name else (path or name or "")
        out.append(item)
    return out


def list_retest_logs(apply_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            ral.id,
            ral.addTime,
            ral.content,
            ral.user_id AS userId,
            IFNULL(su.true_name, IFNULL(eu.trueName, IFNULL(eu.userName, IFNULL(eu.mobile, '')))) AS addusername
        FROM retest_application_log ral
        LEFT JOIN sy_users su ON CAST(su.id AS CHAR) = CAST(ral.user_id AS CHAR)
        LEFT JOIN exp_user eu ON CAST(eu.id AS CHAR) = CAST(ral.user_id AS CHAR)
        WHERE ral.retest_application_id = %(id)s
        ORDER BY ral.addTime ASC, ral.id ASC
        """,
        {"id": apply_id},
    )
    return [to_jsonable(r) for r in rows]


def get_retest_detail(apply_id: int) -> dict[str, Any] | None:
    """对齐 Java retestDetail.htm 返回结构。"""
    row = get_retest_application(apply_id)
    if not row:
        return None
    child_id = str(row.get("orderId") or "")
    exp = _related_experiment_order(child_id)
    row["fc_no"] = row.get("order_id") or row.get("fc_no")
    row["experimentOrder"] = exp
    row["testfiles"] = list_retest_test_files(child_id)
    row["logs"] = list_retest_logs(apply_id)
    return row
