"""数字化运营中心下钻订单列表 — 对齐 Java companySaleList / expList。"""
from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_all, scalar

ORDER_STATUS_LABEL = {
    0: "已取消",
    5: "订单未发起审核",
    10: "已驳回",
    20: "待审核",
    30: "已审核",
    35: "样品发货",
    36: "样品到货",
    40: "已确认",
    50: "已完成",
    55: "已评价",
    66: "待平台确认",
    67: "待客户确认",
}


def _status_label(v: Any) -> str:
    try:
        return ORDER_STATUS_LABEL.get(int(v), str(v) if v is not None else "-")
    except (TypeError, ValueError):
        return str(v) if v is not None else "-"


def _norm_company_order_type(order_type: str) -> str:
    """公司表点击 data-otype=3 → Java 映射为 6（实验 6|8）。"""
    ot = str(order_type or "").strip()
    return "6" if ot == "3" else ot


def _append_year(where: list[str], params: dict[str, Any], year: str, alias: str = "t") -> None:
    y = str(year or "").strip()
    if not y:
        return
    if "-" in y:
        where.append(f"DATE_FORMAT({alias}.order_time,'%%Y-%%m') = %(ym)s")
        params["ym"] = y
    else:
        where.append(f"DATE_FORMAT({alias}.order_time,'%%Y') = %(yy)s")
        params["yy"] = y


def _common_filters(
    where: list[str],
    params: dict[str, Any],
    *,
    supplier_name: str = "",
    customer_company_id: str = "",
    customer_name: str = "",
    order_id: str = "",
    goods_name: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    sale_user: str = "",
    sale_manager: str = "",
    order_status: str = "",
    year: str = "",
    currency_type: str = "",
    test_type: str = "",
) -> None:
    if supplier_name:
        where.append("CAST(t.supplier_name AS CHAR) = %(supplier_name)s")
        params["supplier_name"] = supplier_name
    if customer_company_id and customer_company_id not in ("0",):
        where.append("com.id = %(customer_company_id)s")
        params["customer_company_id"] = (
            int(customer_company_id) if str(customer_company_id).isdigit() else customer_company_id
        )
    elif customer_company_id == "0":
        where.append("com.id IS NULL")
    if customer_name:
        where.append("com.name LIKE %(customer_name)s")
        params["customer_name"] = f"%{customer_name}%"
    if order_id:
        where.append("t.order_id LIKE %(order_id)s")
        params["order_id"] = f"%{order_id}%"
    if goods_name:
        where.append(
            "EXISTS ("
            " SELECT 1 FROM experiment_order_child ocf"
            " WHERE ocf.order_form_id = t.id"
            "   AND (ocf.goods_name LIKE %(goods_name)s OR IFNULL(ocf.goods_spec,'') LIKE %(goods_name)s)"
            ")"
        )
        params["goods_name"] = f"%{goods_name}%"
    if order_startime:
        where.append("t.order_time >= %(order_startime)s")
        params["order_startime"] = order_startime
    if order_endtime:
        where.append("t.order_time <= %(order_endtime)s")
        params["order_endtime"] = order_endtime
    if sale_user:
        where.append("CAST(t.sale_user AS CHAR) = %(sale_user)s")
        params["sale_user"] = sale_user
    if sale_manager:
        where.append("CAST(t.sale_manager AS CHAR) = %(sale_manager)s")
        params["sale_manager"] = sale_manager
    if order_status != "":
        where.append("t.order_status = %(ui_order_status)s")
        params["ui_order_status"] = (
            int(order_status) if str(order_status).isdigit() else order_status
        )
    if currency_type:
        where.append("t.currency_type = %(currency_type)s")
        params["currency_type"] = (
            int(currency_type) if str(currency_type).isdigit() else currency_type
        )
    if test_type:
        where.append(
            "EXISTS ("
            " SELECT 1 FROM experiment_manage em"
            " WHERE em.id = t.exp_type_id AND em.parent_id = %(test_type)s"
            ")"
        )
        params["test_type"] = int(test_type) if str(test_type).isdigit() else test_type
    _append_year(where, params, year)


def _format_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        st = r.get("order_status")
        inv = r.get("invoiceType")
        out.append(
            {
                **r,
                "orderId": r.get("order_id"),
                "customerName": r.get("customer_company_name") or "",
                "supplierName": r.get("supplier_company_name") or "",
                "managerTrueName": r.get("sale_manager_name") or "",
                "saleUserTrueName": r.get("sale_user_name") or "",
                "totalPrice": r.get("totalPrice"),
                "invoiceLabel": "是" if str(inv) == "1" else "否",
                "orderTime": r.get("order_time"),
                "addTime": r.get("addTime"),
                "orderStatusLabel": _status_label(st),
                "company": {"name": r.get("customer_company_name") or ""},
                "supplierUser": {"company_name": r.get("supplier_company_name") or ""},
                "saleManagerUser": {"userName": r.get("sale_manager_name") or ""},
                "saleUser": {"userName": r.get("sale_user_name") or ""},
            }
        )
    return out


_SELECT = """
SELECT
    t.id,
    t.order_id,
    t.order_type,
    t.order_status,
    t.totalPrice,
    t.invoiceType,
    t.order_time,
    t.addTime,
    t.customer_name,
    t.supplier_name,
    t.sale_manager,
    t.sale_user,
    com.name AS customer_company_name,
    IFNULL(NULLIF(TRIM(su.company_name), ''), su.userName) AS supplier_company_name,
    sm.trueName AS sale_manager_name,
    sy.trueName AS sale_user_name
FROM experiment_order t
LEFT JOIN qd_user_company com ON t.customer_name = com.id
LEFT JOIN `user` su ON CAST(t.supplier_name AS CHAR) = CAST(su.id AS CHAR)
LEFT JOIN sy_users sm ON CAST(t.sale_manager AS CHAR) = CAST(sm.id AS CHAR)
LEFT JOIN sy_users sy ON CAST(t.sale_user AS CHAR) = CAST(sy.id AS CHAR)
"""


def _paginate(
    where_sql: str,
    params: dict[str, Any],
    *,
    extra_join: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    count_sql = (
        "SELECT COUNT(*) FROM experiment_order t "
        f"{extra_join} "
        "LEFT JOIN qd_user_company com ON t.customer_name = com.id "
        f"WHERE {where_sql}"
    )
    total = int(scalar(count_sql, params) or 0)
    offset = max(page - 1, 0) * page_size
    qparams = {**params, "limit": page_size, "offset": offset}
    select = _SELECT.replace(
        "FROM experiment_order t",
        f"FROM experiment_order t {extra_join}",
    )
    rows = fetch_all(
        f"{select} WHERE {where_sql} ORDER BY t.addTime DESC LIMIT %(limit)s OFFSET %(offset)s",
        qparams,
    )
    return _format_rows(rows or []), total


def list_company_sale_orders(
    *,
    company_id: str = "",
    year: str = "",
    type_code: str = "1",
    order_type: str = "3",
    account_type: str = "1",
    customer_name: str = "",
    order_id: str = "",
    goods_name: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    sale_user: str = "",
    sale_manager: str = "",
    order_status: str = "",
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java digitalManage/companySaleList.ajax（实验 otype=3 → order_type 6|8）。"""
    where = ["IFNULL(t.deleteStatus, 0) = 0"]
    params: dict[str, Any] = {}
    ot = _norm_company_order_type(order_type)
    if ot == "6":
        where.append("t.order_type IN (6, 8)")
    elif ot:
        where.append("t.order_type = %(order_type)s")
        params["order_type"] = int(ot) if ot.isdigit() else ot

    tc = str(type_code or "1").strip() or "1"
    if tc == "2":
        where.append("t.order_status IN (5, 20)")
    else:
        where.append("IFNULL(t.order_status, 0) <> 0")

    _common_filters(
        where,
        params,
        supplier_name=str(company_id or "").strip(),
        customer_name=customer_name.strip(),
        order_id=order_id.strip(),
        goods_name=goods_name.strip(),
        order_startime=order_startime.strip(),
        order_endtime=order_endtime.strip(),
        sale_user=sale_user.strip(),
        sale_manager=sale_manager.strip(),
        order_status=order_status.strip(),
        year=year.strip(),
        currency_type=str(account_type or "").strip(),
    )
    return _paginate(" AND ".join(where), params, page=page, page_size=page_size)


def list_exp_orders(
    *,
    list_type: str = "0",
    currency_type: str = "1",
    company_id: str = "",
    supplier_name: str = "",
    year: str = "",
    test_type: str = "",
    sale_user: str = "",
    order_type: str = "6",
    customer_name: str = "",
    order_id: str = "",
    goods_name: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    sale_manager: str = "",
    order_status: str = "",
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java digitalManage/expList.ajax。

    list_type: 0柱图销售额 / 1已收 / 2应收 / 4个人实验总额
    """
    lt = str(list_type or "0").strip() or "0"
    ot = str(order_type or "").strip()
    where = ["IFNULL(t.deleteStatus, 0) = 0"]
    params: dict[str, Any] = {}
    extra_join = ""

    if lt in ("1", "2"):
        where.append("t.order_status IN (30, 40, 50, 35, 45)")
        extra_join = (
            "LEFT JOIN ("
            " SELECT qb.exp_of_id, COUNT(qb.id) AS num"
            " FROM qd_bill qb WHERE qb.type = 2 GROUP BY qb.exp_of_id"
            ") qdtab ON t.id = qdtab.exp_of_id"
        )
        if lt == "1":
            where.append("IFNULL(qdtab.num, 0) > 0")
        else:
            where.append(
                "IFNULL(qdtab.num, 0) < LENGTH(IFNULL(t.collection_time,''))"
                " - LENGTH(REPLACE(IFNULL(t.collection_time,''), ',', '')) + 1"
            )
        if ot in ("6", "8"):
            where.append("t.order_type = %(order_type)s")
            params["order_type"] = int(ot)
        elif ot:
            where.append("t.order_type = %(order_type)s")
            params["order_type"] = int(ot) if ot.isdigit() else ot
        else:
            where.append("t.order_type IN (6, 8)")
        _common_filters(
            where,
            params,
            supplier_name=supplier_name.strip(),
            customer_company_id=company_id.strip(),
            customer_name=customer_name.strip(),
            order_id=order_id.strip(),
            goods_name=goods_name.strip(),
            order_startime=order_startime.strip(),
            order_endtime=order_endtime.strip(),
            sale_user=sale_user.strip(),
            sale_manager=sale_manager.strip(),
            order_status=order_status.strip(),
            year=year.strip(),
            currency_type=currency_type.strip(),
            test_type=test_type.strip(),
        )
    else:
        where.append("IFNULL(t.order_status, 0) > 0")
        if ot in ("6", "8"):
            where.append("t.order_type = %(order_type)s")
            params["order_type"] = int(ot)
        elif ot:
            where.append("t.order_type = %(order_type)s")
            params["order_type"] = int(ot) if ot.isdigit() else ot
        else:
            where.append("t.order_type IN (6, 8)")
        _common_filters(
            where,
            params,
            supplier_name=supplier_name.strip() or company_id.strip(),
            customer_name=customer_name.strip(),
            order_id=order_id.strip(),
            goods_name=goods_name.strip(),
            order_startime=order_startime.strip(),
            order_endtime=order_endtime.strip(),
            sale_user=sale_user.strip(),
            sale_manager=sale_manager.strip(),
            order_status=order_status.strip(),
            year=year.strip(),
            currency_type=currency_type.strip(),
            test_type=test_type.strip(),
        )

    return _paginate(
        " AND ".join(where),
        params,
        extra_join=extra_join,
        page=page,
        page_size=page_size,
    )
