from __future__ import annotations

from typing import Any

from django.db import DatabaseError

from apps.admin_service.helpers import normalize_row, page_clause
from apps.core.db_utils import execute, fetch_all, scalar

CALI_TYPE_LABELS = {3: "校准", 4: "维修"}
CALI_STATUS_LABELS = {1: "待处理", 2: "已处理", 3: "已驳回"}


def list_service_applies(
    *,
    cali_type: str = "",
    cali_status: str = "",
    order_id: str = "",
    customer_name: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    try:
        where = """
        WHERE ocf.delete_status = 2
          AND ocf.goods_price * ocf.goods_nums >= 1
          AND (oc.delete_status = 0 OR oc.delete_status IS NULL)
        """
        params: dict[str, Any] = {}
        if cali_type:
            where += " AND oc.cali_type = %(cali_type)s"
            params["cali_type"] = int(cali_type)
        if cali_status:
            where += " AND oc.cali_status = %(cali_status)s"
            params["cali_status"] = int(cali_status)
        if order_id:
            where += " AND ocf.order_id LIKE %(order_id)s"
            params["order_id"] = f"%{order_id}%"
        if customer_name:
            where += " AND uc.name LIKE %(customer_name)s"
            params["customer_name"] = f"%{customer_name}%"

        base_from = """
        FROM order_calibration oc
        JOIN experiment_order_child ocf ON ocf.id = oc.orderform_id
        LEFT JOIN experiment_order eo ON eo.id = ocf.order_form_id
        LEFT JOIN qd_user_company uc ON uc.id = eo.customer_name
        """
        total = int(
            scalar(f"SELECT COUNT(*) {base_from} {where}", params) or 0
        )
        clause, page_params = page_clause(page, page_size)
        rows = fetch_all(
            f"""
            SELECT
                oc.id,
                oc.cali_no,
                oc.cali_type,
                oc.cali_status,
                oc.add_time AS cali_add_time,
                oc.orderform_id,
                ocf.order_id,
                ocf.goods_name,
                ocf.goods_spec,
                ocf.dept,
                uc.name AS customer_name
            {base_from}
            {where}
            ORDER BY oc.add_time DESC
            {clause}
            """,
            {**params, **page_params},
        )
        return [_normalize_service_apply(row) for row in rows], total
    except DatabaseError:
        return [], 0


def update_service_apply(*, record_id: int, cali_status: int, operator_id: str) -> bool:
    try:
        execute(
            """
            UPDATE order_calibration
            SET cali_status = %(cali_status)s,
                update_user_id = %(operator_id)s,
                update_time = NOW()
            WHERE id = %(id)s
            """,
            {
                "id": record_id,
                "cali_status": cali_status,
                "operator_id": operator_id,
            },
        )
        return True
    except DatabaseError:
        return False


def _normalize_service_apply(row: dict[str, Any]) -> dict[str, Any]:
    base = normalize_row(row) or {}
    cali_type = row.get("cali_type")
    cali_status = row.get("cali_status")
    return {
        **base,
        "id": row.get("id"),
        "caliNo": row.get("cali_no"),
        "caliType": cali_type,
        "caliTypeLabel": CALI_TYPE_LABELS.get(int(cali_type or 0), str(cali_type or "")),
        "caliStatus": cali_status,
        "caliStatusLabel": CALI_STATUS_LABELS.get(int(cali_status or 0), str(cali_status or "")),
        "caliAddTime": row.get("cali_add_time"),
        "addTime": row.get("cali_add_time"),
        "orderformId": row.get("orderform_id"),
        "orderId": row.get("order_id"),
        "goodsName": row.get("goods_name"),
        "goodsSpec": row.get("goods_spec"),
        "dept": row.get("dept"),
        "customerName": row.get("customer_name"),
    }
