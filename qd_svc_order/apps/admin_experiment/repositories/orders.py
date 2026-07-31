from __future__ import annotations

from typing import Any

from apps.admin_experiment.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

# 对齐 Java mainOrderStatus / experiment_orders_list 状态下拉
ORDER_STATUS_LABEL = {
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

# 实验订单列表筛选用（与 Java 下拉一致）
ORDER_STATUS_FILTER_OPTIONS = [
    {"value": "0", "label": "已取消"},
    {"value": "5", "label": "订单未发起审核"},
    {"value": "10", "label": "已驳回"},
    {"value": "20", "label": "待审核"},
    {"value": "30", "label": "已审核"},
    {"value": "55", "label": "已评价"},
    {"value": "50", "label": "已完成"},
    {"value": "66", "label": "待平台确认"},
    {"value": "67", "label": "待客户确认"},
    {"value": "70", "label": "已开票待收款"},
]

# 实验子订单状态（对齐 Java mainOrderStatusSub + list 下拉）
# 对齐 Java jy.main.js mainOrderStatusSub（实验子/分包子订单）
SUB_ORDER_STATUS_LABEL = {
    0: "已取消",
    5: "订单未发起审核",
    10: "已驳回",
    20: "待审核",
    30: "已审核",
    35: "已下单",
    36: "样品到货",
    37: "样品领用",
    38: "测试中",
    39: "测试完成",
    41: "样品归还",
    42: "样品寄回",
    43: "样品留存",
    45: "已发货",
    46: "已入库",
    50: "已完成",
}

SUB_ORDER_STATUS_FILTER_OPTIONS = [
    {"value": "0", "label": "已取消"},
    {"value": "10", "label": "已驳回"},
    {"value": "20", "label": "待审核"},
    {"value": "30", "label": "已审核"},
    {"value": "35", "label": "已下单"},
    {"value": "45", "label": "已发货"},
    {"value": "50", "label": "已完成"},
]

# 对齐 Java purchasePayStatus
PAY_STATUS_LABEL = {
    0: "未申请",
    32: "待审核",
    33: "已驳回",
    34: "已审核",
    36: "已付款",
    38: "已完成",
}

PAY_STATUS_FILTER_OPTIONS = [
    {"value": "0", "label": "未申请"},
    {"value": "33", "label": "已驳回"},
    {"value": "32", "label": "待审核"},
    {"value": "34", "label": "已审核"},
    {"value": "36", "label": "已付款"},
    {"value": "38", "label": "已完成"},
]

# 对齐 Java jy.main.js childOrderStatus（experiment_order_child 行状态）
CHILD_LINE_STATUS_LABEL = {
    0: "已取消",
    1: "待处理",
    2: "已处理",
    3: "已驳回",
    10: "生产中",
    15: "样品到货",
    16: "测试中",
    17: "测试完成",
    20: "运输中",
    30: "已签收",
    36: "样品到货",
    37: "样品领用",
    38: "测试中",
    39: "测试完成",
    40: "已验收",
    41: "样品归还",
    42: "样品寄回",
    43: "样品留存",
    44: "样品报废",
    50: "已完成",
}


def _status_label(v: Any) -> str:
    try:
        return ORDER_STATUS_LABEL.get(int(v), str(v) if v is not None else "-")
    except (TypeError, ValueError):
        return str(v or "-")


def _us_exchange_rate() -> float | None:
    """读取 account_setting.us_exchange_rate；无表/无值时返回 None（按原币）。"""
    try:
        val = scalar("SELECT us_exchange_rate FROM account_setting LIMIT 1", {}, None)
        if val is None:
            return None
        rate = float(val)
        return rate if rate > 0 else None
    except Exception:
        return None


def _to_rmb(amount: Any, currency_type: Any, rate: float | None) -> float:
    try:
        money = float(amount or 0)
    except (TypeError, ValueError):
        money = 0.0
    try:
        ct = int(currency_type or 1)
    except (TypeError, ValueError):
        ct = 1
    if ct == 2 and rate is not None:
        return money * rate
    return money


def _attach_subcontract_gross_profit(rows: list[dict[str, Any]]) -> None:
    """简化毛利：本单 RMB 总价 − Σ(order_type=9 子单总价，按 RMB)。"""
    if not rows:
        return
    rate = _us_exchange_rate()
    ids = [r["id"] for r in rows if r.get("id") is not None]
    child_cost: dict[Any, float] = {i: 0.0 for i in ids}
    if ids:
        placeholders = ", ".join(f"%(pid{i})s" for i in range(len(ids)))
        params = {f"pid{i}": ids[i] for i in range(len(ids))}
        child_rows = fetch_all(
            f"""
            SELECT parent_id AS parentId,
                   IFNULL(currency_type, 1) AS currencyType,
                   SUM(IFNULL(totalPrice, 0)) AS childTotal
            FROM experiment_order
            WHERE IFNULL(deleteStatus, 0) = 0
              AND order_type = '9'
              AND parent_id IN ({placeholders})
            GROUP BY parent_id, IFNULL(currency_type, 1)
            """,
            params,
        )
        for cr in child_rows:
            pid = cr.get("parentId")
            if pid not in child_cost:
                continue
            child_cost[pid] += _to_rmb(cr.get("childTotal"), cr.get("currencyType"), rate)
    for r in rows:
        parent_rmb = _to_rmb(r.get("totalPrice"), r.get("currencyType"), rate)
        profit = round(parent_rmb - child_cost.get(r.get("id"), 0.0), 2)
        r["grossProfit"] = profit
        r["maoli"] = profit


def list_orders(
    *,
    order_type: str | int,
    order_id: str = "",
    company_name: str = "",
    supplier_name: str = "",
    sale_manager: str = "",
    sale_user: str = "",
    order_status: str = "",
    goods_name: str = "",
    order_start: str = "",
    order_end: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """实验订单列表（对齐 Java list_dpt / listPagesdpt 主字段）。"""
    where = (
        "WHERE IFNULL(t.deleteStatus, 0) = 0"
        " AND t.order_type = %(order_type)s"
        " AND t.order_status > 0"
    )
    params: dict[str, Any] = {"order_type": str(order_type)}
    if order_id:
        where += " AND t.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if company_name:
        where += " AND q.name LIKE %(company_name)s"
        params["company_name"] = f"%{company_name}%"
    if supplier_name:
        where += " AND t.supplier_name = %(supplier_name)s"
        params["supplier_name"] = supplier_name
    if sale_manager:
        where += " AND t.sale_manager = %(sale_manager)s"
        params["sale_manager"] = sale_manager
    if sale_user:
        where += " AND t.sale_user = %(sale_user)s"
        params["sale_user"] = sale_user
    if order_status == "55":
        where += " AND IFNULL(t.is_evaluate, 0) = 1"
    elif order_status == "70":
        where += " AND t.invoiceType = 1"
    elif order_status == "0":
        # 显式查已取消：去掉默认 order_status > 0
        where = where.replace(" AND t.order_status > 0", " AND t.order_status = 0")
    elif order_status:
        where += " AND t.order_status = %(order_status)s"
        params["order_status"] = order_status
    if order_start:
        where += " AND DATE(t.order_time) >= %(order_start)s"
        params["order_start"] = order_start
    if order_end:
        where += " AND DATE(t.order_time) <= %(order_end)s"
        params["order_end"] = order_end
    if goods_name:
        where += """
          AND EXISTS (
            SELECT 1 FROM experiment_order_child ocf
            WHERE ocf.order_form_id = t.id
              AND IFNULL(ocf.delete_status, 2) <> 1
              AND (ocf.goods_name LIKE %(goods_name)s OR ocf.goods_spec LIKE %(goods_name)s)
          )
        """
        params["goods_name"] = f"%{goods_name}%"

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_order t
            LEFT JOIN qd_user_company q ON t.customer_name = q.id
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
            t.id, t.addTime, t.order_id AS orderId, t.order_type AS orderType,
            t.order_status AS orderStatus, t.totalPrice AS totalPrice,
            t.invoiceType AS invoiceType, t.order_time AS orderTime,
            t.collection_time AS collectionTime,
            t.currency_type AS currencyType,
            q.name AS customerName,
            u.company_name AS supplierName,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName,
            IFNULL(bill_kp.kpje, 0) AS invoiceAmount,
            IFNULL(bill_sk.skje, 0) AS receiveAmount,
            IFNULL(bill_kp.num, 0) AS kpCount,
            IFNULL(bill_sk.num, 0) AS skCount,
            p.order_id AS parentOrderId
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN `user` u ON t.supplier_name = u.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        LEFT JOIN (
            SELECT exp_of_id, SUM(money) kpje, COUNT(id) num
            FROM qd_bill WHERE type = 1 GROUP BY exp_of_id
        ) bill_kp ON t.id = bill_kp.exp_of_id
        LEFT JOIN (
            SELECT exp_of_id, SUM(money) skje, COUNT(id) num
            FROM qd_bill WHERE type = 2 GROUP BY exp_of_id
        ) bill_sk ON t.id = bill_sk.exp_of_id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        # 对齐 Java list_dpt 收款/开票派生状态
        status = r.get("orderStatus")
        try:
            st = int(status) if status is not None else None
        except (TypeError, ValueError):
            st = None
        collec = str(r.get("collectionTime") or "")
        collec_parts = [x for x in collec.split(",") if x.strip()] if collec else []
        sk_count = int(r.get("skCount") or 0)
        kp_count = int(r.get("kpCount") or 0)
        invoice_type = r.get("invoiceType")
        total_price = r.get("totalPrice") or 0
        invoice_amount = r.get("invoiceAmount") or 0
        skflag = len(collec_parts) == sk_count and sk_count > 0
        kpflag = False
        try:
            if int(invoice_type or 0) == 1:
                if float(invoice_amount) >= float(total_price):
                    kpflag = True
                elif kp_count > len(collec_parts):
                    kpflag = True
        except (TypeError, ValueError):
            pass
        if st not in (50, 55):
            if skflag and not kpflag:
                st = 41
            elif (not skflag) and kpflag:
                st = 42
            elif skflag and kpflag:
                st = 41
            if st is not None:
                r["orderStatus"] = st
        r["orderStatusLabel"] = _status_label(r.get("orderStatus"))
        r["companyName"] = r.get("customerName") or "-"
        r["customerName"] = r.get("customerName") or ""
        r["supplierName"] = r.get("supplierName") or ""
        r["saleManager"] = str(r.get("managerName") or r.get("managerTrueName") or "").strip()
        r["saleUser"] = str(r.get("saleUserName") or r.get("saleUserTrueName") or "").strip()
        r["invoiceLabel"] = "是" if str(r.get("invoiceType") or "") == "1" else "否"
        ot = r.get("orderTime") or r.get("addTime")
        r["orderTime"] = str(ot)[:10] if ot else ""
        at = r.get("addTime")
        r["addTime"] = str(at)[:19] if at else ""
    if str(order_type) == "8":
        _attach_subcontract_gross_profit(rows)
    return rows, total


def _sub_status_label(v: Any) -> str:
    try:
        return SUB_ORDER_STATUS_LABEL.get(int(v), str(v) if v is not None else "-")
    except (TypeError, ValueError):
        return str(v or "-")


def _pay_status_label(v: Any) -> str:
    try:
        return PAY_STATUS_LABEL.get(int(v), str(v) if v is not None else "-")
    except (TypeError, ValueError):
        return str(v or "-")


def _child_line_status_label(v: Any) -> str:
    try:
        return CHILD_LINE_STATUS_LABEL.get(int(v), str(v) if v is not None else "-")
    except (TypeError, ValueError):
        return str(v or "-")


def list_sub_orders(
    *,
    order_type: str | int = "10",
    order_id: str = "",
    parent_order_id: str = "",
    customer_name: str = "",
    sale_manager: str = "",
    sale_user: str = "",
    order_status: str = "",
    pay_status: str = "",
    test_user_id: str = "",
    is_confirm: str = "",
    finish_start: str = "",
    finish_end: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java listPagesdpt1024：order_type=10 实验子订单 / =9 实验分包子订单。"""
    ot = str(order_type or "10")
    if ot not in ("9", "10"):
        ot = "10"
    where = (
        "WHERE IFNULL(t.deleteStatus, 0) = 0 "
        "AND t.order_type = %(order_type)s AND t.order_status > 0"
    )
    params: dict[str, Any] = {"order_type": ot}
    if order_id:
        where += " AND t.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if parent_order_id:
        where += " AND p.order_id LIKE %(parent_order_id)s"
        params["parent_order_id"] = f"%{parent_order_id}%"
    if customer_name:
        # Java stockCompanyName：按客户企业 quc.name LIKE（非进货公司字段）
        where += " AND q.name LIKE %(customer_name)s"
        params["customer_name"] = f"%{customer_name}%"
    if sale_manager:
        where += " AND t.sale_manager = %(sale_manager)s"
        params["sale_manager"] = sale_manager
    if sale_user:
        where += " AND t.sale_user = %(sale_user)s"
        params["sale_user"] = sale_user
    if order_status:
        where += " AND t.order_status = %(order_status)s"
        params["order_status"] = order_status
    if pay_status != "":
        where += " AND t.pay_status = %(pay_status)s"
        params["pay_status"] = pay_status
    if is_confirm != "":
        where += " AND IFNULL(t.is_confirm, 0) = %(is_confirm)s"
        params["is_confirm"] = is_confirm
    if test_user_id:
        where += """
          AND EXISTS (
            SELECT 1 FROM exp_qd_purchase_order_child poc
            JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
            WHERE poc.purchase_order_id = t.id AND ocf.test_user_id = %(test_user_id)s
          )
        """
        params["test_user_id"] = test_user_id
    if finish_start or finish_end:
        # Java：按 order_log「测试完成」最早时间过滤
        where += """
          AND EXISTS (
            SELECT 1 FROM experiment_order_log log
            WHERE log.of_id = t.id AND log.log_info LIKE %(finish_kw)s
        """
        params["finish_kw"] = "%测试完成%"
        if finish_start:
            where += " AND log.addTime >= %(finish_start)s"
            params["finish_start"] = finish_start
        if finish_end:
            where += " AND log.addTime <= %(finish_end)s"
            params["finish_end"] = f"{finish_end} 23:59:59"
        where += ")"

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_order t
            LEFT JOIN experiment_order p ON t.parent_id = p.id
            LEFT JOIN qd_user_company q ON t.customer_name = q.id
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
            t.id, t.addTime, t.order_id AS orderId, t.order_status AS orderStatus,
            t.order_time AS orderTime, t.is_confirm AS isConfirm,
            t.purchase_type AS purchaseType, t.totalPrice AS totalPrice,
            t.pay_status AS payStatus,
            q.name AS customerName,
            qs.name AS stockCompanyName,
            p.order_id AS parentOrderId,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName,
            tu.user_name AS testName, tu.true_name AS testTrueName
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN qd_user_company qs ON t.stock_company_name = qs.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        LEFT JOIN (
            SELECT poc.purchase_order_id, MIN(ocf.test_user_id) AS test_user_id
            FROM exp_qd_purchase_order_child poc
            LEFT JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
            GROUP BY poc.purchase_order_id
        ) tab2 ON t.id = tab2.purchase_order_id
        LEFT JOIN sy_users tu ON tab2.test_user_id = tu.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        r["orderStatusLabel"] = _sub_status_label(r.get("orderStatus"))
        r["payStatusLabel"] = _pay_status_label(r.get("payStatus"))
        cust = r.get("customerName") or ""
        stock = r.get("stockCompanyName") or ""
        r["customerName"] = cust
        r["stockCompanyName"] = stock
        # type=9 列表列「进货公司」；type=10 用客户名称
        r["companyName"] = (stock or cust) if ot == "9" else (cust or "-")
        if ot == "9" and not r["companyName"]:
            r["companyName"] = "-"
        parent = r.get("parentOrderId")
        if not parent:
            pt = str(r.get("purchaseType") or "")
            parent = "自主发起" if pt == "1" else ("自主发起配件采购" if pt == "2" else "")
        r["parentOrderId"] = parent or ""
        r["saleManager"] = str(r.get("managerName") or r.get("managerTrueName") or "").strip()
        r["saleUser"] = str(r.get("saleUserName") or r.get("saleUserTrueName") or "").strip()
        r["testName"] = str(r.get("testName") or r.get("testTrueName") or "").strip()
        conf = r.get("isConfirm")
        try:
            conf_i = int(conf) if conf is not None else 0
        except (TypeError, ValueError):
            conf_i = 0
        r["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
        otm = r.get("orderTime") or r.get("addTime")
        r["orderTime"] = str(otm)[:10] if otm else ""
    return rows, total


# Java 抢单池哨兵值：experiment_order_child.test_user_id = '22' 表示待抢
GRAB_POOL_TEST_USER_ID = "22"


def list_grab_orders(
    *,
    order_id: str = "",
    source_order: str = "",
    company_name: str = "",
    sale_manager: str = "",
    sale_user: str = "",
    order_status: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java qd_list_dpt / listPagesdpt0419：type=10 + 子单 test_user_id=22。"""
    where = """
        WHERE t.order_status > 0 AND t.order_type = '10'
          AND EXISTS (
            SELECT 1
            FROM exp_qd_purchase_order_child poc
            JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
            WHERE poc.purchase_order_id = t.id
              AND ocf.test_user_id = %(pool_uid)s
              AND ocf.order_status <= 36
              AND IFNULL(ocf.delete_status, 2) <> 1
          )
    """
    params: dict[str, Any] = {"pool_uid": GRAB_POOL_TEST_USER_ID}
    if order_id:
        where += " AND t.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if source_order:
        where += " AND p.order_id LIKE %(source_order)s"
        params["source_order"] = f"%{source_order}%"
    if company_name:
        where += " AND (q.name LIKE %(company_name)s OR qs.name LIKE %(company_name)s)"
        params["company_name"] = f"%{company_name}%"
    if sale_manager:
        where += " AND (sm.user_name LIKE %(sale_manager)s OR sm.true_name LIKE %(sale_manager)s OR t.sale_manager = %(sale_manager_eq)s)"
        params["sale_manager"] = f"%{sale_manager}%"
        params["sale_manager_eq"] = sale_manager
    if sale_user:
        where += " AND (su.user_name LIKE %(sale_user)s OR su.true_name LIKE %(sale_user)s OR t.sale_user = %(sale_user_eq)s)"
        params["sale_user"] = f"%{sale_user}%"
        params["sale_user_eq"] = sale_user
    if order_status:
        where += " AND t.order_status = %(order_status)s"
        params["order_status"] = order_status

    total = int(
        scalar(
            f"""
            SELECT COUNT(DISTINCT t.id)
            FROM experiment_order t
            LEFT JOIN experiment_order p ON t.parent_id = p.id
            LEFT JOIN qd_user_company q ON t.customer_name = q.id
            LEFT JOIN qd_user_company qs ON t.stock_company_name = qs.id
            LEFT JOIN sy_users sm ON t.sale_manager = sm.id
            LEFT JOIN sy_users su ON t.sale_user = su.id
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
            t.id, t.addTime, t.order_id AS orderId, t.order_status AS orderStatus,
            t.order_time AS orderTime, t.purchase_type AS purchaseType,
            qs.name AS stockCompanyName, q.name AS companyName,
            p.order_id AS parentOrderId,
            sm.user_name AS saleManagerName, sm.true_name AS saleManagerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN qd_user_company qs ON t.stock_company_name = qs.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        r["orderStatusLabel"] = _status_label(r.get("orderStatus"))
        r["companyName"] = r.get("companyName") or r.get("stockCompanyName") or "-"
        r["saleManager"] = str(r.get("saleManagerTrueName") or r.get("saleManagerName") or "-")
        r["saleUser"] = str(r.get("saleUserTrueName") or r.get("saleUserName") or "-")
        r["parentOrderId"] = r.get("parentOrderId") or (
            "自主发起" if str(r.get("purchaseType") or "") == "1" else r.get("parentOrderId")
        )
    return rows, total


def grab_order(*, order_id: int, user_id: str) -> tuple[bool, str]:
    """对齐 Java competitionOrder：ofId 为子单 experiment_order_child.id。"""
    child = fetch_one(
        """
        SELECT id, test_user_id AS testUserId, order_status AS orderStatus
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not child:
        return False, "子单不存在"
    if str(child.get("testUserId") or "") != GRAB_POOL_TEST_USER_ID:
        return False, "该子单不可抢或已被抢"
    try:
        st = int(child.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    if st > 36:
        return False, "该子单当前状态不可抢"
    execute(
        "UPDATE experiment_order_child SET test_user_id = %(uid)s WHERE id = %(id)s",
        {"uid": user_id, "id": child["id"]},
    )
    try:
        execute(
            """
            UPDATE statistic_experiment_finish
            SET test_user_id = %(uid)s
            WHERE child_id = %(cid)s
            """,
            {"uid": user_id, "cid": child["id"]},
        )
    except Exception:
        pass
    return True, "抢单成功！"


def _is_child_order_type(order_type: Any) -> bool:
    return str(order_type or "") in ("9", "10")


def get_order(order_id: int) -> dict[str, Any] | None:
    """对齐 Java orderdetail.htm 主单头字段（admin 侧精简版）。"""
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.order_id AS orderId, t.order_type AS orderType,
            t.order_status AS orderStatus, t.totalPrice AS totalPrice,
            t.order_time AS orderTime, t.is_confirm AS isConfirm,
            t.stock_company_name AS stockCompanyName, t.mark, t.msg AS msg,
            t.invoiceType AS invoiceType, t.currency_type AS currencyType,
            t.collection_time AS collectionTime, t.parent_id AS parentId,
            t.purchase_type AS purchaseType, t.delivery_time AS deliveryTime,
            t.send_address AS shipAddress, t.addressee_name AS shipUser,
            t.addressee_mobile AS shipPhone, t.pay_status AS payStatus,
            t.pay_times AS payTimes, t.pay_way AS payWay, t.mobile AS mobile,
            t.is_video AS isVideo, t.cost_settle AS costSettle,
            t.is_online AS isOnline, t.is_yyd AS isYyd, t.is_evaluate AS isEvaluate,
            t.reverso_context AS reversoContext,
            t.consultid AS consultId,
            t.sale_scale AS saleScale,
            t.test_manager AS testManagerId,
            IFNULL(bill_cnt.kpCnt, 0) AS invoiceBillCount,
            IFNULL(bill_cnt.skCnt, 0) AS receiveBillCount,
            t.user_scale_info AS userScaleInfo, t.scale_info AS scaleInfo,
            t.salecb_user_scale_info AS salecbUserScaleInfo,
            t.related_order_num AS relatedOrderNum,
            q.name AS companyName,
            u.company_name AS supplierName,
            sm.user_name AS saleManagerName, sm.true_name AS saleManagerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName,
            au.user_name AS addUserName, au.true_name AS addUserTrueName,
            tm.user_name AS testManagerName, tm.true_name AS testManagerTrueName,
            pt.name AS payWayName, pt.scale_val AS payScaleVal,
            p.id AS parentPkId, p.order_id AS parentOrderId, p.order_type AS parentOrderType,
            p.mobile AS parentMobile, p.reverso_context AS parentReversoContext,
            p.send_address AS parentSendAddress, p.is_video AS parentIsVideo,
            tc.name AS testClassName,
            IFNULL(bill_kp.kpje, 0) AS invoiceAmount,
            IFNULL(bill_sk.skje, 0) AS receiveAmount,
            tu.user_name AS testName, tu.true_name AS testTrueName
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN `user` u ON t.supplier_name = u.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        LEFT JOIN sy_users au ON t.add_user_id = au.id
        LEFT JOIN sy_users tm ON t.test_manager = tm.id
        LEFT JOIN qd_consume_paytype pt ON t.pay_way = pt.id
        LEFT JOIN experiment_manage tc ON t.class_id = tc.id
        LEFT JOIN (
            SELECT exp_of_id, SUM(money) kpje FROM qd_bill WHERE type = 1 GROUP BY exp_of_id
        ) bill_kp ON t.id = bill_kp.exp_of_id
        LEFT JOIN (
            SELECT exp_of_id, SUM(money) skje FROM qd_bill WHERE type = 2 GROUP BY exp_of_id
        ) bill_sk ON t.id = bill_sk.exp_of_id
        LEFT JOIN (
            SELECT
                exp_of_id,
                SUM(CASE WHEN type = 1 THEN 1 ELSE 0 END) AS kpCnt,
                SUM(CASE WHEN type = 2 THEN 1 ELSE 0 END) AS skCnt
            FROM qd_bill
            GROUP BY exp_of_id
        ) bill_cnt ON t.id = bill_cnt.exp_of_id
        LEFT JOIN (
            SELECT poc.purchase_order_id, MIN(ocf.test_user_id) AS test_user_id
            FROM exp_qd_purchase_order_child poc
            LEFT JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
            GROUP BY poc.purchase_order_id
        ) tab2 ON t.id = tab2.purchase_order_id
        LEFT JOIN sy_users tu ON tab2.test_user_id = tu.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not row:
        return None
    ot = str(row.get("orderType") or "")
    row["orderStatusLabel"] = (
        _sub_status_label(row.get("orderStatus"))
        if _is_child_order_type(ot)
        else _status_label(row.get("orderStatus"))
    )
    q_name = str(row.get("companyName") or "").strip()
    stock = str(row.get("stockCompanyName") or "").strip()
    row["stockCompanyName"] = stock or "-"
    if ot == "9":
        # 分包子单：公司名单独展示，不把 stock 冒充客户
        row["companyName"] = q_name or "-"
        row["customerName"] = q_name or "-"
    else:
        row["companyName"] = q_name or stock or "-"
        row["customerName"] = "" if row["companyName"] == "-" else row["companyName"]
    row["supplierName"] = row.get("supplierName") or ""
    # type=9 Java 展示 userName；其它优先真实姓名
    if ot == "9":
        row["saleManager"] = str(row.get("saleManagerName") or row.get("saleManagerTrueName") or "-")
        row["saleUser"] = str(row.get("saleUserName") or row.get("saleUserTrueName") or "-")
        row["addUser"] = str(row.get("addUserName") or row.get("addUserTrueName") or "-")
        row["testManager"] = str(row.get("testManagerName") or row.get("testManagerTrueName") or "-") or "-"
    else:
        row["saleManager"] = str(row.get("saleManagerTrueName") or row.get("saleManagerName") or "-")
        row["saleUser"] = str(row.get("saleUserTrueName") or row.get("saleUserName") or "-")
        row["addUser"] = str(row.get("addUserTrueName") or row.get("addUserName") or "-")
        row["testManager"] = str(
            row.get("testManagerTrueName") or row.get("testManagerName") or "-"
        ).strip() or "-"
    row["testName"] = str(row.get("testTrueName") or row.get("testName") or "").strip()
    row["payWayName"] = str(row.get("payWayName") or "").strip() or "-"
    try:
        is_yyd_flag = int(row.get("isYyd") or 0)
    except (TypeError, ValueError):
        is_yyd_flag = 0
    row["isYydLabel"] = "已生成" if is_yyd_flag == 1 else "未生成"
    # 预约单（ServiceConsult）
    row["appointmentNo"] = ""
    row["appointmentId"] = None
    consult_id = row.get("consultId")
    if consult_id not in (None, "", 0, "0"):
        try:
            consult = fetch_one(
                """
                SELECT id, order_id AS appointmentNo, status AS appointmentStatus,
                       addTime, mobile AS appointmentMobile, company_name AS appointmentCompany
                FROM service_consult
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": consult_id},
            )
            if consult:
                row["appointmentId"] = consult.get("id")
                row["appointmentNo"] = str(consult.get("appointmentNo") or consult.get("id") or "")
                row["appointmentStatus"] = consult.get("appointmentStatus")
                row["appointmentMobile"] = consult.get("appointmentMobile") or ""
                row["appointmentCompany"] = consult.get("appointmentCompany") or ""
        except Exception:
            pass
    parent = row.get("parentOrderId")
    if not parent and _is_child_order_type(ot):
        pt = str(row.get("purchaseType") or "")
        parent = "自主发起" if pt == "1" else ("自主发起配件采购" if pt == "2" else "")
    row["parentOrderId"] = parent or ""
    try:
        conf_i = int(row.get("isConfirm")) if row.get("isConfirm") is not None else 0
    except (TypeError, ValueError):
        conf_i = 0
    row["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
    row["invoiceLabel"] = "是" if str(row.get("invoiceType") or "") == "1" else "否"
    ct = row.get("currencyType")
    try:
        ct_i = int(ct) if ct is not None else 1
    except (TypeError, ValueError):
        ct_i = 1
    row["currencyLabel"] = "美金" if ct_i == 2 else "人民币"
    for key in ("addTime", "orderTime", "deliveryTime"):
        v = row.get(key)
        if v:
            row[key] = str(v)[:19] if key == "addTime" else str(v)[:10]
        else:
            row[key] = ""
    if not row.get("orderTime"):
        row["orderTime"] = (row.get("addTime") or "")[:10]
    row["isVideoLabel"] = "是" if str(row.get("isVideo") or "") in ("1", "true") else "否"
    # type=9：样品回收/电话/寄回地址/云视频取自关联主单（对齐 Java orderParent）
    if ot == "9":
        rev = row.get("parentReversoContext")
        if rev is None:
            rev = row.get("reversoContext")
        row["reversoLabel"] = "是" if str(rev or "") == "1" else "否"
        phone = (
            str(row.get("parentMobile") or "").strip()
            or str(row.get("mobile") or "").strip()
            or str(row.get("shipPhone") or "").strip()
        )
        row["contactPhone"] = phone or "-"
        if not str(row.get("shipAddress") or "").strip():
            row["shipAddress"] = str(row.get("parentSendAddress") or "").strip()
        pv = row.get("parentIsVideo")
        if pv is not None and str(pv).strip() != "":
            row["isVideoLabel"] = "是" if str(pv) in ("1", "true") else "否"
    else:
        rev = row.get("reversoContext")
        row["reversoLabel"] = "是" if str(rev or "") == "1" else "否"
        row["contactPhone"] = str(row.get("mobile") or row.get("shipPhone") or "").strip() or "-"
    row["msg"] = str(row.get("msg") or row.get("mark") or "").strip()
    # 预计付款时间/金额（对齐 Java collectionTimes）
    expect_pay: list[dict[str, Any]] = []
    coll_raw = str(row.get("collectionTime") or "").strip()
    if coll_raw:
        slots = [p.strip() for p in coll_raw.split(",") if p.strip()]
        scales_raw = str(row.get("payScaleVal") or "").strip()
        scales = [p.strip() for p in scales_raw.split(",") if p.strip()] if scales_raw else []
        try:
            total_pay = float(row.get("totalPrice") or 0)
        except (TypeError, ValueError):
            total_pay = 0.0
        for i, tm in enumerate(slots):
            try:
                scale = float(scales[i]) if i < len(scales) else (100.0 if len(slots) == 1 else 0.0)
            except (TypeError, ValueError):
                scale = 0.0
            price = round(total_pay * scale / 100.0, 2)
            expect_pay.append({"time": tm[:10] if len(tm) >= 10 else tm, "price": f"{price:.2f}"})
    row["expectPayList"] = expect_pay
    try:
        st = int(row.get("orderStatus")) if row.get("orderStatus") is not None else -1
    except (TypeError, ValueError):
        st = -1
    ot = str(row.get("orderType") or "")
    parent_kind = ot in ("6", "8")
    child_kind = ot in ("9", "10")
    try:
        cost_settle = int(row.get("costSettle") or 0)
    except (TypeError, ValueError):
        cost_settle = 0
    row["costSettle"] = cost_settle
    row["costSettleLabel"] = "已结清" if cost_settle == 1 else "未结清"
    # 对齐 Java 详情按钮显隐（管理端不做角色细分时按状态）
    row["canCancel"] = (st in (5, 10, 20, 30, 67) and parent_kind) or (
        child_kind and st not in (0, 50)
    )
    if ot == "9":
        row["canCancel"] = st in (5, 10)
    row["canSubmitAudit"] = st == 5
    row["canWithdrawAudit"] = st == 20
    row["canAudit"] = st == 20
    try:
        inv_bill_cnt = int(row.get("invoiceBillCount") or 0)
        recv_bill_cnt = int(row.get("receiveBillCount") or 0)
    except (TypeError, ValueError):
        inv_bill_cnt, recv_bill_cnt = 0, 0
    # Java isDisabled=true 才显示「编辑订单」；有开票/收款票、主单已分钱、子行 is_sure=1 则禁编
    edit_allowed_by_bill = inv_bill_cnt <= 0 and recv_bill_cnt <= 0
    can_edit = False
    if parent_kind:
        can_edit = st in (5, 10, 20) and edit_allowed_by_bill
    elif ot == "9":
        # experimentsub/purchase_order_detail：status!=0 && isDisabled
        can_edit = st != 0 and edit_allowed_by_bill
    elif ot == "10":
        # experiment/sub/purchase_order_detail：status∉{0,50} && isDisabled
        can_edit = st not in (0, 50) and edit_allowed_by_bill
    if can_edit and ot in ("9", "10"):
        parent_pk = row.get("parentId") or row.get("parentPkId")
        if parent_pk:
            split_cnt = int(
                scalar(
                    """
                    SELECT COUNT(*) FROM qd_bill
                    WHERE type = 2
                      AND exp_of_id = %(pid)s
                      AND IFNULL(is_split, 0) = 1
                    """,
                    {"pid": parent_pk},
                    0,
                )
                or 0
            )
            if split_cnt > 0:
                can_edit = False
        if can_edit:
            sure_cnt = int(
                scalar(
                    """
                    SELECT COUNT(*) FROM experiment_order_child c
                    WHERE (
                        c.order_form_id = %(oid)s
                        OR EXISTS (
                            SELECT 1 FROM exp_qd_purchase_order_child poc
                            WHERE poc.purchase_order_id = %(oid)s
                              AND poc.order_child_id = c.id
                        )
                    )
                      AND IFNULL(c.delete_status, 2) <> 1
                      AND IFNULL(c.is_sure, 0) = 1
                    """,
                    {"oid": row["id"]},
                    0,
                )
                or 0
            )
            if sure_cnt > 0:
                can_edit = False
    row["canEdit"] = can_edit
    row["canCostSettle"] = parent_kind and cost_settle == 0 and st != 0
    # Java isfcbl：sale_scale 已设置则隐藏「调整分成比例」
    sale_scale_raw = row.get("saleScale")
    has_sale_scale = sale_scale_raw is not None and str(sale_scale_raw).strip() not in ("", "None")
    row["canShareRatio"] = parent_kind and st in (5, 20, 30, 67) and not has_sale_scale
    row["canAddRelated"] = parent_kind
    # Java 子订单详情无「更多信息」按钮；主单保留
    row["canMoreInfo"] = parent_kind
    # Java isSave：仅实验子订单 type=10，且 status∉{0,50}
    row["canSaveFinish"] = ot == "10" and st not in (0, 50)
    row["canCreateChild"] = parent_kind and st not in (0,)
    row["canConfirmDone"] = False
    # type=6/8 开票收款（对齐 Java：status∈{30,50} + viewKp/viewRecive/sureRecive）
    try:
        is_online = int(row.get("isOnline") or 0)
    except (TypeError, ValueError):
        is_online = 0
    try:
        is_yyd = int(row.get("isYyd") or 0)
    except (TypeError, ValueError):
        is_yyd = 0
    try:
        inv_type = int(row.get("invoiceType") or 0)
    except (TypeError, ValueError):
        inv_type = 0
    try:
        total_p = float(row.get("totalPrice") or 0)
        inv_amt = float(row.get("invoiceAmount") or 0)
        recv_amt = float(row.get("receiveAmount") or 0)
    except (TypeError, ValueError):
        total_p, inv_amt, recv_amt = 0.0, 0.0, 0.0
    try:
        pay_st = int(row.get("payStatus") or 0)
    except (TypeError, ValueError):
        pay_st = 0
    try:
        pay_times = int(row.get("payTimes") or 0)
    except (TypeError, ValueError):
        pay_times = 0
    row["payStatusLabel"] = _pay_status_label(pay_st)
    # Java：开票/收款仅 status∈{30,50}（模板硬条件，不含 is_evaluate）
    status_ok_bill = st in (30, 50)
    collection_time = str(row.get("collectionTime") or "").strip()
    pay_way_raw = row.get("payWay")
    has_paytype = pay_way_raw is not None and str(pay_way_raw).strip() not in ("", "0", "None")
    view_kp = False
    view_recv = False
    sure_recv = False
    if parent_kind:
        from apps.orders.services import detail_flags

        open_bills = fetch_all(
            "SELECT id, money FROM qd_bill WHERE exp_of_id = %(oid)s AND type = 1",
            {"oid": row["id"]},
        ) or []
        recv_bills = fetch_all(
            "SELECT id, money FROM qd_bill WHERE exp_of_id = %(oid)s AND type = 2",
            {"oid": row["id"]},
        ) or []
        of_flags = {
            "invoiceType": inv_type,
            "totalPrice": total_p,
            "collection_time": collection_time,
        }
        view_kp = detail_flags.compute_view_kp_btn(
            order_id=int(row["id"]), of=of_flags, open_bills=open_bills
        )
        # Java：仅当 paytype!=null 且 collection_time 非空时才 put viewReciveBtn；
        # 否则 Velocity 中 $!viewReciveBtn 为空 → 不显示「收款」
        if has_paytype and collection_time:
            view_recv = detail_flags.compute_view_receive_btn(
                order_id=int(row["id"]), of=of_flags, receive_bills=recv_bills
            )
        # Java sureReciveBtn：线上收款单 + paytype + collection_time + 线下期数未满
        online_recv_cnt = int(
            scalar(
                """
                SELECT COUNT(*) FROM exp_online_qd_bill
                WHERE exp_of_id = %(oid)s AND type = 2
                """,
                {"oid": row["id"]},
                0,
            )
            or 0
        )
        slots = [p for p in collection_time.split(",") if p.strip()] if collection_time else []
        if (
            online_recv_cnt > 0
            and has_paytype
            and slots
            and len(recv_bills) < len(slots)
        ):
            sure_recv = True
    row["canInvoice"] = parent_kind and status_ok_bill and is_online == 0 and view_kp
    row["canReceiveBill"] = parent_kind and status_ok_bill and view_recv and not sure_recv
    row["canConfirmPay"] = parent_kind and sure_recv
    row["canConfirmCustomer"] = parent_kind and st == 67
    row["canGenerateAppointment"] = parent_kind and is_online == 0 and is_yyd == 0 and st not in (0,)
    # 创建子单：存在待处理产品行 op_status=1
    if parent_kind and st != 0:
        pending_lines = int(
            scalar(
                """
                SELECT COUNT(*) FROM experiment_order_child
                WHERE order_form_id = %(oid)s
                  AND IFNULL(delete_status, 2) <> 1
                  AND IFNULL(op_status, 0) = 1
                """,
                {"oid": row["id"]},
                0,
            )
            or 0
        )
        row["canCreateChild"] = pending_lines > 0
    # type=9：确认已下单 + 付款申请流 + 上传付款/发票
    row["canConfirmOrdered"] = False
    row["canAskPay"] = False
    row["canAuditPay"] = False
    row["canReAskPay"] = False
    row["canUploadPay"] = False
    row["canUploadInvoice"] = False
    if ot == "9":
        # 提交审核：存在已处理子行（op_status=2）对齐 tjshShow
        processed = int(
            scalar(
                """
                SELECT COUNT(*) FROM experiment_order_child c
                WHERE (
                    c.order_form_id = %(oid)s
                    OR EXISTS (
                        SELECT 1 FROM exp_qd_purchase_order_child poc
                        WHERE poc.purchase_order_id = %(oid)s AND poc.order_child_id = c.id
                    )
                )
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND IFNULL(c.op_status, 0) = 2
                """,
                {"oid": row["id"]},
                0,
            )
            or 0
        )
        row["canSubmitAudit"] = st == 5 and processed > 0
        row["canConfirmOrdered"] = st == 30
        coll = str(row.get("collectionTime") or "").strip()
        slots = [x for x in coll.split(",") if x.strip()] if coll else []
        ask_ok = True
        if slots and pay_times >= len(slots):
            ask_ok = False
        row["canAskPay"] = st >= 30 and pay_st in (0, 36) and ask_ok
        row["canAuditPay"] = st >= 30 and pay_st == 32
        row["canReAskPay"] = st >= 30 and pay_st == 33
        # 上传付款：pay_status=34 且收款次数未满
        recv_slots_full = bool(slots) and recv_bill_cnt >= len(slots)
        if not slots:
            recv_slots_full = recv_amt >= total_p > 0
        row["canUploadPay"] = pay_st == 34 and not recv_slots_full
        inv_slots_full = inv_amt >= total_p > 0
        if slots and inv_bill_cnt >= len(slots):
            inv_slots_full = True
        row["canUploadInvoice"] = st >= 30 and not inv_slots_full and inv_type != 2
    # type=9/10 样品流转（确认完成仅 type=10）
    if ot in ("9", "10"):
        from apps.admin_experiment.repositories import sample_flow as sample_flow_repo

        sample_flow_repo.attach_sample_action_flags(row)
    return row


def list_order_children(order_id: int) -> list[dict[str, Any]]:
    """对齐详情页产品行：order_form_id 优先，否则采购关联表。"""
    rows = fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
            c.experiment_project_name AS projectName,
            c.experiment_class_name AS className, c.goods_price AS price,
            c.reference_price AS referencePrice,
            IFNULL(c.expect_finishtime, c.finish_time) AS finishTime,
            c.is_confirm AS isConfirm, c.op_status AS opStatus,
            c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.test_user_id AS testUserId, u.user_name AS testUserName,
            u.true_name AS testUserTrueName, c.add_time AS addTime
        FROM experiment_order_child c
        LEFT JOIN sy_users u ON c.test_user_id = u.id
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )
    if not rows:
        rows = fetch_all(
            """
            SELECT
                c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
                c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
                c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
                c.experiment_project_name AS projectName,
                c.experiment_class_name AS className, c.goods_price AS price,
                c.reference_price AS referencePrice,
                IFNULL(c.expect_finishtime, c.finish_time) AS finishTime,
                c.is_confirm AS isConfirm, c.op_status AS opStatus,
                c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
                c.line_id AS lineId, c.sample_id AS sampleId,
                c.test_user_id AS testUserId, u.user_name AS testUserName,
                u.true_name AS testUserTrueName, c.add_time AS addTime
            FROM exp_qd_purchase_order_child poc
            JOIN experiment_order_child c ON poc.order_child_id = c.id
            LEFT JOIN sy_users u ON c.test_user_id = u.id
            WHERE poc.purchase_order_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
            ORDER BY c.id ASC
            """,
            {"oid": order_id},
        )
    for r in rows:
        # 行状态用 childOrderStatus，不用主单 SUB 映射（否则 2 会原样显示）
        r["orderStatusLabel"] = _child_line_status_label(r.get("orderStatus"))
        r["testUserName"] = str(r.get("testUserTrueName") or r.get("testUserName") or "-")
        pool = str(r.get("testUserId") or "") == GRAB_POOL_TEST_USER_ID
        if pool:
            r["testUserName"] = "待抢单"
        try:
            child_st = int(r.get("orderStatus")) if r.get("orderStatus") is not None else -1
        except (TypeError, ValueError):
            child_st = -1
        # 对齐 Java：待抢池子单且状态未超样品到货，详情中可单独抢单
        r["canGrab"] = pool and child_st <= 36
        try:
            conf_i = int(r.get("isConfirm")) if r.get("isConfirm") is not None else 0
        except (TypeError, ValueError):
            conf_i = 0
        r["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
        ft = r.get("finishTime")
        r["finishTime"] = str(ft)[:19] if ft else ""
    return rows


def list_order_logs(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            l.id, l.addTime, l.log_info AS logInfo, l.log_user_id AS logUserId,
            u.user_name AS logUserName, u.true_name AS logUserTrueName
        FROM experiment_order_log l
        LEFT JOIN sy_users u ON l.log_user_id = u.id
        WHERE l.of_id = %(oid)s AND IFNULL(l.deleteStatus, 0) = 0
        ORDER BY l.addTime DESC
        LIMIT 200
        """,
        {"oid": order_id},
    )
    for r in rows:
        r["logUser"] = str(r.get("logUserTrueName") or r.get("logUserName") or "-")
        at = r.get("addTime")
        r["addTime"] = str(at)[:19] if at else ""
        r["logInfo"] = r.get("logInfo") or ""
    return rows


def list_linked_child_orders(parent_id: int, *, child_order_type: str) -> list[dict[str, Any]]:
    """主单下挂的实验子订单(10) / 分包子订单(9)。"""
    rows = fetch_all(
        """
        SELECT
            t.id, t.order_id AS orderId, t.order_status AS orderStatus,
            t.totalPrice AS totalPrice, t.order_time AS orderTime, t.addTime,
            t.is_confirm AS isConfirm,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName
        FROM experiment_order t
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        WHERE t.parent_id = %(pid)s
          AND t.order_type = %(ot)s
          AND IFNULL(t.deleteStatus, 0) = 0
        ORDER BY t.addTime DESC
        """,
        {"pid": parent_id, "ot": str(child_order_type)},
    )
    for r in rows:
        r["orderStatusLabel"] = _sub_status_label(r.get("orderStatus"))
        r["saleManager"] = str(r.get("managerName") or r.get("managerTrueName") or "").strip()
        r["saleUser"] = str(r.get("saleUserName") or r.get("saleUserTrueName") or "").strip()
        try:
            conf_i = int(r.get("isConfirm")) if r.get("isConfirm") is not None else 0
        except (TypeError, ValueError):
            conf_i = 0
        r["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
        otm = r.get("orderTime") or r.get("addTime")
        r["orderTime"] = str(otm)[:10] if otm else ""
    return rows


def _split_related_nums(raw: Any) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def _join_related_nums(nums: list[str]) -> str:
    """对齐 Java：逗号分隔且末尾保留逗号。"""
    cleaned = [n for n in nums if n]
    if not cleaned:
        return ""
    return ",".join(cleaned) + ","


def list_related_orders(related_order_num: Any) -> list[dict[str, Any]]:
    """related_order_num 对应的关联主单列表（非父子子单）。"""
    nums = _split_related_nums(related_order_num)
    if not nums:
        return []
    placeholders = ", ".join([f"%(n{i})s" for i in range(len(nums))])
    params = {f"n{i}": n for i, n in enumerate(nums)}
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.order_id AS orderId, t.order_type AS orderType,
            t.order_status AS orderStatus, t.totalPrice AS totalPrice,
            t.order_time AS orderTime, t.addTime,
            q.name AS companyName,
            u.company_name AS supplierName,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName
        FROM experiment_order t
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN `user` u ON t.supplier_name = u.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        WHERE t.order_id IN ({placeholders})
          AND IFNULL(t.deleteStatus, 0) = 0
        """,
        params,
    )
    by_no = {str(r.get("orderId") or ""): r for r in rows}
    ordered: list[dict[str, Any]] = []
    for no in nums:
        r = by_no.get(no)
        if not r:
            continue
        ot = str(r.get("orderType") or "")
        r["orderStatusLabel"] = (
            _sub_status_label(r.get("orderStatus"))
            if _is_child_order_type(ot)
            else _status_label(r.get("orderStatus"))
        )
        r["companyName"] = r.get("companyName") or "-"
        r["supplierName"] = r.get("supplierName") or "-"
        r["saleManager"] = str(r.get("managerTrueName") or r.get("managerName") or "-")
        r["saleUser"] = str(r.get("saleUserTrueName") or r.get("saleUserName") or "-")
        otm = r.get("orderTime") or r.get("addTime")
        r["orderTime"] = str(otm)[:19] if otm else ""
        ordered.append(r)
    return ordered


def list_order_files(order_id: int) -> list[dict[str, Any]]:
    """对齐 Java getByExpOfId：订单资料（排除 type=5 发票资料）。"""
    from apps.core.services.sysconfig import get_config_row, image_web_server
    from apps.orders.repositories import accessory_list as acc_repo
    from apps.orders.services.sale_detail_enrich import accessory_url, enrich_accessory_rows

    rows = acc_repo.load_accessories(exp_of_id=order_id, exclude_types=(5,))
    config = get_config_row()
    base = image_web_server(config)
    out = enrich_accessory_rows(rows, base)
    for a in out:
        a["url"] = accessory_url(base, a)
        if not a.get("info"):
            a["info"] = a.get("name") or ""
    return out


def update_order_msg(*, order_id: int, msg: str) -> tuple[bool, str]:
    """对齐 Java msgBlur：更新订单备注（msg/mark）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    text = (msg or "")[:2000]
    try:
        execute(
            """
            UPDATE experiment_order
            SET msg = %(msg)s, mark = %(msg)s
            WHERE id = %(id)s
            """,
            {"msg": text, "id": order_id},
        )
    except Exception:
        try:
            execute(
                "UPDATE experiment_order SET mark = %(msg)s WHERE id = %(id)s",
                {"msg": text, "id": order_id},
            )
        except Exception:
            return False, "更新备注失败"
    return True, "备注已保存"


def delete_order_file(*, accessory_id: int) -> tuple[bool, str]:
    from apps.orders.repositories import accessory as accessory_repo

    if not accessory_id:
        return False, "参数错误"
    if not accessory_repo.soft_delete_accessory(accessory_id):
        return False, "附件不存在或已删除"
    return True, "删除成功"


def get_order_detail_bundle(order_id: int) -> dict[str, Any] | None:
    """Java orderdetail 聚合：主信息 + 产品行 + 关联子单 + 关联订单 + 操作日志 + 订单资料。"""
    row = get_order(order_id)
    if not row:
        return None
    ot = str(row.get("orderType") or "")
    children = list_order_children(order_id)
    logs = list_order_logs(order_id)
    linked: list[dict[str, Any]] = []
    if ot == "6":
        linked = list_linked_child_orders(order_id, child_order_type="10")
    elif ot == "8":
        linked = list_linked_child_orders(order_id, child_order_type="9")
    related = list_related_orders(row.get("relatedOrderNum"))
    files = list_order_files(order_id)
    yyd_files = [f for f in files if str(f.get("type") or "") == "6"]
    return {
        **row,
        "children": children,
        "logs": logs,
        "linkedOrders": linked,
        "relatedOrders": related,
        "files": files,
        "yydFiles": yyd_files,
        "detailKind": {
            "6": "experiment",
            "10": "experiment_sub",
            "8": "subcontract",
            "9": "subcontract_sub",
        }.get(ot, "unknown"),
    }


def _write_order_log(order_id: int, info: str, user_id: str | int | None = None) -> None:
    uid = str(user_id).strip() if user_id not in (None, "") else None
    try:
        execute(
            """
            INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info, log_user_id)
            VALUES (NOW(), 0, %(oid)s, %(info)s, %(uid)s)
            """,
            {"oid": order_id, "info": info, "uid": uid},
        )
    except Exception:
        try:
            execute(
                """
                INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info)
                VALUES (NOW(), 0, %(oid)s, %(info)s)
                """,
                {"oid": order_id, "info": info},
            )
        except Exception:
            pass


def _set_order_status(order_id: int, status: int) -> None:
    execute(
        "UPDATE experiment_order SET order_status = %(st)s WHERE id = %(id)s",
        {"st": status, "id": order_id},
    )


def audit_order(
    *, order_id: int, pass_: bool, remark: str = "", staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        return False, "订单状态异常"
    if st != 20:
        return False, "当前状态不可审核"
    next_status = 30 if pass_ else 10
    _set_order_status(order_id, next_status)
    _write_order_log(
        order_id,
        ("审核通过" if pass_ else "审核驳回") + (f"：{remark}" if remark else ""),
        user_id=staff_user_id,
    )
    return True, "审核成功" if pass_ else "已驳回"


def cancel_order(
    *, order_id: int, remark: str = "", staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    """对齐 Java customeOperateCancel：主单取消并同步取消下属采购子单。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canCancel"):
        return False, "当前状态不可取消"
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        st = -1
    if st == 0:
        return False, "该订单已取消，请刷新页面！"
    _set_order_status(order_id, 0)
    _write_order_log(
        order_id,
        "取消订单" + (f"：{remark}" if remark else ""),
        user_id=staff_user_id,
    )
    ot = str(row.get("orderType") or "")
    if ot in ("6", "8"):
        child_ot = "10" if ot == "6" else "9"
        children = fetch_all(
            """
            SELECT id, order_id AS orderId
            FROM experiment_order
            WHERE parent_id = %(pid)s
              AND order_type = %(ot)s
              AND IFNULL(deleteStatus, 0) = 0
              AND IFNULL(order_status, -1) != 0
            """,
            {"pid": order_id, "ot": child_ot},
        )
        for c in children:
            cid = int(c["id"])
            _set_order_status(cid, 0)
            _write_order_log(cid, f"主单取消，同步取消子订单 {c.get('orderId') or ''}".strip())
    return True, "订单已取消"


def submit_audit(*, order_id: int) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canSubmitAudit"):
        return False, "当前状态不可提交审核"
    _set_order_status(order_id, 20)
    _write_order_log(order_id, "提交审核")
    return True, "已提交审核"


def withdraw_audit(*, order_id: int) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canWithdrawAudit"):
        return False, "当前状态不可取消审核申请"
    _set_order_status(order_id, 5)
    _write_order_log(order_id, "取消审核申请")
    return True, "已取消审核申请"


def cost_settle_sure(*, order_id: int) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canCostSettle"):
        return False, "当前不可结清成本"
    execute(
        "UPDATE experiment_order SET cost_settle = 1 WHERE id = %(id)s",
        {"id": order_id},
    )
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        st = -1
    # Java：部分场景 49→50；若已审核完成附近则升至已完成
    if st in (49, 45, 46):
        _set_order_status(order_id, 50)
    _write_order_log(order_id, "所有成本已结清")
    # Java costSettleSure：结清后对未分账收款补分钱
    try:
        from apps.admin_experiment.services.split_money import try_split_on_settle

        try_split_on_settle(order_id)
    except Exception:
        return True, "已标记成本结清（分钱补分失败，请检查账户日志）"
    return True, "已标记成本结清"


def _parse_scale_pairs(raw: str) -> list[tuple[str, str]]:
    """解析 userId_value,userId_value。"""
    text = (raw or "").strip()
    if not text:
        return []
    out: list[tuple[str, str]] = []
    for part in text.split(","):
        part = part.strip()
        if not part or "_" not in part:
            continue
        uid, val = part.split("_", 1)
        uid = uid.strip()
        val = val.strip().replace("%", "")
        if uid and val != "":
            out.append((uid, val))
    return out


def _user_display_name(user_id: str) -> str:
    u = fetch_one(
        """
        SELECT user_name AS userName, true_name AS trueName
        FROM sy_users WHERE id = %(id)s LIMIT 1
        """,
        {"id": user_id},
    )
    if not u:
        return user_id
    return str(u.get("trueName") or u.get("userName") or user_id)


def update_share_ratio(
    *,
    order_id: int,
    user_scale_info: str = "",
    salecb_user_scale_info: str = "",
    scale_info: str = "",
) -> tuple[bool, str]:
    """对齐 Java updateShareRatio：毛利%（合计100）+ 可选成本金额。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canShareRatio"):
        return False, "当前不可调整分成"
    profit_raw = (user_scale_info or scale_info or "").strip()
    cost_raw = (salecb_user_scale_info or "").strip()
    profit_pairs = _parse_scale_pairs(profit_raw)
    if not profit_pairs:
        return False, "请填写毛利分成比例"
    total = 0.0
    for uid, val in profit_pairs:
        urow = fetch_one(
            "SELECT id FROM sy_users WHERE id = %(id)s LIMIT 1",
            {"id": uid},
        )
        if not urow:
            return False, "请填写正确的分成人员"
        try:
            n = float(val)
        except (TypeError, ValueError):
            return False, "请填写正确的分成比例!"
        if n < 0:
            return False, "请填写正确的分成比例!"
        total += n
    if abs(total - 100.0) > 0.01:
        return False, "总的分成比例不是100，请重新输入"
    # 规范化存储格式
    profit_store = ",".join(f"{uid}_{val}" for uid, val in profit_pairs)
    cost_pairs = _parse_scale_pairs(cost_raw)
    cost_store = ",".join(f"{uid}_{val}" for uid, val in cost_pairs) if cost_pairs else ""
    ot = str(row.get("orderType") or "")
    # 分包订单(8) 仅毛利分成
    if ot == "8":
        cost_store = ""
    execute(
        """
        UPDATE experiment_order
        SET user_scale_info = %(profit)s,
            scale_info = %(profit)s,
            salecb_user_scale_info = %(cost)s
        WHERE id = %(id)s
        """,
        {"id": order_id, "profit": profit_store[:2000], "cost": cost_store[:2000]},
    )
    log_parts = ["调整分成比例，毛利分成："]
    log_parts.append(
        "，".join(f"{_user_display_name(uid)} {val} %" for uid, val in profit_pairs)
    )
    if cost_pairs:
        log_parts.append("；成本分成：")
        log_parts.append(
            "，".join(f"{_user_display_name(uid)} {val}" for uid, val in cost_pairs)
        )
    _write_order_log(order_id, "".join(log_parts)[:500])
    return True, "操作成功!"


def add_related_order(
    *,
    order_id: int,
    related_order_no: str,
    r_select: str = "",
) -> tuple[bool, str]:
    """对齐 Java addRelevanceOrder_dpt：双向写入 related_order_num。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canAddRelated"):
        return False, "当前不可关联订单"
    related_no = (related_order_no or "").strip()
    select_key = str(r_select or "").strip()
    if not related_no:
        return False, "订单类型或订单号不能为空"
    if not select_key:
        return False, "订单类型或订单号不能为空"
    self_no = str(row.get("orderId") or "")
    if self_no and self_no == related_no:
        return False, "不能添加自身订单"
    # Java rSelect: 5=实验订单(type6), 6=实验分包订单(type8)
    expect_type = {"5": "6", "6": "8"}.get(select_key)
    if not expect_type:
        return False, "订单类型或订单号不能为空"
    other = fetch_one(
        """
        SELECT id, order_id AS orderId, order_type AS orderType,
               related_order_num AS relatedOrderNum
        FROM experiment_order
        WHERE order_id = %(oid)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"oid": related_no},
    )
    if not other:
        return False, "订单不存在"
    if int(other["id"]) == int(order_id):
        return False, "不能添加自身订单"
    if str(other.get("orderType") or "") != expect_type:
        return False, "订单号与订单类型不匹配"
    self_related = _split_related_nums(row.get("relatedOrderNum"))
    if related_no in self_related:
        return False, "已关联过该订单"
    other_related = _split_related_nums(other.get("relatedOrderNum"))
    if self_no and self_no not in other_related:
        other_related.append(self_no)
    if related_no not in self_related:
        self_related.append(related_no)
    execute(
        "UPDATE experiment_order SET related_order_num = %(n)s WHERE id = %(id)s",
        {"id": order_id, "n": _join_related_nums(self_related)},
    )
    execute(
        "UPDATE experiment_order SET related_order_num = %(n)s WHERE id = %(id)s",
        {"id": int(other["id"]), "n": _join_related_nums(other_related)},
    )
    _write_order_log(order_id, f"增加关联订单：{related_no}")
    _write_order_log(int(other["id"]), f"被关联到订单：{self_no}")
    return True, "关联成功"


def del_related_order(*, of_order_no: str, related_order_no: str) -> tuple[bool, str]:
    """对齐 Java delRelatedOrder：双向从 related_order_num 移除。"""
    of_no = (of_order_no or "").strip()
    rel_no = (related_order_no or "").strip()
    if not of_no or not rel_no:
        return False, "参数错误"

    def _strip_one(owner_no: str, remove_no: str) -> None:
        owner = fetch_one(
            """
            SELECT id, related_order_num AS relatedOrderNum
            FROM experiment_order
            WHERE order_id = %(oid)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"oid": owner_no},
        )
        if not owner:
            return
        nums = [n for n in _split_related_nums(owner.get("relatedOrderNum")) if n != remove_no]
        execute(
            "UPDATE experiment_order SET related_order_num = %(n)s WHERE id = %(id)s",
            {"id": int(owner["id"]), "n": _join_related_nums(nums)},
        )
        _write_order_log(int(owner["id"]), f"删除关联订单：{remove_no}")

    _strip_one(of_no, rel_no)
    _strip_one(rel_no, of_no)
    return True, "删除成功"


def save_finish_times(*, order_id: int, items: list[dict[str, Any]]) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canSaveFinish"):
        return False, "当前不可保存完成时间"
    if not items:
        return False, "没有可保存的明细"
    updated = 0
    for it in items:
        cid = it.get("id")
        ft = (it.get("finishTime") or it.get("finish_time") or "").strip()
        if not cid:
            continue
        try:
            cid_i = int(cid)
        except (TypeError, ValueError):
            continue
        if ft:
            execute(
                """
                UPDATE experiment_order_child
                SET expect_finishtime = %(ft)s
                WHERE id = %(id)s
                """,
                {"id": cid_i, "ft": ft[:19]},
            )
        updated += 1
    _write_order_log(order_id, f"保存预计完成时间（{updated} 行）")
    return True, "保存成功"


def build_more_info(order_id: int) -> dict[str, Any] | None:
    row = get_order(order_id)
    if not row:
        return None
    return {
        "orderId": row.get("orderId"),
        "customerName": row.get("customerName") or row.get("companyName"),
        "supplierName": row.get("supplierName"),
        "shipUser": row.get("shipUser"),
        "shipPhone": row.get("shipPhone"),
        "shipAddress": row.get("shipAddress"),
        "saleManager": row.get("saleManager"),
        "saleUser": row.get("saleUser"),
        "mark": row.get("mark"),
        "userScaleInfo": row.get("userScaleInfo") or row.get("scaleInfo") or "",
        "costSettleLabel": row.get("costSettleLabel"),
        "currencyLabel": row.get("currencyLabel"),
        "invoiceAmount": row.get("invoiceAmount"),
        "receiveAmount": row.get("receiveAmount"),
    }


def save_invoice_bill(
    *, order_id: int, money: Any, staff_user_id: str = "", log_info: str = "录入开票"
) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canInvoice"):
        return False, "当前不可开票"
    try:
        amt = float(money or 0)
    except (TypeError, ValueError):
        amt = 0
    if amt <= 0:
        return False, "开票金额须大于 0"
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark)
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 1, 0, NOW(), %(log_info)s)
        """,
        {
            "oid": order_id,
            "money": amt,
            "log_info": (log_info or "录入开票")[:500],
            "uid": staff_user_id or None,
        },
    )
    _write_order_log(order_id, f"开票 {amt}", user_id=staff_user_id)
    return True, "开票成功"


def confirm_customer_order(*, order_id: int) -> tuple[bool, str]:
    """对齐 Java makeFrontOrder type=confirm（status 67 → 推进）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canConfirmCustomer"):
        return False, "当前状态不可确认"
    _set_order_status(order_id, 30)
    _write_order_log(order_id, "已和客户沟通确认")
    return True, "已确认"


def confirm_online_pay(*, order_id: int, staff_user_id: str = "") -> tuple[bool, str]:
    """对齐 Java sureReciveBtn：线上未结清时，补录差额收款确认。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canConfirmPay"):
        return False, "当前无需确认付款"
    try:
        total_p = float(row.get("totalPrice") or 0)
        recv_amt = float(row.get("receiveAmount") or 0)
    except (TypeError, ValueError):
        return False, "金额异常"
    remain = round(total_p - recv_amt, 2)
    if remain <= 0:
        return False, "当前无需确认付款"
    from apps.admin_experiment.services.split_money import save_receive_bill

    return save_receive_bill(
        order_id=order_id,
        money=remain,
        staff_user_id=staff_user_id,
        log_info="确认付款",
    )


def generate_appointment(
    *, order_id: int, test_address_id: str = "", staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    """对齐 Java geranateYydForm：写地址、标记 is_yyd、生成预约单 PDF(type=6)。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canGenerateAppointment"):
        return False, "当前不可生成预约单"
    addr = (test_address_id or "").strip()
    if not addr:
        return False, "请选择寄送地址"
    try:
        addr_id = int(addr)
    except (TypeError, ValueError):
        return False, "寄送地址无效"
    try:
        execute(
            """
            UPDATE experiment_order
            SET is_yyd = 1, test_address_id = %(tid)s
            WHERE id = %(id)s
            """,
            {"id": order_id, "tid": addr_id},
        )
    except Exception:
        try:
            execute(
                "UPDATE experiment_order SET is_yyd = 1 WHERE id = %(id)s",
                {"id": order_id},
            )
        except Exception:
            return False, "更新预约标志失败"

    pdf_ok, pdf_msg = _build_appointment_pdf(order_id=order_id, test_address_id=addr_id)
    _write_order_log(
        order_id,
        f"生成预约单 地址:{addr_id}" + ("" if pdf_ok else f"（PDF:{pdf_msg}）"),
        user_id=staff_user_id,
    )
    if not pdf_ok:
        return True, f"已标记预约单，但 PDF 生成失败：{pdf_msg}"
    return True, "已生成预约单"


def _build_appointment_pdf(*, order_id: int, test_address_id: int) -> tuple[bool, str]:
    """生成简易预约单 PDF 并写入 accessory type=6。"""
    try:
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfgen import canvas

        from apps.orders.repositories import print_pdf as print_pdf_repo
        from apps.orders.services.accessory_upload import save_order_attachment
    except Exception as exc:
        return False, f"缺少 PDF 依赖: {exc}"

    order = fetch_one(
        """
        SELECT id, order_id AS orderNo, customer_name AS customerName,
               supplier_name AS supplierName, addTime, send_address AS sendAddress,
               addressee_name AS shipUser, addressee_mobile AS shipPhone
        FROM experiment_order WHERE id = %(id)s LIMIT 1
        """,
        {"id": order_id},
    )
    if not order:
        return False, "订单不存在"
    addr_row = print_pdf_repo.get_test_address(test_address_id) or {}
    address_text = str(addr_row.get("address") or order.get("sendAddress") or "")
    children = fetch_all(
        """
        SELECT
            order_id AS childOrderId, goods_name AS goodsName, goods_spec AS goodsSpec,
            goods_brand_name AS goodsBrand, goods_nums AS goodsCount,
            experiment_project_name AS projectName, experiment_class_name AS className
        FROM experiment_order_child
        WHERE order_form_id = %(oid)s AND IFNULL(delete_status, 2) <> 1
        ORDER BY id ASC
        LIMIT 100
        """,
        {"oid": order_id},
    )
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font_name = "STSong-Light"
    except Exception:
        font_name = "Helvetica"

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont(font_name, 16)
    c.drawString(40, y, "实验预约单")
    y -= 28
    c.setFont(font_name, 10)
    lines = [
        f"订单编号：{order.get('orderNo') or order_id}",
        f"客户名称：{order.get('customerName') or '-'}",
        f"所属公司：{order.get('supplierName') or '-'}",
        f"收件人：{order.get('shipUser') or '-'}",
        f"联系电话：{order.get('shipPhone') or '-'}",
        f"寄送地址：{address_text or '-'}",
        f"制单时间：{str(order.get('addTime') or '')[:19]}",
        "",
        "产品明细：",
    ]
    for line in lines:
        c.drawString(40, y, str(line)[:90])
        y -= 16
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 40
    for idx, ch in enumerate(children, 1):
        text = (
            f"{idx}. {ch.get('childOrderId') or ''} "
            f"{ch.get('goodsName') or ''} / {ch.get('goodsSpec') or ''} "
            f"x{ch.get('goodsCount') or ''} "
            f"{ch.get('projectName') or ''} ({ch.get('className') or ''})"
        )
        c.drawString(40, y, text[:95])
        y -= 14
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 40
    c.save()
    pdf_bytes = buf.getvalue()
    order_no = str(order.get("orderNo") or order_id)
    ok_flag, msg, _meta = save_order_attachment(
        data=pdf_bytes,
        orig_name=f"{order_no}预约单.pdf",
        content_type="application/pdf",
        acc_type=6,
        exp_of_id=order_id,
    )
    return (True, "ok") if ok_flag else (False, msg)


def update_order_basic(
    *,
    order_id: int,
    mark: str = "",
    ship_user: str = "",
    ship_phone: str = "",
    ship_address: str = "",
    total_price: Any = None,
    delivery_time: str = "",
) -> tuple[bool, str]:
    """编辑订单主字段（精简版 editPage）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canEdit"):
        return False, "当前不可编辑"
    sets = []
    params: dict[str, Any] = {"id": order_id}
    if mark is not None:
        sets.append("mark = %(mark)s")
        sets.append("msg = %(mark)s")
        params["mark"] = mark[:1000]
    if ship_user is not None:
        sets.append("addressee_name = %(ship_user)s")
        params["ship_user"] = ship_user[:100]
    if ship_phone is not None:
        sets.append("addressee_mobile = %(ship_phone)s")
        params["ship_phone"] = ship_phone[:50]
    if ship_address is not None:
        sets.append("send_address = %(ship_address)s")
        params["ship_address"] = ship_address[:500]
    if delivery_time is not None and str(delivery_time).strip():
        sets.append("delivery_time = %(delivery_time)s")
        params["delivery_time"] = str(delivery_time).strip()[:19]
    if total_price is not None and str(total_price) != "":
        try:
            params["tp"] = float(total_price)
            sets.append("totalPrice = %(tp)s")
        except (TypeError, ValueError):
            pass
    if not sets:
        return False, "无变更"
    # mark/msg 可能重复；去重保留顺序
    uniq: list[str] = []
    for s in sets:
        if s not in uniq:
            uniq.append(s)
    execute(
        f"UPDATE experiment_order SET {', '.join(uniq)} WHERE id = %(id)s",
        params,
    )
    _write_order_log(order_id, "编辑订单信息")
    return True, "保存成功"


def confirm_ordered(*, order_id: int) -> tuple[bool, str]:
    """对齐 Java addOrderData / saveXdData：status 30 → 35 确认已下单。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canConfirmOrdered"):
        return False, "当前不可确认已下单"
    _set_order_status(order_id, 35)
    _write_order_log(order_id, "确认已下单")
    return True, "已确认下单"


def update_sub_order_status(*, order_id: int, order_status: int) -> tuple[bool, str]:
    """对齐 Java updateOrderStatus：厂家已发货等（常见 45）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if str(row.get("orderType") or "") != "9":
        return False, "仅实验分包子订单支持此操作"
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    target = int(order_status)
    if target == 45:
        if st < 30 or st == 0:
            return False, "当前状态不可发货"
        if st >= 45:
            return False, "已发货或已完成"
        _set_order_status(order_id, 45)
        _write_order_log(order_id, "厂家已发货")
        return True, "发货成功"
    return False, "不支持的状态变更"


def update_sub_pay(*, order_id: int, pay_type: str | int) -> tuple[bool, str]:
    """
    对齐 Java pay.ajax / updatePayPurchaseOrder：
    type=1 申请/重提 → 32；type=2 审核通过 → 34；type=3 驳回 → 33。
    """
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if str(row.get("orderType") or "") != "9":
        return False, "仅实验分包子订单支持付款申请"
    t = str(pay_type or "").strip()
    try:
        st = int(row.get("orderStatus") or 0)
        pay_st = int(row.get("payStatus") or 0)
    except (TypeError, ValueError):
        return False, "状态异常"
    if st < 30:
        return False, "订单未审核通过，不可操作付款"
    if t == "1":
        if pay_st == 33:
            if not row.get("canReAskPay"):
                return False, "当前不可重新发起付款申请"
            log_txt = "重新发起付款申请"
        elif pay_st in (0, 36):
            if not row.get("canAskPay"):
                return False, "当前不可申请付款"
            log_txt = "申请付款"
        else:
            return False, "当前付款状态不可申请"
        execute(
            "UPDATE experiment_order SET pay_status = 32 WHERE id = %(id)s",
            {"id": order_id},
        )
        _write_order_log(order_id, log_txt)
        return True, "已提交付款申请"
    if t == "2":
        if not row.get("canAuditPay"):
            return False, "当前无可审核的付款申请"
        execute(
            "UPDATE experiment_order SET pay_status = 34 WHERE id = %(id)s",
            {"id": order_id},
        )
        _write_order_log(order_id, "申请付款审核通过")
        return True, "付款申请已通过"
    if t == "3":
        if not row.get("canAuditPay"):
            return False, "当前无可审核的付款申请"
        execute(
            "UPDATE experiment_order SET pay_status = 33 WHERE id = %(id)s",
            {"id": order_id},
        )
        _write_order_log(order_id, "申请付款驳回")
        return True, "付款申请已驳回"
    return False, "无法处理此类别"


def upload_sub_pay_bill(
    *, order_id: int, money: Any, staff_user_id: str = "", log_info: str = "上传付款信息"
) -> tuple[bool, str]:
    """type=9 上传付款信息（qd_bill type=2），并推进 pay_status 36/38。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canUploadPay"):
        return False, "当前不可上传付款信息"
    try:
        amt = float(money or 0)
    except (TypeError, ValueError):
        amt = 0
    if amt <= 0:
        return False, "付款金额须大于 0"
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark)
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 2, 0, NOW(), %(log_info)s)
        """,
        {
            "oid": order_id,
            "money": amt,
            "log_info": (log_info or "上传付款信息")[:500],
            "uid": staff_user_id or None,
        },
    )
    # pay_times +1；收齐则 38 否则 36
    coll = str(row.get("collectionTime") or "").strip()
    slots = [x for x in coll.split(",") if x.strip()] if coll else []
    try:
        pay_times = int(row.get("payTimes") or 0) + 1
    except (TypeError, ValueError):
        pay_times = 1
    try:
        recv_cnt = int(row.get("receiveBillCount") or 0) + 1
    except (TypeError, ValueError):
        recv_cnt = 1
    if slots and recv_cnt >= len(slots):
        new_pay = 38
    else:
        new_pay = 36
    execute(
        """
        UPDATE experiment_order
        SET pay_status = %(ps)s, pay_times = %(pt)s
        WHERE id = %(id)s
        """,
        {"ps": new_pay, "pt": pay_times, "id": order_id},
    )
    _write_order_log(order_id, f"上传付款信息 {amt}")
    return True, "上传付款成功"


def upload_sub_invoice_bill(
    *, order_id: int, money: Any, staff_user_id: str = "", log_info: str = "上传发票信息"
) -> tuple[bool, str]:
    """type=9 上传发票信息（qd_bill type=1）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canUploadInvoice"):
        return False, "当前不可上传发票信息"
    try:
        amt = float(money or 0)
    except (TypeError, ValueError):
        amt = 0
    if amt <= 0:
        return False, "发票金额须大于 0"
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark)
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 1, 0, NOW(), %(log_info)s)
        """,
        {
            "oid": order_id,
            "money": amt,
            "log_info": (log_info or "上传发票信息")[:500],
            "uid": staff_user_id or None,
        },
    )
    _write_order_log(order_id, f"上传发票信息 {amt}")
    return True, "上传发票成功"


def create_sub_order_from_parent(
    *,
    parent_id: int,
    child_line_ids: Any = None,
    form: dict[str, Any] | None = None,
) -> tuple[bool, str, int | None]:
    """
    从实验主单创建子订单。
    - type=6 → type=10 实验子订单（精简）
    - type=8 → type=9 实验分包子订单（对齐 Java expSubPurchaseOrder/submitOrder）
    """
    parent = get_order(parent_id)
    if not parent:
        return False, "主单不存在", None
    if str(parent.get("orderType") or "") not in ("6", "8"):
        return False, "仅实验/分包主单可创建子订单", None
    if not parent.get("canCreateChild"):
        return False, "没有待处理的产品行，无法创建子订单", None

    child_ot = "10" if str(parent.get("orderType")) == "6" else "9"
    form = form or {}
    # 选行
    ids: list[int] = []
    if child_line_ids:
        raw = child_line_ids
        if isinstance(raw, (list, tuple)):
            for x in raw:
                try:
                    ids.append(int(x))
                except (TypeError, ValueError):
                    pass
        else:
            for p in str(raw).split(","):
                p = p.strip()
                if p.isdigit():
                    ids.append(int(p))
    if not ids:
        rows = fetch_all(
            """
            SELECT id FROM experiment_order_child
            WHERE order_form_id = %(oid)s
              AND IFNULL(delete_status, 2) <> 1
              AND IFNULL(op_status, 0) = 1
            ORDER BY id
            """,
            {"oid": parent_id},
        )
        ids = [int(r["id"]) for r in rows if r.get("id") is not None]
    if not ids:
        return False, "没有可挂接的产品行", None

    test_user_ids: list[str] = []
    cost_prices: list[str] = []
    finish_times: list[str] = []
    raw_tu = form.get("testUserIds") or form.get("test_user_ids") or []
    raw_cp = form.get("costPrices") or form.get("cost_prices") or []
    raw_ft = form.get("finishTimes") or form.get("finish_times") or []
    if isinstance(raw_tu, str):
        test_user_ids = [x.strip() for x in raw_tu.split(",")]
    elif isinstance(raw_tu, (list, tuple)):
        test_user_ids = [str(x).strip() for x in raw_tu]
    if isinstance(raw_cp, str):
        cost_prices = [x.strip() for x in raw_cp.split(",")]
    elif isinstance(raw_cp, (list, tuple)):
        cost_prices = [str(x).strip() for x in raw_cp]
    if isinstance(raw_ft, str):
        finish_times = [x.strip() for x in raw_ft.split(",")]
    elif isinstance(raw_ft, (list, tuple)):
        finish_times = [str(x).strip() for x in raw_ft]

    if child_ot == "9":
        if len(test_user_ids) != len(ids) or any(not t for t in test_user_ids):
            return False, "所选分包测试人员不能为空", None
        if len(cost_prices) != len(ids) or any(not c for c in cost_prices):
            return False, "所选分包单价不能为空", None

    from datetime import datetime

    suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    new_no = f"{parent.get('orderId') or parent_id}-Z{suffix[-6:]}"
    # 分包提交审核 → status=20；实验子单创建 → status=5
    init_status = 20 if child_ot == "9" and form.get("submitAudit") else 5
    try:
        total_price = float(form.get("totalPrice") or 0)
    except (TypeError, ValueError):
        total_price = 0.0
    if child_ot == "9" and total_price <= 0 and cost_prices:
        try:
            total_price = sum(float(c or 0) for c in cost_prices)
        except (TypeError, ValueError):
            total_price = 0.0

    sale_manager = str(form.get("saleManager") or form.get("sale_manager") or "").strip()
    test_manager = str(form.get("testManager") or form.get("test_manager") or "").strip()
    stock_company = str(
        form.get("stockCompanyName") or form.get("stock_company_name") or ""
    ).strip()
    try:
        invoice_type = int(form.get("invoiceType") if form.get("invoiceType") is not None else 1)
    except (TypeError, ValueError):
        invoice_type = 1
    in_bill_type_id = str(form.get("inBillTypeId") or form.get("in_bill_type_id") or "").strip()
    taxes = str(form.get("taxes") or "").strip()
    order_time = str(form.get("orderTime") or form.get("order_time") or "").strip()
    delivery_time = str(form.get("deliveryTime") or form.get("delivery_time") or "").strip()
    pay_way = str(form.get("payWay") or form.get("pay_way") or "").strip()
    currency_type = str(form.get("currencyType") or form.get("currency_type") or "1").strip() or "1"
    collection_time = str(
        form.get("collectionTime") or form.get("collection_time") or ""
    ).strip()
    msg = str(form.get("msg") or form.get("mark") or "").strip()

    new_id = execute_insert(
        """
        INSERT INTO experiment_order
            (addTime, deleteStatus, order_id, order_type, order_status, parent_id,
             totalPrice, sale_manager, sale_user, customer_name, supplier_name,
             currency_type, invoiceType, is_confirm, cost_settle)
        SELECT
            NOW(), 0, %(ono)s, %(ot)s, %(st)s, id,
            %(tp)s,
            COALESCE(NULLIF(%(sm)s, ''), sale_manager),
            sale_user, customer_name, supplier_name,
            %(ct)s, %(inv)s, 0, 0
        FROM experiment_order WHERE id = %(pid)s
        """,
        {
            "ono": new_no[:80],
            "ot": child_ot,
            "st": init_status,
            "tp": total_price,
            "sm": sale_manager,
            "ct": currency_type,
            "inv": invoice_type,
            "pid": parent_id,
        },
    )
    if not new_id:
        return False, "创建子订单失败", None

    # 补充分包字段（列可能因库版本差异，失败不阻断主流程）
    if child_ot == "9":
        try:
            execute(
                """
                UPDATE experiment_order
                SET test_manager = %(tm)s,
                    stock_company_name = %(scn)s,
                    in_bill_type_id = %(ibt)s,
                    order_time = NULLIF(%(otm)s, ''),
                    delivery_time = NULLIF(%(dt)s, ''),
                    pay_way = NULLIF(%(pw)s, ''),
                    taxes = NULLIF(%(tx)s, ''),
                    collection_time = NULLIF(%(ctm)s, ''),
                    mark = NULLIF(%(mk)s, '')
                WHERE id = %(id)s
                """,
                {
                    "id": new_id,
                    "tm": test_manager or None,
                    "scn": stock_company or None,
                    "ibt": int(in_bill_type_id) if in_bill_type_id.isdigit() else None,
                    "otm": order_time[:19] if order_time else "",
                    "dt": delivery_time[:19] if delivery_time else "",
                    "pw": pay_way if pay_way.isdigit() else None,
                    "tx": taxes or None,
                    "ctm": collection_time or None,
                    "mk": msg[:500] if msg else None,
                },
            )
        except Exception:
            try:
                execute(
                    """
                    UPDATE experiment_order
                    SET stock_company_name = %(scn)s,
                        order_time = NULLIF(%(otm)s, ''),
                        delivery_time = NULLIF(%(dt)s, ''),
                        mark = NULLIF(%(mk)s, '')
                    WHERE id = %(id)s
                    """,
                    {
                        "id": new_id,
                        "scn": stock_company or None,
                        "otm": order_time[:19] if order_time else "",
                        "dt": delivery_time[:19] if delivery_time else "",
                        "mk": msg[:500] if msg else None,
                    },
                )
            except Exception:
                pass

    # 把产品行挂到新子单（采购关联表）
    for i, cid in enumerate(ids):
        try:
            execute(
                """
                INSERT INTO exp_qd_purchase_order_child (purchase_order_id, order_child_id, addTime)
                VALUES (%(pid)s, %(cid)s, NOW())
                """,
                {"pid": new_id, "cid": cid},
            )
        except Exception:
            try:
                execute(
                    """
                    INSERT INTO exp_qd_purchase_order_child (purchase_order_id, order_child_id)
                    VALUES (%(pid)s, %(cid)s)
                    """,
                    {"pid": new_id, "cid": cid},
                )
            except Exception:
                pass
        # 更新测试员 / 分包单价 / 预计完成
        tu = test_user_ids[i] if i < len(test_user_ids) else ""
        cp = cost_prices[i] if i < len(cost_prices) else ""
        ft = finish_times[i] if i < len(finish_times) else ""
        if tu or cp or ft:
            try:
                execute(
                    """
                    UPDATE experiment_order_child
                    SET test_user_id = COALESCE(NULLIF(%(tu)s, ''), test_user_id),
                        cost_price = COALESCE(NULLIF(%(cp)s, ''), cost_price),
                        reference_price = COALESCE(NULLIF(%(cp)s, ''), reference_price),
                        expect_finishtime = COALESCE(NULLIF(%(ft)s, ''), expect_finishtime),
                        op_status = 2,
                        order_status = CASE
                            WHEN IFNULL(order_status, 0) < 2 THEN 2
                            ELSE order_status
                        END
                    WHERE id = %(cid)s AND order_form_id = %(oid)s
                    """,
                    {"tu": tu, "cp": cp, "ft": ft[:19] if ft else "", "cid": cid, "oid": parent_id},
                )
            except Exception:
                execute(
                    """
                    UPDATE experiment_order_child
                    SET op_status = 2,
                        order_status = CASE
                            WHEN IFNULL(order_status, 0) < 2 THEN 2
                            ELSE order_status
                        END
                    WHERE id = %(cid)s AND order_form_id = %(oid)s
                    """,
                    {"cid": cid, "oid": parent_id},
                )
        else:
            execute(
                """
                UPDATE experiment_order_child
                SET op_status = 2,
                    order_status = CASE
                        WHEN IFNULL(order_status, 0) < 2 THEN 2
                        ELSE order_status
                    END
                WHERE id = %(cid)s AND order_form_id = %(oid)s
                """,
                {"cid": cid, "oid": parent_id},
            )
    _write_order_log(parent_id, f"创建{'实验' if child_ot == '10' else '分包'}子订单 {new_no}")
    _write_order_log(
        new_id,
        "子订单创建并提交审核" if init_status == 20 else "子订单创建",
    )
    return True, "创建成功", int(new_id)


def list_export_orders(
    *,
    order_type: str | int,
    limit: int = 5000,
    **filters: Any,
) -> list[dict[str, Any]]:
    if str(order_type) in ("9", "10"):
        rows, _ = list_sub_orders(
            order_type=str(order_type),
            order_id=str(filters.get("order_id") or ""),
            parent_order_id=str(filters.get("parent_order_id") or ""),
            customer_name=str(filters.get("customer_name") or ""),
            sale_manager=str(filters.get("sale_manager") or ""),
            sale_user=str(filters.get("sale_user") or ""),
            order_status=str(filters.get("order_status") or ""),
            pay_status=str(filters.get("pay_status") if filters.get("pay_status") is not None else ""),
            test_user_id=str(filters.get("test_user_id") or ""),
            is_confirm=str(filters.get("is_confirm") if filters.get("is_confirm") is not None else ""),
            finish_start=str(filters.get("finish_start") or ""),
            finish_end=str(filters.get("finish_end") or ""),
            page=1,
            page_size=limit,
        )
        return rows
    rows, _ = list_orders(
        order_type=order_type,
        order_id=str(filters.get("order_id") or ""),
        company_name=str(filters.get("customer_name") or filters.get("company_name") or ""),
        supplier_name=str(filters.get("supplier_name") or ""),
        sale_manager=str(filters.get("sale_manager") or ""),
        sale_user=str(filters.get("sale_user") or ""),
        order_status=str(filters.get("order_status") or ""),
        goods_name=str(filters.get("goods_name") or ""),
        order_start=str(filters.get("order_start") or filters.get("finish_start") or ""),
        order_end=str(filters.get("order_end") or filters.get("finish_end") or ""),
        page=1,
        page_size=limit,
    )
    return rows
