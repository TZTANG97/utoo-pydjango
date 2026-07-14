from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_rows, page_clause
from apps.core.db_utils import fetch_all, scalar


def list_evaluated_orders(
    *,
    order_type: str,
    order_id: str = "",
    customer_name: str = "",
    goods_name: str = "",
    supplier_name: str = "",
    sale_manager: str = "",
    sale_user: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.is_evaluate = 1 AND t.order_type = %(order_type)s"
    params: dict[str, Any] = {"order_type": order_type}
    if order_id:
        where += " AND t.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if customer_name:
        where += " AND quc.name LIKE %(customer_name)s"
        params["customer_name"] = f"%{customer_name}%"
    if goods_name:
        where += (
            " AND EXISTS ("
            " SELECT 1 FROM experiment_order_child oc"
            " WHERE oc.of_id = t.id"
            " AND (oc.goods_name LIKE %(goods_name)s OR oc.experiment_project_name LIKE %(goods_name)s)"
            ")"
        )
        params["goods_name"] = f"%{goods_name}%"
    if supplier_name:
        where += " AND t.supplier_name = %(supplier_name)s"
        params["supplier_name"] = str(supplier_name)
    if sale_manager:
        where += " AND t.sale_manager = %(sale_manager)s"
        params["sale_manager"] = sale_manager
    if sale_user:
        where += " AND t.sale_user = %(sale_user)s"
        params["sale_user"] = sale_user
    if order_startime:
        where += " AND t.order_time >= %(order_startime)s"
        params["order_startime"] = order_startime
    if order_endtime:
        where += " AND t.order_time <= CONCAT(%(order_endtime)s, ' 23:59:59')"
        params["order_endtime"] = order_endtime

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_order t
            LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
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
            t.id,
            t.order_id,
            t.order_status,
            t.totalPrice,
            t.invoiceType,
            t.order_time,
            t.addTime,
            t.is_evaluate,
            t.star,
            t.content,
            t.supplier_name,
            t.sale_manager,
            t.sale_user,
            quc.name AS customerCompanyName,
            su.company_name AS supplierCompanyName,
            sm.true_name AS saleManagerName,
            sm.user_name AS saleManagerUserName,
            sale.true_name AS saleUserName,
            sale.user_name AS saleUserUserName
        FROM experiment_order t
        LEFT JOIN qd_user_company quc ON t.customer_name = quc.id
        LEFT JOIN user su ON su.id = CAST(t.supplier_name AS UNSIGNED)
        LEFT JOIN sy_users sm ON sm.id = t.sale_manager
        LEFT JOIN sy_users sale ON sale.id = t.sale_user
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total
