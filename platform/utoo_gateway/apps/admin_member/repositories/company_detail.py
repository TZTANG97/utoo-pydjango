from __future__ import annotations

from typing import Any

from apps.admin_member.helpers import page_clause
from apps.core.db_utils import fetch_all, scalar


def list_company_contacts(
    *,
    parent_id: int | str,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    if parent_id in (None, ""):
        return [], 0
    where = "WHERE u.deleteStatus = 0 AND u.parent_id = %(parent_id)s"
    params: dict[str, Any] = {"parent_id": parent_id}
    total = int(scalar(f"SELECT COUNT(*) FROM exp_user u {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.trueName, u.company_name, u.company_name AS companyName,
            u.dept, u.job, u.telephone, u.extension,
            u.mobile, u.email, u.zipCode, u.address_info AS addreddInfo, u.parent_id AS parentId,
            u.userType, u.addTime
        FROM exp_user u
        {where}
        ORDER BY u.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_company_invoices(
    *,
    company_id: int | str,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    if company_id in (None, ""):
        return [], 0
    where = "WHERE cil.company_id = %(company_id)s"
    params: dict[str, Any] = {"company_id": company_id}
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM company_invoice_log cil
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            cil.id,
            cil.addTime,
            cil.money,
            cil.company_id AS companyId,
            quc.name AS companyName,
            eo.order_id AS orderId,
            qb.bill_date AS invoiceDate
        FROM company_invoice_log cil
        LEFT JOIN experiment_order eo ON cil.of_id = eo.id
        LEFT JOIN qd_user_company quc ON cil.company_id = quc.id
        LEFT JOIN qd_bill qb ON cil.qd_bill_id = qb.id
        {where}
        ORDER BY COALESCE(qb.bill_date, cil.addTime) DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_company_pay_logs(
    *,
    company_id: int | str,
    pay_type: int | str | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """付款/还款明细：company_pay_log listPage0909。"""
    if company_id in (None, ""):
        return [], 0
    where = "WHERE t.deleteStatus = 0 AND t.company_id = %(company_id)s"
    params: dict[str, Any] = {"company_id": company_id}
    if pay_type not in (None, ""):
        where += " AND t.pay_type = %(pay_type)s"
        params["pay_type"] = pay_type
    total = int(scalar(f"SELECT COUNT(*) FROM company_pay_log t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.addTime,
            t.money,
            t.pay_type AS payType,
            e.order_id AS orderNum,
            e.order_type AS orderType,
            e.id AS eid,
            quc.name AS trueName,
            quc.contract_phone AS contractPhone
        FROM company_pay_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_company_balance_logs(
    *,
    company_id: int | str,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """余额变更明细：listPage910，pay_way in (4,5,6,7)，status=2。"""
    if company_id in (None, ""):
        return [], 0
    where = """
        WHERE t.deleteStatus = 0
          AND t.company_id = %(company_id)s
          AND t.status = 2
          AND t.pay_way IN (4, 5, 6, 7)
    """
    params: dict[str, Any] = {"company_id": company_id}
    total = int(scalar(f"SELECT COUNT(*) FROM company_pay_log t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.addTime,
            t.money,
            t.pay_type AS payType,
            t.pay_way AS payWay,
            e.order_id AS orderNum,
            e.order_type AS orderType,
            u.name AS trueName,
            off.recharge_num AS rechargeNum
        FROM company_pay_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN exp_offline_recharge off ON t.pa_id = off.id
        LEFT JOIN qd_user_company u ON t.company_id = u.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_company_arrears(
    *,
    company_id: int | str,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """欠款明细：expreceivePlanListPc0909 简化版。"""
    if company_id in (None, ""):
        return [], 0
    params: dict[str, Any] = {"company_id": company_id}
    base_where = """
        FROM experiment_order t
        LEFT JOIN (
            SELECT qb.exp_of_id, COUNT(qb.id) AS num
            FROM qd_bill qb
            WHERE qb.type = 2
            GROUP BY qb.exp_of_id
        ) qdtab ON t.id = qdtab.exp_of_id
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        WHERE t.order_type IN (6, 8)
          AND t.order_status > 0
          AND IFNULL(qdtab.num, 0) < (
              LENGTH(IFNULL(t.collection_time, ''))
              - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', ''))
              + 1
          )
          AND t.customer_name = %(company_id)s
          AND t.order_status >= 30
    """
    total = int(scalar(f"SELECT COUNT(DISTINCT t.id) {base_where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.addTime,
            t.order_id,
            t.order_type,
            t.receive_amount,
            quc.name AS userName
        {base_where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_user_invoices(
    *,
    user_id: int | str,
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """个人开票明细：user_invoice_log ∪ company_invoice_log(按手机号)。"""
    if user_id in (None, ""):
        return [], 0
    params: dict[str, Any] = {"user_id": user_id, "mobile": mobile or ""}
    union_sql = """
        SELECT t.id, t.addTime, t.money, t.user_id AS userId,
               qb.bill_date AS invoiceDate, eo.order_id AS orderId,
               eu.trueName AS userName
        FROM user_invoice_log t
        LEFT JOIN exp_user eu ON eu.id = t.user_id
        LEFT JOIN qd_bill qb ON t.qd_bill_id = qb.id
        LEFT JOIN experiment_order eo ON t.of_id = eo.id
        WHERE t.type = 0 AND t.user_id = %(user_id)s
        UNION ALL
        SELECT t.id, t.addTime, t.money, t.company_id AS userId,
               qb.bill_date AS invoiceDate, eo.order_id AS orderId,
               quc.name AS userName
        FROM company_invoice_log t
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        LEFT JOIN qd_bill qb ON t.qd_bill_id = qb.id
        LEFT JOIN experiment_order eo ON t.of_id = eo.id
        WHERE %(mobile)s <> '' AND quc.contract_phone = %(mobile)s
    """
    total = int(scalar(f"SELECT COUNT(*) FROM ({union_sql}) tab", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT * FROM ({union_sql}) tab
        ORDER BY COALESCE(invoiceDate, addTime) DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_user_pay_logs(
    *,
    user_id: int | str,
    mobile: str = "",
    pay_type: int | str | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """付款/还款明细 listPage828。"""
    if user_id in (None, ""):
        return [], 0
    params: dict[str, Any] = {
        "user_id": user_id,
        "mobile": mobile or "",
        "pay_type": pay_type,
    }
    pay_filter = ""
    if pay_type not in (None, ""):
        pay_filter = " AND t.pay_type = %(pay_type)s"
    union_sql = f"""
        SELECT t.id, t.addTime, t.money, e.order_id AS orderNum,
               u.trueName, e.order_type AS orderType, e.id AS eid
        FROM pay_info_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.deleteStatus = 0 AND t.user_id = %(user_id)s
        {pay_filter}
        UNION ALL
        SELECT t.id, t.addTime, t.money, e.order_id AS orderNum,
               quc.name AS trueName, e.order_type AS orderType, e.id AS eid
        FROM company_pay_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        WHERE t.deleteStatus = 0
          AND %(mobile)s <> ''
          AND quc.contract_phone = %(mobile)s
        {pay_filter}
    """
    total = int(scalar(f"SELECT COUNT(*) FROM ({union_sql}) tab", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT * FROM ({union_sql}) tab
        ORDER BY addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_user_balance_logs(
    *,
    user_id: int | str,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """余额变更明细：pay_info_log，pay_way in (4,5,6,7)，status=2。"""
    if user_id in (None, ""):
        return [], 0
    where = """
        WHERE t.deleteStatus = 0
          AND t.user_id = %(user_id)s
          AND t.status = 2
          AND t.pay_way IN (4, 5, 6, 7)
    """
    params: dict[str, Any] = {"user_id": user_id}
    total = int(scalar(f"SELECT COUNT(*) FROM pay_info_log t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.addTime,
            t.money,
            t.pay_type AS payType,
            t.pay_way AS payWay,
            t.order_id,
            t.pa_id AS paId,
            e.order_id AS orderNum,
            e.order_type AS orderType,
            u.trueName,
            off.recharge_num AS rechargeNum
        FROM pay_info_log t
        LEFT JOIN experiment_order e ON t.order_id = e.id
        LEFT JOIN exp_offline_recharge off ON t.pa_id = off.id
        LEFT JOIN exp_user u ON t.user_id = u.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_user_arrears(
    *,
    user_id: int | str,
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """个人欠款明细：expreceivePlanListPc 简化版。"""
    if user_id in (None, ""):
        return [], 0
    params: dict[str, Any] = {"user_id": user_id, "mobile": mobile or ""}
    # 先取 id 再关联姓名，避免 FROM 后再 LEFT JOIN 语法问题
    id_sql = """
        SELECT DISTINCT t.id
        FROM experiment_order t
        LEFT JOIN (
            SELECT qb.exp_of_id, COUNT(qb.id) AS num
            FROM qd_bill qb
            WHERE qb.type = 2
            GROUP BY qb.exp_of_id
        ) qdtab ON t.id = qdtab.exp_of_id
        LEFT JOIN (
            SELECT qb.exp_of_id, COUNT(qb.id) AS num
            FROM exp_online_qd_bill qb
            WHERE qb.type = 2
            GROUP BY qb.exp_of_id
        ) qdtab2 ON t.id = qdtab2.exp_of_id
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        WHERE t.order_type IN (6, 8)
          AND t.order_status > 0
          AND IFNULL(qdtab.num, 0) < (
              LENGTH(IFNULL(t.collection_time, ''))
              - LENGTH(REPLACE(IFNULL(t.collection_time, ''), ',', ''))
              + 1
          )
          AND IFNULL(qdtab2.num, 0) < 1
          AND (
              t.custom_user_id = %(user_id)s
              OR (%(mobile)s <> '' AND quc.contract_phone = %(mobile)s)
          )
          AND t.order_status >= 30
    """
    total = int(scalar(f"SELECT COUNT(*) FROM ({id_sql}) x", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            of.id,
            of.addTime,
            of.order_id,
            of.order_type,
            of.receive_amount,
            COALESCE(eu.trueName, quc.name) AS userName
        FROM experiment_order of
        LEFT JOIN exp_user eu ON of.custom_user_id = eu.id
        LEFT JOIN qd_user_company quc ON of.customer_name = quc.id
        WHERE of.id IN ({id_sql})
        ORDER BY of.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total
