from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar
from qd_common.serialize import to_jsonable


def _page_clause(offset: int, limit: int) -> str:
    return " LIMIT %(limit)s OFFSET %(offset)s "


def _invoice_order_join() -> str:
    """批量开票按订单号展开成多行（对齐 Java 按 of_id 展示）。"""
    return """
        LEFT JOIN experiment_order e
          ON IFNULL(t.order_ids, '') <> ''
         AND FIND_IN_SET(CAST(e.id AS CHAR), REPLACE(t.order_ids, ' ', ''))
    """


def count_invoice_applies(*, status: str = "", start_time: str = "", end_time: str = "") -> int:
    extra, params = _invoice_filters(status, start_time, end_time)
    return int(
        scalar(
            f"""
            SELECT COUNT(1)
            FROM invoice_apply_log t
            {_invoice_order_join()}
            WHERE t.deleteStatus = 0 {extra}
            """,
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
            t.type, t.status, t.order_ids, t.moneys, t.is_pay, t.notes, t.email,
            t.invoice_type, t.credit_code, t.invoice_num,
            e.id AS of_id, e.order_id AS order_id,
            u.userName, u.mobile
        FROM invoice_apply_log t
        LEFT JOIN exp_user u ON t.user_id = u.id
        {_invoice_order_join()}
        WHERE t.deleteStatus = 0 {extra}
        ORDER BY t.addTime DESC, t.id DESC, e.id ASC
        {_page_clause(offset, limit)}
        """,
        params,
    )
    out = []
    for row in rows:
        item = to_jsonable(row)
        oids = [x.strip() for x in str(item.get("order_ids") or "").split(",") if x.strip()]
        moneys = [x.strip() for x in str(item.get("moneys") or "").split(",") if x.strip()]
        of_id = str(item.get("of_id") or "").strip()
        if of_id and of_id in oids:
            idx = oids.index(of_id)
            if idx < len(moneys):
                item["invoice_money"] = moneys[idx]
        elif not item.get("order_id") and oids:
            first = oids[0]
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


def _order_status_label(status: Any) -> str:
    try:
        st = int(status) if status is not None else None
    except (TypeError, ValueError):
        st = None
    labels = {
        0: "已取消",
        5: "订单未发起审核",
        10: "已驳回",
        15: "审核中",
        20: "待审核",
        25: "待确认",
        30: "已审核",
        35: "样品发货",
        36: "样品到货",
        38: "测试中",
        39: "测试中",
        40: "已确认",
        41: "已付款",
        42: "已开票",
        43: "部分完成",
        50: "已完成",
        55: "已评价",
        60: "已关闭",
        66: "待平台确认",
        67: "待客户确认",
        70: "已开票待收款",
    }
    if st is None:
        return "-"
    return labels.get(st, str(st))


def list_invoice_related_orders(order_ids_raw: str) -> list[dict[str, Any]]:
    """关联订单：编号/下单时间/所属公司/状态/总价。"""
    out: list[dict[str, Any]] = []
    for part in str(order_ids_raw or "").split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        row = fetch_one(
            """
            SELECT
                eo.id, eo.order_id AS orderId, eo.order_id AS order_id,
                eo.addTime, eo.totalPrice, eo.order_status AS orderStatus,
                eo.order_type AS orderType, eo.is_online AS isOnline,
                eo.custom_user_id AS customUserId,
                eo.customer_name AS customerName,
                eo.supplier_name AS supplierName,
                IFNULL(u.company_name, '') AS companyName
            FROM experiment_order eo
            LEFT JOIN `user` u ON CAST(u.id AS CHAR) = CAST(eo.supplier_name AS CHAR)
            WHERE eo.id = %(id)s
            LIMIT 1
            """,
            {"id": int(part)},
        )
        if not row:
            continue
        item = to_jsonable(row)
        item["statusLabel"] = _order_status_label(item.get("orderStatus"))
        item["company_name"] = item.get("companyName") or ""
        out.append(item)
    return out


def list_invoice_order_files(order_ids_raw: str) -> list[dict[str, Any]]:
    """订单资料：accessory type=5（对齐 Java getByExpOfId1120）。"""
    return _list_order_accessories(order_ids_raw, acc_types=(5,))


def list_invoice_kp_files(order_ids_raw: str) -> list[dict[str, Any]]:
    """开票凭据：bill/uploadBill 写入的 accessory type=1。"""
    return _list_order_accessories(order_ids_raw, acc_types=(1,))


def _list_order_accessories(order_ids_raw: str, *, acc_types: tuple[int, ...]) -> list[dict[str, Any]]:
    from django.conf import settings

    base = (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")
    type_list = ",".join(str(int(t)) for t in acc_types) or "5"
    out: list[dict[str, Any]] = []
    for part in str(order_ids_raw or "").split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        rows = fetch_all(
            f"""
            SELECT id, name, path, info, ext, type, exp_of_id AS expOfId
            FROM accessory
            WHERE IFNULL(deleteStatus, 0) = 0
              AND IFNULL(type, 0) IN ({type_list})
              AND CAST(exp_of_id AS CHAR) = CAST(%(oid)s AS CHAR)
            ORDER BY id ASC
            """,
            {"oid": int(part)},
        )
        for r in rows:
            item = to_jsonable(r)
            path = str(item.get("path") or "").rstrip("/")
            name = str(item.get("name") or "")
            if path.startswith("http"):
                item["url"] = f"{path}/{name}" if name else path
            elif base and path and name:
                item["url"] = f"{base}/{path.strip('/')}/{name}"
            else:
                item["url"] = f"{path}/{name}" if path and name else (path or name or "")
            item["displayName"] = str(item.get("info") or name or item["url"] or "-")
            out.append(item)
    return out


def list_invoice_bills(order_ids_raw: str) -> list[dict[str, Any]]:
    """开票票据：qd_bill type=1 + 关联附件，供详情展示备注/文件。"""
    from django.conf import settings

    base = (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")
    out: list[dict[str, Any]] = []
    for part in str(order_ids_raw or "").split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        rows = fetch_all(
            """
            SELECT
                b.id, b.add_time AS addTime, b.money, b.mark,
                b.exp_of_id AS ofId, b.accessory_id AS accessoryId,
                a.name AS accessoryName, a.path AS accessoryPath,
                a.info AS accessoryInfo, a.ext AS accessoryExt
            FROM qd_bill b
            LEFT JOIN accessory a ON a.id = b.accessory_id
            WHERE b.type = 1
              AND CAST(b.exp_of_id AS CHAR) = CAST(%(oid)s AS CHAR)
            ORDER BY b.id DESC
            """,
            {"oid": int(part)},
        )
        for r in rows:
            item = to_jsonable(r)
            path = str(item.get("accessoryPath") or "").rstrip("/")
            name = str(item.get("accessoryName") or "")
            if path.startswith("http"):
                item["url"] = f"{path}/{name}" if name else path
            elif base and path and name:
                item["url"] = f"{base}/{path.strip('/')}/{name}"
            else:
                item["url"] = f"{path}/{name}" if path and name else ""
            item["displayName"] = str(
                item.get("accessoryInfo") or name or item.get("url") or ""
            )
            out.append(item)
    return out


def list_invoice_record_logs(apply_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            l.id, l.addTime, l.content, l.user_id AS userId,
            IFNULL(su.true_name, IFNULL(su.user_name, IFNULL(eu.trueName, IFNULL(eu.userName, '')))) AS addusername
        FROM invoice_record_log l
        LEFT JOIN sy_users su ON CAST(su.id AS CHAR) = CAST(l.user_id AS CHAR)
        LEFT JOIN exp_user eu ON CAST(eu.id AS CHAR) = CAST(l.user_id AS CHAR)
        WHERE l.invoice_apply_id = %(aid)s
        ORDER BY l.addTime DESC, l.id DESC
        """,
        {"aid": apply_id},
    )
    return [to_jsonable(r) for r in rows]


def get_invoice_detail(apply_id: int) -> dict[str, Any] | None:
    """对齐 Java invoiceDetail.ajax：obj + files + ofList + logs + 开票票据/凭据。"""
    row = get_invoice_apply(apply_id)
    if not row:
        return None
    order_ids = str(row.get("order_ids") or "")
    of_list = list_invoice_related_orders(order_ids)
    return {
        "obj": row,
        "files": list_invoice_order_files(order_ids),
        "invoiceFiles": list_invoice_kp_files(order_ids),
        "bills": list_invoice_bills(order_ids),
        "ofList": of_list,
        "logs": list_invoice_record_logs(apply_id),
        "ids": order_ids,
        "isSqfp": True,
    }


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


def get_payment_application_detail(apply_id: int) -> dict[str, Any] | None:
    """对齐 Java applyDetail.html：关联订单号、订单资料、操作记录。"""
    from django.conf import settings

    row = get_payment_application(apply_id)
    if not row:
        return None
    base = (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")
    order_ids = [x.strip() for x in str(row.get("orderId") or row.get("order_id") or "").split(",") if x.strip()]
    of_list: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for oid in order_ids:
        of_row = None
        if oid.isdigit():
            of_row = fetch_one(
                "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
                {"oid": int(oid)},
            )
        if not of_row:
            of_row = fetch_one(
                "SELECT id, order_id FROM experiment_order WHERE order_id = %(ono)s LIMIT 1",
                {"ono": oid},
            )
        if of_row:
            of_list.append(to_jsonable(of_row))
            pk = of_row.get("id")
        else:
            continue
        if pk is None:
            continue
        acc_rows = fetch_all(
            """
            SELECT id, path, name, info, ext FROM accessory
            WHERE IFNULL(deleteStatus, 0) = 0
              AND CAST(exp_of_id AS CHAR) = CAST(%(oid)s AS CHAR)
              AND IFNULL(type, 0) = 7
            ORDER BY id ASC
            """,
            {"oid": int(pk)},
        )
        for r in acc_rows or []:
            item = to_jsonable(r)
            path = str(item.get("path") or "").rstrip("/")
            name = str(item.get("name") or "")
            if path.startswith("http"):
                item["url"] = f"{path}/{name}" if name else path
            elif base and path and name:
                item["url"] = f"{base}/{path.strip('/')}/{name}"
            else:
                item["url"] = f"{path}/{name}" if path and name else (path or name or "")
            item["displayName"] = str(item.get("info") or name or item["url"] or "-")
            files.append(item)
    if str(row.get("orderType") or "") == "1":
        try:
            pa_files = fetch_all(
                """
                SELECT id, path, name, info, ext FROM accessory
                WHERE IFNULL(deleteStatus, 0) = 0 AND pa_id = %(pid)s
                ORDER BY id ASC
                """,
                {"pid": apply_id},
            )
        except Exception:
            pa_files = []
        for r in pa_files or []:
            item = to_jsonable(r)
            path = str(item.get("path") or "").rstrip("/")
            name = str(item.get("name") or "")
            if path.startswith("http"):
                item["url"] = f"{path}/{name}" if name else path
            elif base and path and name:
                item["url"] = f"{base}/{path.strip('/')}/{name}"
            else:
                item["url"] = f"{path}/{name}" if path and name else (path or name or "")
            item["displayName"] = str(item.get("info") or name or item["url"] or "-")
            files.append(item)
    try:
        logs = fetch_all(
            """
            SELECT
                l.id, l.addTime, l.content, l.user_id AS userId,
                IFNULL(su.true_name, IFNULL(su.user_name, IFNULL(eu.trueName, IFNULL(eu.userName, '')))) AS addusername
            FROM payment_application_log l
            LEFT JOIN sy_users su ON CAST(su.id AS CHAR) = CAST(l.user_id AS CHAR)
            LEFT JOIN exp_user eu ON CAST(eu.id AS CHAR) = CAST(l.user_id AS CHAR)
            WHERE IFNULL(l.deleteStatus, 0) = 0 AND l.payment_application_id = %(pid)s
            ORDER BY l.addTime ASC, l.id ASC
            """,
            {"pid": apply_id},
        )
    except Exception:
        logs = []
    return {
        "obj": row,
        "ofList": of_list,
        "files": files,
        "logs": [to_jsonable(l) for l in (logs or [])],
    }


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
