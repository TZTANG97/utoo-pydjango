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


# Java UserTypes.name → roleName（UserRoles）；测试主管与销售主管同属「销售主管」权限
_UTOO_TYPE_ROLE = {
    "系统管理员": "系统管理员",
    "公共账号": "公共账号",
    "公司账号": "公司账号",
    "外部合作公司": "外部合作公司",
    "外部公司": "外部公司",
    "销售主管": "销售主管",
    "测试主管": "销售主管",
    "C类销售人员": "C类销售人员",
    "R类人员": "R类人员",
    "H类用户": "H类用户",
    "A类销售人员": "A类销售人员",
    "制单员": "A类销售人员",
    "销售人员": "A类销售人员",
    "内勤主管": "A类销售人员",
    "仓库管理": "A类销售人员",
    "公司基金": "A类销售人员",
    "原厂销售人员": "A类销售人员",
    "外部投资": "A类销售人员",
}


def _resolve_utoo_role_name(utoo_type: str) -> str:
    """对齐 Java UserTypeTools.getUserRoleName。"""
    name = str(utoo_type or "").strip()
    if not name:
        return "A类销售人员"
    if name in _UTOO_TYPE_ROLE:
        return _UTOO_TYPE_ROLE[name]
    row = fetch_one(
        """
        SELECT utr.name AS roleName
        FROM sy_user_type sut
        LEFT JOIN user_type_role utr ON utr.id = sut.role_id
        WHERE sut.type_name = %(n)s AND IFNULL(sut.type, 2) = 2
        LIMIT 1
        """,
        {"n": name},
    )
    role = str((row or {}).get("roleName") or "").strip()
    return role or "A类销售人员"


def _companies_by_syuser(user_id: str) -> list[str]:
    rows = fetch_all(
        """
        SELECT id
        FROM `user`
        WHERE deleteStatus = 0
          AND CAST(syuser_id AS CHAR) = CAST(%(uid)s AS CHAR)
        """,
        {"uid": user_id},
    )
    return [str(r["id"]) for r in (rows or []) if r.get("id") not in (None, "")]


def _has_exp_order_type_perm(user_id: str, order_type: str = "6") -> bool:
    """对齐 Java selListByTypeAndTable(userId, experiment_order, orderType)。"""
    n = scalar(
        """
        SELECT COUNT(1)
        FROM sy_user_ordertype t
        LEFT JOIN order_type ot ON t.type_id = ot.id
        LEFT JOIN order_type_table ott ON ot.table_id = ott.id
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND IFNULL(t.pt_type, 2) = 2
          AND CAST(t.user_id AS CHAR) = CAST(%(uid)s AS CHAR)
          AND ott.table_name = 'experiment_order'
          AND CAST(ott.order_type AS CHAR) = CAST(%(ot)s AS CHAR)
        """,
        {"uid": user_id, "ot": str(order_type)},
    )
    return int(n or 0) > 0


def _companies_from_sy_user_company(user_id: str) -> list[str]:
    rows = fetch_all(
        """
        SELECT company_id AS cid
        FROM sy_user_company
        WHERE CAST(user_id AS CHAR) = CAST(%(uid)s AS CHAR)
          AND company_id IS NOT NULL
        """,
        {"uid": user_id},
    )
    return [str(r["cid"]) for r in (rows or []) if r.get("cid") not in (None, "")]


def build_exp_order_list_scope(
    user: dict[str, Any] | None,
    *,
    order_type: str = "6",
) -> dict[str, Any]:
    """
    对齐 Java ExperimentOrderController.list.ajax 数据范围：
    - filter_list=2 系统管理员：不限制
    - filter_list=0 公共账号：sale_user/add_user/所属公司
    - filter_list=1 外部合作公司：分成/制单/销售
    - filter_list=3 其他（含销售主管/销售人员）：分成/制单/销售/主管/公司绑定
    - filter_list=4 绑定了外部公司账号：分成/制单/销售/主管/公司 syuser
    """
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    if not uid:
        return {"filter_list": 2, "user_id": "", "supplier_ids": []}

    urow = fetch_one(
        "SELECT utoo_type AS utooType FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1",
        {"id": uid},
    )
    utoo = str((urow or {}).get("utooType") or (user or {}).get("utoo_type") or "").strip()
    role = _resolve_utoo_role_name(utoo)
    linked = _companies_by_syuser(uid)

    if role == "系统管理员":
        filter_list = 2
    elif role == "公共账号":
        filter_list = 0
    elif linked:
        filter_list = 4
    elif role == "外部合作公司":
        filter_list = 1
    else:
        filter_list = 3

    # 非销售主管/管理员：预取所属公司 id 列表（supplier_namegl）
    supplier_ids: list[str] = []
    is_sale_mgr_or_admin = role in ("系统管理员", "销售主管")
    if not is_sale_mgr_or_admin:
        supplier_ids = list(linked)
        if _has_exp_order_type_perm(uid, order_type):
            for cid in _companies_from_sy_user_company(uid):
                if cid not in supplier_ids:
                    supplier_ids.append(cid)

    # filter_list 1/3/4 强制带当前用户 id（对齐 Java）
    scope_uid = uid if filter_list in (0, 1, 3, 4) else ""
    if filter_list in (1, 3, 4):
        scope_uid = uid

    return {
        "filter_list": filter_list,
        "user_id": scope_uid,
        "supplier_ids": supplier_ids,
        "sy_order_type": 43 if filter_list in (1, 3, 4) else None,
        "role": role,
        "utoo_type": utoo,
    }


def _append_list_scope_sql(
    where: str,
    params: dict[str, Any],
    scope: dict[str, Any] | None,
    *,
    alias: str = "t",
) -> str:
    """把 Java listPages 的 filter_list 条件拼到 WHERE。"""
    if not scope:
        return where
    fl = int(scope.get("filter_list") or 2)
    uid = str(scope.get("user_id") or "").strip()
    if fl == 2 or not uid:
        return where

    params["scope_uid"] = uid
    params["scope_uid_like"] = f"%{uid}%"
    supplier_ids = [str(x) for x in (scope.get("supplier_ids") or []) if str(x)]
    if fl == 0:
        # sale_user / add_user / supplier_namegl
        parts = [
            f"CAST({alias}.sale_user AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
            f"CAST({alias}.add_user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        ]
        if supplier_ids:
            in_keys = []
            for i, sid in enumerate(supplier_ids):
                k = f"scope_sup_{i}"
                params[k] = sid
                in_keys.append(f"%({k})s")
            parts.append(f"CAST({alias}.supplier_name AS CHAR) IN ({', '.join(in_keys)})")
        where += " AND (" + " OR ".join(parts) + ")"
        return where

    if fl == 1:
        where += f"""
          AND (
            IFNULL({alias}.user_scale_info, '') LIKE %(scope_uid_like)s
            OR IFNULL({alias}.cb_user_scale_info, '') LIKE %(scope_uid_like)s
            OR IFNULL({alias}.salecb_user_scale_info, '') LIKE %(scope_uid_like)s
            OR CAST({alias}.add_user_id AS CHAR) LIKE %(scope_uid_like)s
            OR CAST({alias}.sale_user AS CHAR) LIKE %(scope_uid_like)s
          )
        """
        return where

    if fl == 4:
        where += f"""
          AND (
            IFNULL({alias}.user_scale_info, '') LIKE %(scope_uid_like)s
            OR IFNULL({alias}.cb_user_scale_info, '') LIKE %(scope_uid_like)s
            OR IFNULL({alias}.salecb_user_scale_info, '') LIKE %(scope_uid_like)s
            OR CAST({alias}.add_user_id AS CHAR) LIKE %(scope_uid_like)s
            OR CAST({alias}.sale_user AS CHAR) LIKE %(scope_uid_like)s
            OR CAST({alias}.sale_manager AS CHAR) LIKE %(scope_uid_like)s
            OR (SELECT syuser_id FROM `user` WHERE id = {alias}.supplier_name LIMIT 1) = %(scope_uid)s
          )
        """
        return where

    # filter_list == 3（默认其他角色，含销售主管/销售人员）
    sy_ot = scope.get("sy_order_type")
    extra_company = ""
    if sy_ot not in (None, ""):
        params["scope_sy_ot"] = int(sy_ot)
        extra_company = f"""
            OR (
              {alias}.supplier_name IN (
                SELECT suc.company_id FROM sy_user_company suc
                WHERE CAST(suc.user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
              )
              AND %(scope_sy_ot)s IN (
                SELECT type_id FROM sy_user_ordertype
                WHERE CAST(user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
              )
            )
        """
    where += f"""
      AND (
        IFNULL({alias}.user_scale_info, '') LIKE %(scope_uid_like)s
        OR IFNULL({alias}.cb_user_scale_info, '') LIKE %(scope_uid_like)s
        OR IFNULL({alias}.salecb_user_scale_info, '') LIKE %(scope_uid_like)s
        OR CAST({alias}.add_user_id AS CHAR) LIKE %(scope_uid_like)s
        OR CAST({alias}.sale_user AS CHAR) LIKE %(scope_uid_like)s
        OR CAST({alias}.sale_manager AS CHAR) LIKE %(scope_uid_like)s
        OR {alias}.parent_id IN (
          SELECT ofm.id FROM experiment_order ofm
          WHERE CAST(ofm.sale_user AS CHAR) LIKE %(scope_uid_like)s
             OR CAST(ofm.sale_manager AS CHAR) LIKE %(scope_uid_like)s
        )
        {extra_company}
        OR {alias}.supplier_name IN (
          SELECT id FROM `user` WHERE CAST(syuser_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
        )
      )
    """
    return where


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
    scope: dict[str, Any] | None = None,
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
    elif order_status:
        # 对齐 Java listPages：默认 order_status > 0，再叠加 = status。
        # 筛「已取消」(0) 时 >0 与 =0 互斥，结果为空。
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

    where = _append_list_scope_sql(where, params, scope, alias="t")

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
        # 对齐 Java list_dpt 收款/开票派生状态（已取消不改写）
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
        # 0=已取消：保持原状态，避免被改成「已付款」
        if st not in (0, 50, 55):
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

# 对齐 Java qdorderdetail isqdqx：系统管理员 / 测试人员 / 测试主管可抢；R 类人员不可抢
_GRAB_ALLOWED_UTOO_TYPES = frozenset({"系统管理员", "测试人员", "测试主管"})
_GRAB_DENIED_ROLE_NAME = "R类人员"


def _load_grab_perm_ctx(user_id: str | None) -> dict[str, Any] | None:
    """加载当前用户抢单权限上下文（对齐 Java isqdqx + roleName!=R类人员）。"""
    uid = str(user_id or "").strip()
    if not uid:
        return None
    u = fetch_one(
        """
        SELECT u.utoo_type AS utooType, utr.name AS roleName
        FROM sy_users u
        LEFT JOIN sy_user_type sut
          ON sut.type_name = u.utoo_type AND IFNULL(sut.type, 2) = 2
        LEFT JOIN user_type_role utr ON utr.id = sut.role_id
        WHERE CAST(u.id AS CHAR) = CAST(%(id)s AS CHAR)
        LIMIT 1
        """,
        {"id": uid},
    )
    if not u:
        return None
    utoo = str(u.get("utooType") or "").strip()
    role = str(u.get("roleName") or "").strip() or utoo
    # 模板：#if($!roleName!="R类人员")
    if utoo == _GRAB_DENIED_ROLE_NAME or role == _GRAB_DENIED_ROLE_NAME:
        return {"denied": True, "user_id": uid}
    if utoo in _GRAB_ALLOWED_UTOO_TYPES:
        return {"allowed_all": True, "user_id": uid, "class_ids": set()}
    rows = fetch_all(
        """
        SELECT exp_manage_id AS cid
        FROM sy_user_expmanage
        WHERE CAST(user_id AS CHAR) = CAST(%(uid)s AS CHAR)
        """,
        {"uid": uid},
    )
    class_ids = {str(r.get("cid")) for r in (rows or []) if r.get("cid") not in (None, "")}
    return {"allowed_all": False, "user_id": uid, "class_ids": class_ids}


def _ctx_has_grab_qx(ctx: dict[str, Any] | None, class_id: Any) -> bool:
    """是否具备该子单三级分类的抢单资格（不含池状态校验）。"""
    if not ctx or ctx.get("denied"):
        return False
    if ctx.get("allowed_all"):
        return True
    cid = str(class_id if class_id not in (None, "") else "").strip()
    if not cid:
        return False
    return cid in (ctx.get("class_ids") or set())


def _user_has_grab_qx(*, user_id: str, class_id: Any) -> bool:
    return _ctx_has_grab_qx(_load_grab_perm_ctx(user_id), class_id)


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
        # 下拉传所属公司/进货公司 id，或名称模糊（对齐 Java stockCompanyName）
        where += """ AND (
            q.name LIKE %(company_name)s
            OR qs.name LIKE %(company_name)s
            OR CAST(IFNULL(t.stock_company_name, '') AS CHAR) = %(company_eq)s
            OR CAST(IFNULL(t.customer_name, '') AS CHAR) = %(company_eq)s
            OR CAST(IFNULL(t.supplier_name, '') AS CHAR) = %(company_eq)s
        )"""
        params["company_name"] = f"%{company_name}%"
        params["company_eq"] = company_name
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
        SELECT id, test_user_id AS testUserId, order_status AS orderStatus,
               experiment_class_id AS classId
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not child:
        return False, "子单不存在"
    # 对齐 Java 详情 isqdqx：接口侧补校验，避免仅靠前端隐藏
    if not _user_has_grab_qx(user_id=user_id, class_id=child.get("classId")):
        return False, "无抢单权限"
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
            t.taxes AS taxes,
            t.class_id AS classId,
            t.sale_manager AS saleManagerId,
            t.sale_user AS saleUserId,
            t.supplier_name AS supplierId,
            t.customer_name AS customerId,
            t.custom_user_id AS customUserId,
            t.warehouse_user AS warehouseUserId,
            t.test_address_id AS testAddressId,
            t.company_account_id AS companyAccountId,
            t.out_bill_type_id AS outBillTypeId,
            t.in_bill_type_id AS inBillTypeId,
            obt.name AS outBillTypeName,
            ibt.name AS inBillTypeName,
            IFNULL(bill_cnt.kpCnt, 0) AS invoiceBillCount,
            IFNULL(bill_cnt.skCnt, 0) AS receiveBillCount,
            t.user_scale_info AS userScaleInfo, t.scale_info AS scaleInfo,
            t.salecb_user_scale_info AS salecbUserScaleInfo,
            t.related_order_num AS relatedOrderNum,
            q.name AS companyName,
            u.company_name AS supplierName,
            cu.mobile AS customUserMobile,
            pcu.mobile AS parentCustomUserMobile,
            sm.user_name AS saleManagerName, sm.true_name AS saleManagerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName,
            au.user_name AS addUserName, au.true_name AS addUserTrueName,
            tm.user_name AS testManagerName, tm.true_name AS testManagerTrueName,
            wu.user_name AS warehouseUserName, wu.true_name AS warehouseUserTrueName,
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
        LEFT JOIN `user` cu ON t.custom_user_id = cu.id
        LEFT JOIN `user` pcu ON p.custom_user_id = pcu.id
        LEFT JOIN sy_users sm ON t.sale_manager = sm.id
        LEFT JOIN sy_users su ON t.sale_user = su.id
        LEFT JOIN sy_users au ON t.add_user_id = au.id
        LEFT JOIN sy_users tm ON t.test_manager = tm.id
        LEFT JOIN sy_users wu ON CAST(t.warehouse_user AS CHAR) = CAST(wu.id AS CHAR)
        LEFT JOIN qd_consume_paytype pt ON t.pay_way = pt.id
        LEFT JOIN experiment_manage tc ON t.class_id = tc.id
        LEFT JOIN bill_type obt ON t.out_bill_type_id = obt.id
        LEFT JOIN bill_type ibt ON t.in_bill_type_id = ibt.id
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
    row["warehouseUser"] = str(
        row.get("warehouseUserTrueName") or row.get("warehouseUserName") or "-"
    ).strip() or "-"
    row["stockUser"] = row["warehouseUser"]
    # 历史子单可能未写 add_user_id / warehouse_user，尝试从父单补齐展示
    if _is_child_order_type(ot) and (
        row.get("addUser") in (None, "", "-") or row.get("warehouseUser") in (None, "", "-")
    ):
        parent_pk = row.get("parentPkId")
        if parent_pk not in (None, "", 0, "0"):
            try:
                prow = fetch_one(
                    """
                    SELECT
                        au.true_name AS addTrue, au.user_name AS addName,
                        wu.true_name AS whTrue, wu.user_name AS whName
                    FROM experiment_order p
                    LEFT JOIN sy_users au ON p.add_user_id = au.id
                    LEFT JOIN sy_users wu
                      ON CAST(p.warehouse_user AS CHAR) = CAST(wu.id AS CHAR)
                    WHERE p.id = %(id)s
                    LIMIT 1
                    """,
                    {"id": parent_pk},
                )
                if prow:
                    if row.get("addUser") in (None, "", "-"):
                        row["addUser"] = str(
                            prow.get("addTrue") or prow.get("addName") or "-"
                        ).strip() or "-"
                    if row.get("warehouseUser") in (None, "", "-"):
                        row["warehouseUser"] = str(
                            prow.get("whTrue") or prow.get("whName") or "-"
                        ).strip() or "-"
                        row["stockUser"] = row["warehouseUser"]
            except Exception:
                pass
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
    # 开票类型 / 税率（对齐小程序 order_detail）
    taxes_raw = row.get("taxes")
    if taxes_raw is None or str(taxes_raw).strip() == "":
        row["taxes"] = ""
    else:
        try:
            row["taxes"] = format(float(taxes_raw), "g")
        except (TypeError, ValueError):
            row["taxes"] = str(taxes_raw).strip()
    out_id = row.get("outBillTypeId")
    out_name = str(row.get("outBillTypeName") or "").strip()
    row["outBillTypeName"] = out_name or ""
    row["outBillType"] = (
        {"id": out_id, "name": out_name or "未知"} if out_id not in (None, "", 0, "0") else None
    )
    in_id = row.get("inBillTypeId")
    in_name = str(row.get("inBillTypeName") or "").strip()
    row["inBillTypeName"] = in_name or ""
    row["inBillType"] = (
        {"id": in_id, "name": in_name or "未知"} if in_id not in (None, "", 0, "0") else None
    )
    # 分成信息：毛利带 %；成本为固定金额不带 %
    row["userScaleLabel"] = _format_scale_label(
        str(row.get("userScaleInfo") or row.get("scaleInfo") or "")
    )
    row["costScaleLabel"] = _format_cost_scale_label(str(row.get("salecbUserScaleInfo") or ""))
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
    # type=9/10：样品回收/电话等可回退父单（对齐 Java orderParent / 抢单详情）
    if ot in ("9", "10"):
        rev = row.get("reversoContext")
        if rev is None or str(rev).strip() == "":
            rev = row.get("parentReversoContext")
        row["reversoLabel"] = "是" if str(rev or "") == "1" else "否"
        phone = (
            str(row.get("mobile") or "").strip()
            or str(row.get("parentMobile") or "").strip()
            or str(row.get("shipPhone") or "").strip()
        )
        row["contactPhone"] = phone or "-"
        if not str(row.get("mobile") or "").strip() and phone:
            row["mobile"] = phone
        if ot == "9":
            if not str(row.get("shipAddress") or "").strip():
                row["shipAddress"] = str(row.get("parentSendAddress") or "").strip()
            pv = row.get("parentIsVideo")
            if pv is not None and str(pv).strip() != "":
                row["isVideoLabel"] = "是" if str(pv) in ("1", "true") else "否"
    else:
        rev = row.get("reversoContext")
        row["reversoLabel"] = "是" if str(rev or "") == "1" else "否"
        row["contactPhone"] = str(row.get("mobile") or row.get("shipPhone") or "").strip() or "-"
    # 客户账号：优先 custom_user.mobile，其次订单/父单 mobile（对齐 Java customUser.mobile）
    row["customMobile"] = (
        str(row.get("customUserMobile") or "").strip()
        or str(row.get("mobile") or "").strip()
        or str(row.get("parentCustomUserMobile") or "").strip()
        or str(row.get("parentMobile") or "").strip()
        or str(row.get("contactPhone") or "").strip()
        or "-"
    )
    # mark 为标志位(bigint)，备注文本只用 msg
    row["msg"] = str(row.get("msg") or "").strip()
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
        # 对齐 Java：普通角色 status∈{5,10,20}；管理员/销售主管 status>0 且无票时可编
        # 后台详情统一按「status≠0 且无票」放开编辑按钮（权限在保存侧再约束）
        can_edit = st != 0 and edit_allowed_by_bill
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
    # Java：子单 order_status < 30 可改测试金额
    row["canEditReferencePrice"] = ot == "10" and st < 30
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
    # Java type6：status==30 || is_evaluate==1；type8：status∈{30,50}
    try:
        is_evaluate = int(row.get("isEvaluate") or 0)
    except (TypeError, ValueError):
        is_evaluate = 0
    if ot == "6":
        status_ok_bill = st == 30 or is_evaluate == 1
    else:
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
        # 兼容历史：子单已取消但产品行未释放时，自动恢复为可创建
        try:
            execute(
                """
                UPDATE experiment_order_child c
                SET c.op_status = 1
                WHERE c.order_form_id = %(oid)s
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND IFNULL(c.op_status, 0) = 2
                  AND EXISTS (
                      SELECT 1
                      FROM exp_qd_purchase_order_child p
                      INNER JOIN experiment_order o ON o.id = p.purchase_order_id
                      WHERE p.order_child_id = c.id
                        AND IFNULL(o.order_status, -1) = 0
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM exp_qd_purchase_order_child p2
                      INNER JOIN experiment_order o2 ON o2.id = p2.purchase_order_id
                      WHERE p2.order_child_id = c.id
                        AND IFNULL(o2.order_status, -1) <> 0
                  )
                """,
                {"oid": row["id"]},
            )
        except Exception:
            pass
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


_CHILD_LINE_SELECT = """
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.goods_id AS goodsId, c.goods_brand_id AS goodsBrandId,
            c.experiment_project_id AS projectId,
            c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
            c.experiment_project_name AS projectName,
            c.experiment_class_id AS classId,
            c.experiment_class_name AS className,
            c.experiment_class_name AS deviceName,
            c.goods_price AS price,
            c.reference_price AS referencePrice,
            c.cost_price AS costPrice,
            c.expect_finishtime AS expectFinishTime,
            c.finish_time AS estimateFinish,
            IFNULL(c.expect_finishtime, c.finish_time) AS finishTime,
            c.time_type AS timeType,
            c.mark AS confirmMark,
            c.is_confirm AS isConfirm, c.op_status AS opStatus,
            c.is_meeting AS isMeeting,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.test_user_id AS testUserId, u.user_name AS testUserName,
            u.true_name AS testUserTrueName, c.add_time AS addTime,
            ln.line_num AS platformName,
            got.id AS gotId, got.out_num AS outNum,
            gotc.store_id AS storeId,
            gotc.store_position_id AS storePosId,
            b.block AS storeBlock, p.number AS storeNumber,
            gs.sample_store_name AS sampleStoreName,
            v.meeting_num AS meetingNum, v.setting_time AS settingTime,
            osi.sample_name AS sampleName, osi.sample_num AS sampleNum
"""

_CHILD_LINE_JOINS = """
        LEFT JOIN sy_users u ON c.test_user_id = u.id
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        LEFT JOIN experiment_video v ON c.id = v.child_id
        LEFT JOIN order_sample_information osi ON c.sample_id = osi.id
        LEFT JOIN (
            SELECT t1.* FROM exp_goods_out_treasury_child t1
            LEFT JOIN exp_goods_out_treasury t2 ON t1.out_id = t2.id
            WHERE IFNULL(t2.status, 0) != 3
        ) gotc ON c.id = gotc.order_child_id
        LEFT JOIN sample_goods_storehouse gs ON gotc.store_id = gs.id
        LEFT JOIN sample_goods_store_position p ON gotc.store_position_id = p.id
        LEFT JOIN sample_goods_store_block b ON p.sample_block_id = b.id
        LEFT JOIN (
            SELECT * FROM exp_goods_out_treasury WHERE IFNULL(status, 0) != 3
        ) got ON gotc.out_id = got.id
"""


def _fetch_children_basic(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        f"""
        SELECT {_CHILD_LINE_SELECT}
        FROM experiment_order_child c
        {_CHILD_LINE_JOINS}
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )
    if rows:
        return rows
    return fetch_all(
        f"""
        SELECT {_CHILD_LINE_SELECT}
        FROM exp_qd_purchase_order_child poc
        JOIN experiment_order_child c ON poc.order_child_id = c.id
        {_CHILD_LINE_JOINS}
        WHERE poc.purchase_order_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )


def _fetch_children_fallback(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.goods_id AS goodsId, c.goods_brand_id AS goodsBrandId,
            c.experiment_project_id AS projectId,
            c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
            c.experiment_project_name AS projectName,
            c.experiment_class_name AS className,
            c.experiment_class_name AS deviceName,
            c.goods_price AS price,
            c.reference_price AS referencePrice,
            c.cost_price AS costPrice,
            c.expect_finishtime AS expectFinishTime,
            c.finish_time AS estimateFinish,
            IFNULL(c.expect_finishtime, c.finish_time) AS finishTime,
            c.time_type AS timeType,
            c.mark AS confirmMark,
            c.is_confirm AS isConfirm, c.op_status AS opStatus,
            c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.test_user_id AS testUserId, u.user_name AS testUserName,
            u.true_name AS testUserTrueName, c.add_time AS addTime,
            ln.line_num AS platformName
        FROM experiment_order_child c
        LEFT JOIN sy_users u ON c.test_user_id = u.id
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )
    if rows:
        return rows
    return fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.goods_id AS goodsId, c.goods_brand_id AS goodsBrandId,
            c.experiment_project_id AS projectId,
            c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
            c.experiment_project_name AS projectName,
            c.experiment_class_name AS className,
            c.experiment_class_name AS deviceName,
            c.goods_price AS price,
            c.reference_price AS referencePrice,
            c.cost_price AS costPrice,
            c.expect_finishtime AS expectFinishTime,
            c.finish_time AS estimateFinish,
            IFNULL(c.expect_finishtime, c.finish_time) AS finishTime,
            c.time_type AS timeType,
            c.mark AS confirmMark,
            c.is_confirm AS isConfirm, c.op_status AS opStatus,
            c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.test_user_id AS testUserId, u.user_name AS testUserName,
            u.true_name AS testUserTrueName, c.add_time AS addTime,
            ln.line_num AS platformName
        FROM exp_qd_purchase_order_child poc
        JOIN experiment_order_child c ON poc.order_child_id = c.id
        LEFT JOIN sy_users u ON c.test_user_id = u.id
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        WHERE poc.purchase_order_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )


def _attach_child_runtime_fields(rows: list[dict[str, Any]]) -> None:
    """补齐测试时长/复测/附件等 Java getChildsByPurchaseId2 后处理字段。"""
    if not rows:
        return
    ids: list[int] = []
    for r in rows:
        try:
            ids.append(int(r["id"]))
        except (TypeError, ValueError, KeyError):
            continue
    if not ids:
        return
    id_csv = ",".join(str(i) for i in ids)

    logs_by_cid: dict[int, list[dict[str, Any]]] = {}
    try:
        log_rows = fetch_all(
            f"""
            SELECT order_child_id AS childId, start_time AS startTime, end_time AS endTime
            FROM experiment_log
            WHERE order_child_id IN ({id_csv}) AND IFNULL(deleteStatus, 0) = 0
            ORDER BY addTime DESC
            """
        )
        for lg in log_rows:
            try:
                cid = int(lg["childId"])
            except (TypeError, ValueError, KeyError):
                continue
            logs_by_cid.setdefault(cid, []).append(lg)
    except Exception:
        pass

    retest_by_cid: dict[int, dict[str, Any]] = {}
    try:
        rt_rows = fetch_all(
            f"""
            SELECT id, orderId, order_id AS order_id, applyStatus
            FROM retest_application
            WHERE orderId IN ({id_csv}) AND IFNULL(deleteStatus, 0) = 0
              AND IFNULL(applyStatus, 0) = 1
            ORDER BY id DESC
            """
        )
        for rt in rt_rows:
            key = str(rt.get("orderId") or "").strip()
            if not key.isdigit():
                continue
            cid = int(key)
            if cid not in retest_by_cid:
                retest_by_cid[cid] = {
                    "id": rt.get("id"),
                    "orderId": rt.get("orderId"),
                    "order_id": rt.get("order_id"),
                }
    except Exception:
        pass

    files_by_cid: dict[int, list[dict[str, Any]]] = {}
    confirm_by_cid: dict[int, list[dict[str, Any]]] = {}
    try:
        from apps.orders.services.sale_detail_enrich import accessory_url, enrich_accessory_rows
        from apps.core.services.sysconfig import get_config_row, image_web_server

        config = get_config_row()
        base = image_web_server(config) or ""
        acc_rows = fetch_all(
            f"""
            SELECT * FROM accessory
            WHERE IFNULL(deleteStatus, 0) = 0
              AND child_of_id IN ({id_csv})
              AND type IN (4, 30)
            ORDER BY id ASC
            """
        )
        enriched = enrich_accessory_rows(acc_rows, base)
        for a in enriched:
            a["url"] = accessory_url(base, a)
            try:
                cid = int(a.get("child_of_id") or a.get("childOfId") or 0)
            except (TypeError, ValueError):
                continue
            try:
                tp = int(a.get("type") or 0)
            except (TypeError, ValueError):
                tp = 0
            item = {
                "id": a.get("id"),
                "name": a.get("name"),
                "path": a.get("path"),
                "info": a.get("info") or a.get("name"),
                "url": a.get("url"),
                "type": tp,
            }
            if tp == 4:
                files_by_cid.setdefault(cid, []).append(item)
            elif tp == 30:
                confirm_by_cid.setdefault(cid, []).append(item)
    except Exception:
        pass

    for r in rows:
        try:
            cid = int(r["id"])
        except (TypeError, ValueError, KeyError):
            continue
        store = str(r.get("sampleStoreName") or "").strip()
        block = str(r.get("storeBlock") or "").strip()
        number = str(r.get("storeNumber") or "").strip()
        pos = f"{block} - {number}".strip(" -") if (block or number) else ""
        r["storePosition"] = f"{store}; {pos}".strip("; ") if store or pos else ""
        st = r.get("settingTime")
        r["settingTime"] = str(st)[:19] if st else ""
        mn = r.get("meetingNum")
        r["meetingNum"] = str(mn or "").strip()
        r["outNum"] = str(r.get("outNum") or "").strip()
        r["gotId"] = r.get("gotId")
        r["sampleShow"] = r.get("sampleId") not in (None, "", 0, "0")
        r["sampleInfo"] = {
            "sampleName": r.get("sampleName") or "",
            "sampleNum": r.get("sampleNum") or "",
            "sampleId": r.get("sampleId"),
        }
        r["testFiles"] = files_by_cid.get(cid, [])
        r["accessoryList"] = confirm_by_cid.get(cid, [])
        r["retestApplication"] = retest_by_cid.get(cid)
        r["retestOrderNo"] = (
            str((retest_by_cid.get(cid) or {}).get("order_id") or "")
            if cid in retest_by_cid
            else ""
        )
        try:
            tt = int(r.get("timeType")) if r.get("timeType") is not None else 0
        except (TypeError, ValueError):
            tt = 0
        r["timeType"] = tt
        logs = logs_by_cid.get(cid, [])
        jt = ""
        total_min = 0.0
        for lg in logs:
            et = lg.get("endTime")
            stt = lg.get("startTime")
            if et and not jt:
                jt = str(et)[:19]
            if et and stt:
                try:
                    from datetime import datetime

                    def _parse(v: Any):
                        s = str(v)[:19]
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                            try:
                                return datetime.strptime(s, fmt)
                            except ValueError:
                                continue
                        return None

                    a = _parse(stt)
                    b = _parse(et)
                    if a and b and b >= a:
                        total_min += (b - a).total_seconds() / 60.0
                except Exception:
                    pass
        r["jtTime"] = jt
        if tt == 1:
            r["actualFinish"] = round(total_min / 60.0, 2)
            r["timeTypeLabel"] = "小时"
        elif tt == 2:
            r["actualFinish"] = round(total_min / (60.0 * 24.0), 2)
            r["timeTypeLabel"] = "天"
        else:
            r["actualFinish"] = round(total_min, 2)
            r["timeTypeLabel"] = "分钟" if tt == 3 else ""
        r["sjsj"] = r["actualFinish"]
        est = r.get("estimateFinish")
        r["estimateFinish"] = str(est) if est not in (None, "") else "0"
        eft = r.get("expectFinishTime")
        r["expectFinishTime"] = str(eft)[:19] if eft else ""


def list_order_children(
    order_id: int, *, viewer_user_id: str | None = None
) -> list[dict[str, Any]]:
    """对齐 Java getChildsByPurchaseId2：产品行 + 仓位/云视频/样品管理单等。

    canGrab 对齐 Java qdorderdetail：待抢池 + 状态<=36 + isqdqx（角色/三级分类）且非 R 类。
    """
    try:
        rows = _fetch_children_basic(order_id)
    except Exception:
        rows = _fetch_children_fallback(order_id)
    grab_ctx = _load_grab_perm_ctx(viewer_user_id)
    for r in rows:
        r["orderStatusLabel"] = _child_line_status_label(r.get("orderStatus"))
        r["testUserName"] = str(r.get("testUserTrueName") or r.get("testUserName") or "-")
        pool = str(r.get("testUserId") or "") == GRAB_POOL_TEST_USER_ID
        if pool:
            r["testUserName"] = "待抢单"
        try:
            child_st = int(r.get("orderStatus")) if r.get("orderStatus") is not None else -1
        except (TypeError, ValueError):
            child_st = -1
        # 对齐 Java child.put("isqdqx", isqdqx)；前端仍用 canGrab 控制按钮
        isqdqx = _ctx_has_grab_qx(grab_ctx, r.get("classId"))
        r["isqdqx"] = isqdqx
        r["canGrab"] = bool(pool and child_st <= 36 and isqdqx)
        try:
            conf_i = int(r.get("isConfirm")) if r.get("isConfirm") is not None else 0
        except (TypeError, ValueError):
            conf_i = 0
        r["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
        ft = r.get("finishTime")
        r["finishTime"] = str(ft)[:19] if ft else ""
        if not r.get("deviceName"):
            r["deviceName"] = r.get("className") or ""
    _attach_child_runtime_fields(rows)
    return rows


def list_order_logs(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            l.id, l.addTime, l.log_info AS logInfo, l.log_user_id AS logUserId,
            COALESCE(u.true_name, u.user_name, eu.trueName, eu.userName) AS logUserName
        FROM experiment_order_log l
        LEFT JOIN sy_users u ON CAST(l.log_user_id AS CHAR) = CAST(u.id AS CHAR)
        LEFT JOIN exp_user eu ON CAST(l.log_user_id AS CHAR) = CAST(eu.id AS CHAR)
        WHERE l.of_id = %(oid)s AND IFNULL(l.deleteStatus, 0) = 0
        ORDER BY l.addTime DESC
        LIMIT 200
        """,
        {"oid": order_id},
    )
    for r in rows:
        r["logUser"] = str(r.get("logUserName") or "-")
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
            t.is_confirm AS isConfirm, t.order_type AS orderType,
            u.company_name AS supplierName,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName
        FROM experiment_order t
        LEFT JOIN `user` u ON t.supplier_name = u.id
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
        r["supplierName"] = r.get("supplierName") or "-"
        try:
            conf_i = int(r.get("isConfirm")) if r.get("isConfirm") is not None else 0
        except (TypeError, ValueError):
            conf_i = 0
        r["confirmLabel"] = "已确认" if conf_i == 1 else "未确认"
        add_t = r.get("addTime")
        r["addTime"] = str(add_t)[:19] if add_t else ""
        otm = r.get("orderTime") or add_t
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
            t.order_time AS orderTime, t.addTime, t.invoiceType AS invoiceType,
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
        r["invoiceLabel"] = "是" if str(r.get("invoiceType") or "") == "1" else "否"
        add_t = r.get("addTime")
        r["addTime"] = str(add_t)[:19] if add_t else ""
        otm = r.get("orderTime") or add_t
        r["orderTime"] = str(otm)[:19] if otm else ""
        ordered.append(r)
    return ordered


def _enrich_accessory_urls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from apps.core.services.sysconfig import get_config_row, image_web_server
    from apps.orders.services.sale_detail_enrich import accessory_url, enrich_accessory_rows

    config = get_config_row()
    base = image_web_server(config)
    out = enrich_accessory_rows(rows, base)
    for a in out:
        a["url"] = accessory_url(base, a)
        if not a.get("info"):
            a["info"] = a.get("name") or ""
    return out


def list_order_files(order_id: int) -> list[dict[str, Any]]:
    """对齐 Java getByExpOfId：订单资料（排除 type=5 发票资料）。"""
    from apps.orders.repositories import accessory_list as acc_repo

    rows = acc_repo.load_accessories(exp_of_id=order_id, exclude_types=(5,))
    return _enrich_accessory_urls(rows)


def list_invoice_files(order_id: int) -> list[dict[str, Any]]:
    """发票资料：accessory.type = 5。"""
    from apps.orders.repositories import accessory_list as acc_repo

    rows = acc_repo.load_accessories(exp_of_id=order_id, file_type=5)
    return _enrich_accessory_urls(rows)


def update_order_msg(*, order_id: int, msg: str) -> tuple[bool, str]:
    """对齐 Java msgBlur：更新订单备注（msg；mark 为标志位勿写文本）。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    text = (msg or "")[:2000]
    try:
        execute(
            "UPDATE experiment_order SET msg = %(msg)s WHERE id = %(id)s",
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


def get_order_detail_bundle(
    order_id: int, *, viewer_user_id: str | None = None
) -> dict[str, Any] | None:
    """Java orderdetail 聚合：主信息 + 产品行 + 关联子单 + 关联订单 + 操作日志 + 订单资料。"""
    row = get_order(order_id)
    if not row:
        return None
    ot = str(row.get("orderType") or "")
    children = list_order_children(order_id, viewer_user_id=viewer_user_id)
    logs = list_order_logs(order_id)
    linked: list[dict[str, Any]] = []
    if ot == "6":
        linked = list_linked_child_orders(order_id, child_order_type="10")
    elif ot == "8":
        linked = list_linked_child_orders(order_id, child_order_type="9")
    related = list_related_orders(row.get("relatedOrderNum"))
    files = list_order_files(order_id)
    invoice_files = list_invoice_files(order_id)
    yyd_files = [f for f in files if str(f.get("type") or "") == "6"]
    can_view_share = _viewer_can_see_share(viewer_user_id)
    row["canViewShareInfo"] = can_view_share
    if not can_view_share:
        row["userScaleLabel"] = ""
        row["costScaleLabel"] = ""
        row["userScaleInfo"] = ""
        row["scaleInfo"] = ""
        row["salecbUserScaleInfo"] = ""
        row["canShareRatio"] = False
    return {
        **row,
        "children": children,
        "logs": logs,
        "linkedOrders": linked,
        "relatedOrders": related,
        "files": files,
        "invoiceFiles": invoice_files,
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


def _release_purchase_child_lines(purchase_order_id: int) -> None:
    """取消子单后释放产品行，便于主单再次创建子订单。"""
    if not purchase_order_id:
        return
    try:
        execute(
            """
            UPDATE experiment_order_child c
            INNER JOIN exp_qd_purchase_order_child p ON p.order_child_id = c.id
            SET c.op_status = 1
            WHERE p.purchase_order_id = %(oid)s
            """,
            {"oid": purchase_order_id},
        )
    except Exception:
        pass


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
    if ot in ("9", "10"):
        _release_purchase_child_lines(order_id)
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
            _release_purchase_child_lines(cid)
            _write_order_log(cid, f"主单取消，同步取消子订单 {c.get('orderId') or ''}".strip())
    return True, "订单已取消"


def submit_audit(*, order_id: int, staff_user_id: str | int | None = None) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canSubmitAudit"):
        return False, "当前状态不可提交审核"
    _set_order_status(order_id, 20)
    _write_order_log(order_id, "提交审核", user_id=staff_user_id)
    return True, "已提交审核"


def withdraw_audit(*, order_id: int, staff_user_id: str | int | None = None) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canWithdrawAudit"):
        return False, "当前状态不可取消审核申请"
    _set_order_status(order_id, 5)
    _write_order_log(order_id, "取消审核申请", user_id=staff_user_id)
    return True, "已取消审核申请"


def cost_settle_sure(
    *, order_id: int, staff_user_id: str | int | None = None
) -> tuple[bool, str]:
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
    _write_order_log(order_id, "所有成本已结清", user_id=staff_user_id)
    # Java costSettleSure：结清后对未分账收款补分钱
    try:
        from apps.admin_experiment.services.split_money import try_split_on_settle

        try_split_on_settle(order_id)
    except Exception as exc:
        return True, f"已标记成本结清（分钱补分失败：{exc}）"
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


def _format_scale_label(raw: str) -> str:
    """userId_value,... -> 「姓名 比例%；...」便于详情展示（毛利分成）。"""
    pairs = _parse_scale_pairs(raw or "")
    if not pairs:
        return (raw or "").strip()
    return "；".join(f"{_user_display_name(uid)} {val}%" for uid, val in pairs)


def _format_cost_scale_label(raw: str) -> str:
    """成本分成按固定金额展示，不加 %（对齐 Java / 小程序）。"""
    pairs = _parse_scale_pairs(raw or "")
    if not pairs:
        return (raw or "").strip()
    return "；".join(f"{_user_display_name(uid)} {val}" for uid, val in pairs)


def _viewer_can_see_share(viewer_user_id: str | int | None) -> bool:
    """测试主管/测试人员及 R/H 类不可看分成信息。"""
    uid = str(viewer_user_id or "").strip()
    if not uid:
        return True
    u = fetch_one(
        """
        SELECT utoo_type AS utooType
        FROM sy_users
        WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR)
        LIMIT 1
        """,
        {"id": uid},
    )
    utoo = str((u or {}).get("utooType") or "").strip()
    if "测试主管" in utoo:
        return False
    if "测试人员" in utoo and "测试主管" not in utoo:
        return False
    role = _resolve_utoo_role_name(utoo)
    if role in ("R类人员", "H类用户"):
        return False
    return True


def update_share_ratio(
    *,
    order_id: int,
    user_scale_info: str = "",
    salecb_user_scale_info: str = "",
    scale_info: str = "",
    staff_user_id: str | int | None = None,
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
    _write_order_log(order_id, "".join(log_parts)[:500], user_id=staff_user_id)
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


def save_finish_times(
    *, order_id: int, items: list[dict[str, Any]], staff_user_id: str | int | None = None
) -> tuple[bool, str]:
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
        ft = (
            it.get("expectFinishTime")
            or it.get("expect_finishtime")
            or it.get("finishTime")
            or it.get("finish_time")
            or ""
        )
        ft = str(ft).strip()
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
    if updated <= 0:
        return False, "没有可保存的明细"
    _write_order_log(order_id, f"保存预计完成时间（{updated} 行）", user_id=staff_user_id)
    return True, "保存成功"


def save_child_reference_price(
    *,
    child_id: int,
    reference_price: Any,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java saveReferencePrice.ajax。"""
    row = fetch_one(
        """
        SELECT c.id, c.order_form_id AS orderFormId, poc.purchase_order_id AS purchaseOrderId
        FROM experiment_order_child c
        LEFT JOIN exp_qd_purchase_order_child poc ON poc.order_child_id = c.id
        WHERE c.id = %(id)s AND IFNULL(c.delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": child_id},
    )
    if not row:
        return False, "子订单不存在"
    try:
        price = float(reference_price)
    except (TypeError, ValueError):
        return False, "请输入有效的测试金额"
    if price < 0:
        return False, "请输入有效的测试金额"
    execute(
        "UPDATE experiment_order_child SET reference_price = %(p)s WHERE id = %(id)s",
        {"p": price, "id": child_id},
    )
    oid = row.get("purchaseOrderId") or row.get("orderFormId")
    if oid:
        try:
            _write_order_log(int(oid), f"修改测试金额为 {price}", user_id=staff_user_id)
        except Exception:
            pass
    return True, "保存成功"


def update_child_time_type(
    *,
    child_id: int,
    time_type: Any,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java updateTimeType.ajax。"""
    row = fetch_one(
        """
        SELECT c.id, poc.purchase_order_id AS purchaseOrderId, c.order_form_id AS orderFormId
        FROM experiment_order_child c
        LEFT JOIN exp_qd_purchase_order_child poc ON poc.order_child_id = c.id
        WHERE c.id = %(id)s AND IFNULL(c.delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": child_id},
    )
    if not row:
        return False, "子订单不存在"
    try:
        tt = int(time_type)
    except (TypeError, ValueError):
        return False, "时间单位无效"
    if tt not in (1, 2, 3):
        return False, "时间单位无效"
    execute(
        "UPDATE experiment_order_child SET time_type = %(tt)s WHERE id = %(id)s",
        {"tt": tt, "id": child_id},
    )
    oid = row.get("purchaseOrderId") or row.get("orderFormId")
    if oid:
        try:
            _write_order_log(int(oid), f"修改实际完成时间单位为 {tt}", user_id=staff_user_id)
        except Exception:
            pass
    return True, "保存成功"


def build_more_info(order_id: int) -> dict[str, Any] | None:
    """对齐 Java getConsultByOrderId 弹窗：寄回地址/收件人/电话/汇款账户/实验测试地址。"""
    row = get_order(order_id)
    if not row:
        return None
    test_address = ""
    tid = row.get("testAddressId")
    if tid not in (None, "", 0, "0"):
        try:
            addr = fetch_one(
                """
                SELECT address, true_name, mobile
                FROM test_address
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": tid},
            )
            if addr:
                test_address = str(addr.get("address") or "").strip()
        except Exception:
            test_address = ""
    bank_card = ""
    bank_name = ""
    company_acc = ""
    aid = row.get("companyAccountId")
    if aid not in (None, "", 0, "0"):
        try:
            acc = fetch_one(
                """
                SELECT company_name, bankCardNum, bank
                FROM company_account_info
                WHERE id = %(id)s
                LIMIT 1
                """,
                {"id": aid},
            )
            if acc:
                bank_card = str(acc.get("bankCardNum") or "").strip()
                bank_name = str(acc.get("bank") or "").strip()
                company_acc = " ".join(
                    x for x in [str(acc.get("company_name") or "").strip(), bank_card, bank_name] if x
                )
        except Exception:
            pass
    return {
        "shipAddress": row.get("shipAddress") or "",
        "shipUser": row.get("shipUser") or "",
        "shipPhone": row.get("shipPhone") or "",
        "bankCardNum": bank_card,
        "bankName": bank_name,
        "companyAccount": company_acc,
        "testAddress": test_address,
        # 兼容旧前端字段（不再作为主展示）
        "orderId": row.get("orderId"),
        "customerName": row.get("customerName") or row.get("companyName"),
        "supplierName": row.get("supplierName"),
        "mark": row.get("mark"),
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
    order_time: str = "",
    collection_time: str = "",
    currency_type: Any = None,
    pay_way: Any = None,
    invoice_type: Any = None,
    reverso_context: Any = None,
    taxes: Any = None,
    out_bill_type_id: Any = None,
    sale_manager: Any = None,
    sale_user: Any = None,
    supplier_id: Any = None,
    class_id: Any = None,
    test_address_id: Any = None,
    company_account_id: Any = None,
    is_video: Any = None,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """编辑订单主字段；对齐 Java：编辑后按原状态回退以便再次审核，日志追加不清空。"""
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
    if order_time is not None and str(order_time).strip():
        sets.append("order_time = %(order_time)s")
        params["order_time"] = str(order_time).strip()[:19]
    if collection_time is not None and str(collection_time).strip():
        sets.append("collection_time = %(collection_time)s")
        params["collection_time"] = str(collection_time).strip()[:200]
    if total_price is not None and str(total_price) != "":
        try:
            params["tp"] = float(total_price)
            sets.append("totalPrice = %(tp)s")
        except (TypeError, ValueError):
            pass
    if currency_type not in (None, ""):
        try:
            params["currency_type"] = int(currency_type)
            sets.append("currency_type = %(currency_type)s")
        except (TypeError, ValueError):
            pass
    if pay_way not in (None, ""):
        try:
            params["pay_way"] = int(pay_way)
            sets.append("pay_way = %(pay_way)s")
        except (TypeError, ValueError):
            pass
    if invoice_type not in (None, ""):
        # 1/0 或 ON/OFF
        inv = str(invoice_type).strip().upper()
        params["invoice_type"] = 1 if inv in ("1", "ON", "TRUE", "YES") else 0
        sets.append("invoiceType = %(invoice_type)s")
    if reverso_context not in (None, ""):
        rev = str(reverso_context).strip().upper()
        params["reverso_context"] = "ON" if rev in ("1", "ON", "TRUE", "YES") else "OFF"
        sets.append("reverso_context = %(reverso_context)s")
    if taxes not in (None, ""):
        try:
            params["taxes"] = float(taxes)
            sets.append("taxes = %(taxes)s")
        except (TypeError, ValueError):
            params["taxes"] = str(taxes)[:20]
            sets.append("taxes = %(taxes)s")
    for key, col in (
        ("out_bill_type_id", "out_bill_type_id"),
        ("sale_manager", "sale_manager"),
        ("sale_user", "sale_user"),
        ("supplier_id", "supplier_name"),
        ("class_id", "class_id"),
        ("test_address_id", "test_address_id"),
        ("company_account_id", "company_account_id"),
    ):
        val = locals().get(key)
        if val not in (None, ""):
            try:
                params[key] = int(val)
                sets.append(f"{col} = %({key})s")
            except (TypeError, ValueError):
                pass
    if is_video not in (None, ""):
        try:
            params["is_video"] = 1 if int(is_video) else 0
        except (TypeError, ValueError):
            params["is_video"] = 1 if str(is_video).strip().upper() in ("1", "ON", "TRUE") else 0
        sets.append("is_video = %(is_video)s")
    # 对齐 Java update：status==10→5；status==66→67；status>=30→20（可再次审核）
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    next_st = None
    if st == 10:
        next_st = 5
    elif st == 66:
        next_st = 67
    elif st >= 30:
        next_st = 20
    if next_st is not None:
        sets.append("order_status = %(next_st)s")
        params["next_st"] = next_st
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
    _write_order_log(order_id, "编辑订单", user_id=staff_user_id)
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
    staff_user_id: str | int | None = None,
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

    def _as_str_list(raw: Any) -> list[str]:
        if raw is None or raw == "":
            return []
        if isinstance(raw, str):
            return [x.strip() for x in raw.split(",")]
        if isinstance(raw, (list, tuple)):
            return [str(x).strip() for x in raw]
        return [str(raw).strip()]

    test_user_ids = _as_str_list(form.get("testUserIds") or form.get("test_user_ids"))
    cost_prices = _as_str_list(form.get("costPrices") or form.get("cost_prices"))
    finish_times = _as_str_list(form.get("finishTimes") or form.get("finish_times"))
    line_ids = _as_str_list(form.get("lineIds") or form.get("line_ids"))

    if child_ot == "9":
        if len(test_user_ids) != len(ids) or any(not t for t in test_user_ids):
            return False, "所选分包测试人员不能为空", None
        if len(cost_prices) != len(ids) or any(not c for c in cost_prices):
            return False, "所选分包单价不能为空", None
    if child_ot == "10":
        if line_ids and len(line_ids) != len(ids):
            return False, "实验平台数量与所选产品行不一致", None
        if len(ids) and (not line_ids or any(not x for x in line_ids)):
            return False, "请选择实验平台", None
        if test_user_ids and len(test_user_ids) != len(ids):
            return False, "测试人员数量与所选产品行不一致", None
        if len(ids) and (not test_user_ids or any(not x for x in test_user_ids)):
            return False, "请选择测试人员", None

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
    add_uid = str(staff_user_id or "").strip()

    try:
        new_id = execute_insert(
            """
            INSERT INTO experiment_order
                (addTime, deleteStatus, order_id, order_type, order_status, parent_id,
                 totalPrice, sale_manager, sale_user, customer_name, supplier_name,
                 currency_type, invoiceType, is_confirm, cost_settle, add_user_id)
            SELECT
                NOW(), 0, %(ono)s, %(ot)s, %(st)s, id,
                %(tp)s,
                COALESCE(NULLIF(%(sm)s, ''), sale_manager),
                sale_user, customer_name, supplier_name,
                %(ct)s, %(inv)s, 0, 0, NULLIF(%(au)s, '')
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
                "au": add_uid,
            },
        )
    except Exception:
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
        if new_id and add_uid:
            try:
                execute(
                    "UPDATE experiment_order SET add_user_id = %(au)s WHERE id = %(id)s",
                    {"au": add_uid, "id": new_id},
                )
            except Exception:
                pass
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
    elif child_ot == "10":
        # 对齐 Java experimentChildOrder/submitOrder：客户/公司/账号/主管/销售/仓库/平台等
        sale_user = str(form.get("saleUser") or form.get("sale_user") or "").strip()
        warehouse_user = str(
            form.get("warehouseUser")
            or form.get("warehouse_user")
            or form.get("stockUser")
            or form.get("stock_user")
            or ""
        ).strip()
        customer_name = str(
            form.get("customerName")
            or form.get("customer_name")
            or form.get("customerId")
            or form.get("clientId")
            or ""
        ).strip()
        supplier_name = str(
            form.get("supplierName")
            or form.get("supplier_name")
            or form.get("supplierId")
            or form.get("companyId")
            or ""
        ).strip()
        custom_user_id = str(
            form.get("customUserId")
            or form.get("custom_user_id")
            or form.get("customerAccount")
            or ""
        ).strip()
        try:
            execute(
                """
                UPDATE experiment_order
                SET sale_manager = COALESCE(NULLIF(%(sm)s, ''), sale_manager),
                    sale_user = COALESCE(NULLIF(%(su)s, ''), sale_user),
                    warehouse_user = COALESCE(NULLIF(%(wu)s, ''), warehouse_user),
                    customer_name = COALESCE(NULLIF(%(cn)s, ''), customer_name),
                    supplier_name = COALESCE(NULLIF(%(sn)s, ''), supplier_name),
                    custom_user_id = COALESCE(NULLIF(%(cu)s, ''), custom_user_id),
                    order_time = NULLIF(%(otm)s, ''),
                    delivery_time = NULLIF(%(dt)s, ''),
                    mark = NULLIF(%(mk)s, ''),
                    msg = NULLIF(%(mk)s, '')
                WHERE id = %(id)s
                """,
                {
                    "id": new_id,
                    "sm": sale_manager or "",
                    "su": sale_user or "",
                    "wu": warehouse_user or "",
                    "cn": customer_name if customer_name.isdigit() else "",
                    "sn": supplier_name if supplier_name.isdigit() else "",
                    "cu": custom_user_id if custom_user_id.isdigit() else "",
                    "otm": order_time[:19] if order_time else "",
                    "dt": delivery_time[:19] if delivery_time else "",
                    "mk": msg[:500] if msg else None,
                },
            )
        except Exception:
            try:
                execute(
                    """
                    UPDATE experiment_order
                    SET sale_manager = COALESCE(NULLIF(%(sm)s, ''), sale_manager),
                        sale_user = COALESCE(NULLIF(%(su)s, ''), sale_user),
                        order_time = NULLIF(%(otm)s, ''),
                        delivery_time = NULLIF(%(dt)s, ''),
                        mark = NULLIF(%(mk)s, ''),
                        msg = NULLIF(%(mk)s, '')
                    WHERE id = %(id)s
                    """,
                    {
                        "id": new_id,
                        "sm": sale_manager or "",
                        "su": sale_user or "",
                        "otm": order_time[:19] if order_time else "",
                        "dt": delivery_time[:19] if delivery_time else "",
                        "mk": msg[:500] if msg else None,
                    },
                )
            except Exception:
                pass
        # 订单资料：创建前上传的 accessory id 列表
        orderdata = form.get("orderdata") or form.get("orderData") or form.get("fileIds") or ""
        file_ids = _as_str_list(orderdata)
        for aid in file_ids:
            if not aid.isdigit():
                continue
            try:
                execute(
                    """
                    UPDATE accessory
                    SET exp_of_id = %(oid)s, type = IFNULL(NULLIF(type, 0), 3)
                    WHERE id = %(aid)s AND IFNULL(deleteStatus, 0) = 0
                    """,
                    {"oid": new_id, "aid": int(aid)},
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
        # 更新测试员 / 分包单价 / 预计完成 / 实验平台
        tu = test_user_ids[i] if i < len(test_user_ids) else ""
        cp = cost_prices[i] if i < len(cost_prices) else ""
        ft = finish_times[i] if i < len(finish_times) else ""
        lid = line_ids[i] if i < len(line_ids) else ""
        if tu or cp or ft or lid:
            try:
                execute(
                    """
                    UPDATE experiment_order_child
                    SET test_user_id = COALESCE(NULLIF(%(tu)s, ''), test_user_id),
                        cost_price = COALESCE(NULLIF(%(cp)s, ''), cost_price),
                        reference_price = COALESCE(NULLIF(%(cp)s, ''), reference_price),
                        expect_finishtime = COALESCE(NULLIF(%(ft)s, ''), expect_finishtime),
                        line_id = COALESCE(NULLIF(%(lid)s, ''), line_id),
                        op_status = 2,
                        order_status = CASE
                            WHEN IFNULL(order_status, 0) < 2 THEN 2
                            ELSE order_status
                        END
                    WHERE id = %(cid)s AND order_form_id = %(oid)s
                    """,
                    {
                        "tu": tu,
                        "cp": cp,
                        "ft": ft[:19] if ft else "",
                        "lid": lid if str(lid).isdigit() else "",
                        "cid": cid,
                        "oid": parent_id,
                    },
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
    _write_order_log(
        parent_id,
        f"创建{'实验' if child_ot == '10' else '分包'}子订单 {new_no}",
        user_id=staff_user_id,
    )
    _write_order_log(
        new_id,
        "子订单创建并提交审核" if init_status == 20 else "子订单创建",
        user_id=staff_user_id,
    )
    return True, "创建成功", int(new_id)


def _gen_order_seq_code(n: int) -> str:
    """对齐 Java OrderFormUtils.genCode：不足 5 位左补 0。"""
    if n < 100000:
        return f"{n:05d}"
    return str(n)


def _manage_ennames(class_id: Any) -> tuple[str, str, str]:
    """按三级类目向上取 enname1/enname2/enname3，用于订单号。"""
    en1 = en2 = en3 = ""
    try:
        cid = int(class_id) if class_id not in (None, "") else 0
    except (TypeError, ValueError):
        cid = 0
    if not cid:
        return en1, en2, en3
    row = fetch_one(
        "SELECT id, parent_id, enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
        {"id": cid},
    )
    if not row:
        return en1, en2, en3
    en3 = str(row.get("enname") or "")
    pid = row.get("parent_id")
    if pid:
        sec = fetch_one(
            "SELECT id, parent_id, enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
            {"id": pid},
        )
        if sec:
            en2 = str(sec.get("enname") or "")
            pid2 = sec.get("parent_id")
            if pid2:
                first = fetch_one(
                    "SELECT enname FROM experiment_manage WHERE id = %(id)s LIMIT 1",
                    {"id": pid2},
                )
                if first:
                    en1 = str(first.get("enname") or "")
    return en1, en2, en3


def _generate_exp_order_no(*, order_time: str, class_id: Any, supplier_id: Any) -> str:
    """对齐 Java orderIdGeranateSale：{company_code}PT{en1}{en2}{en3}{yyyyMM}{5位序号}。"""
    from datetime import datetime

    en1, en2, en3 = _manage_ennames(class_id)
    com_code = ""
    try:
        sid = int(supplier_id) if supplier_id not in (None, "") else 0
    except (TypeError, ValueError):
        sid = 0
    if sid:
        u = fetch_one("SELECT company_code FROM `user` WHERE id = %(id)s LIMIT 1", {"id": sid})
        if u:
            com_code = str(u.get("company_code") or "")
    dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(str(order_time).strip()[:19], fmt)
            break
        except (TypeError, ValueError):
            continue
    if dt is None:
        dt = datetime.now()
    datestr = dt.strftime("%Y%m")
    prefix = f"{com_code}PT{en1}{en2}{en3}{datestr}"
    latest = fetch_one(
        """
        SELECT order_id FROM experiment_order
        WHERE order_id LIKE %(pfx)s
        ORDER BY order_id DESC
        LIMIT 1
        """,
        {"pfx": f"{prefix}%"},
    )
    seq = 1
    if latest and latest.get("order_id"):
        oid = str(latest["order_id"])
        try:
            seq = int(oid[-5:]) + 1
        except (TypeError, ValueError):
            seq = 1
    return prefix + _gen_order_seq_code(seq)


def _pick(d: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def create_exp_order(
    *,
    header: dict[str, Any],
    children: list[dict[str, Any]],
    user_id: str | int | None = None,
    accessory_ids: list[Any] | None = None,
) -> tuple[bool, str, int | None]:
    """
    创建实验主单（order_type=6），对齐 Java submitExpOrder / saveExpOrders。
    成功返回 (True, 新订单数字 id 字符串, id)。
    """
    header = header or {}
    children = [c for c in (children or []) if isinstance(c, dict)]
    customer_name = str(
        _pick(header, "customer_name", "customerName", "customerId", default="")
    ).strip()
    custom_user_id = str(
        _pick(header, "custom_user_id", "customUserId", "customerAccount", default="")
    ).strip()
    if not customer_name and not custom_user_id:
        return False, "提交订单失败,客户名称和客户账号不能同时为空!", None
    if not children:
        return False, "实验订单至少选择一个产品才可提交!", None

    class_id = _pick(header, "class_id", "classId", default="")
    supplier_name = str(
        _pick(header, "supplier_name", "supplierName", "supplierId", default="")
    ).strip()
    order_time = str(_pick(header, "order_time", "orderTime", default="")).strip()
    if not order_time:
        from datetime import datetime

        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_manager = str(_pick(header, "sale_manager", "saleManager", "saleManagerId", default="")).strip()
    sale_user = str(_pick(header, "sale_user", "saleUser", "saleUserId", default="")).strip()
    currency_type = str(_pick(header, "currency_type", "currencyType", default="1")).strip() or "1"
    pay_way = str(_pick(header, "pay_way", "payWay", default="")).strip()
    delivery_time = str(_pick(header, "delivery_time", "deliveryTime", default="")).strip()
    msg = str(_pick(header, "msg", "mark", default="")).strip()
    taxes = str(_pick(header, "taxes", default="")).strip()
    out_bill_type_id = str(
        _pick(header, "outBillTypeId", "out_bill_type_id", default="")
    ).strip()
    send_address = str(_pick(header, "send_address", "sendAddress", "shipAddress", default="")).strip()
    addressee_name = str(
        _pick(header, "addressee_name", "addresseeName", "shipUser", default="")
    ).strip()
    addressee_mobile = str(
        _pick(header, "addressee_mobile", "addresseeMobile", "shipPhone", default="")
    ).strip()

    inv_raw = _pick(header, "invoiceType", "invoice_type", default=None)
    if inv_raw in (True, "true", "on", "ON", "1", 1):
        invoice_type = 1
    elif inv_raw in (False, "false", "off", "OFF", "2", 2):
        invoice_type = 2
    else:
        invoice_type = 1

    rev_raw = _pick(header, "reverso_context", "reversoContext", default=None)
    if rev_raw in (True, "true", "on", "ON", "1", 1):
        reverso_context = 1
    elif rev_raw in (False, "false", "off", "OFF", "2", 2):
        reverso_context = 2
    else:
        reverso_context = 1

    try:
        total_price = float(_pick(header, "totalPrice", "total_price", default=0) or 0)
    except (TypeError, ValueError):
        total_price = 0.0

    goods_amount = 0.0
    for ch in children:
        try:
            nums = float(_pick(ch, "goods_nums", "goodsNums", "count", default=1) or 1)
        except (TypeError, ValueError):
            nums = 1.0
        goods_amount += nums

    # 首行分类 → exp_type_id（对齐 Java saveExpOrders）
    first_class = _pick(
        children[0], "experiment_class_id", "experimentClassId", "class_id", default=""
    )
    try:
        exp_type_id = int(first_class) if first_class not in (None, "") else None
    except (TypeError, ValueError):
        exp_type_id = None
    try:
        class_id_int = int(class_id) if class_id not in (None, "") else None
    except (TypeError, ValueError):
        class_id_int = None

    order_no = _generate_exp_order_no(
        order_time=order_time, class_id=class_id_int, supplier_id=supplier_name
    )
    add_uid = str(user_id or "").strip()

    mobile = ""
    if customer_name and str(customer_name).isdigit():
        crow = fetch_one(
            "SELECT contractPhone FROM qd_user_company WHERE id = %(id)s LIMIT 1",
            {"id": int(customer_name)},
        )
        if crow and crow.get("contractPhone"):
            mobile = str(crow["contractPhone"])
    if custom_user_id and str(custom_user_id).isdigit():
        urow = fetch_one(
            "SELECT mobile FROM `user` WHERE id = %(id)s LIMIT 1",
            {"id": int(custom_user_id)},
        )
        if urow and urow.get("mobile"):
            mobile = str(urow["mobile"])

    params = {
        "ono": order_no[:80],
        "ot": "6",
        "st": 5,
        "mobile": mobile[:50] if mobile else None,
        "rev": reverso_context,
        "addr": send_address[:500] if send_address else None,
        "an": addressee_name[:100] if addressee_name else None,
        "am": addressee_mobile[:50] if addressee_mobile else None,
        "inv": invoice_type,
        "msg": msg[:1000] if msg else None,
        "otm": order_time[:19],
        "sm": sale_manager or None,
        "su": sale_user or None,
        "cuid": int(custom_user_id) if str(custom_user_id).isdigit() else None,
        "cust": int(customer_name) if str(customer_name).isdigit() else None,
        "sup": supplier_name if str(supplier_name).isdigit() else None,
        "ct": int(currency_type) if str(currency_type).isdigit() else 1,
        "pw": pay_way or None,
        "ga": goods_amount,
        "delv": delivery_time[:19] if delivery_time else None,
        "tx": taxes or None,
        "tp": total_price,
        "class_id": class_id_int,
        "obt": out_bill_type_id if str(out_bill_type_id).isdigit() else None,
        "add_uid": add_uid or None,
        "exp_type": exp_type_id,
    }

    order_pk = None
    try:
        order_pk = execute_insert(
            """
            INSERT INTO experiment_order
                (addTime, deleteStatus, order_id, order_type, order_status,
                 mobile, reverso_context, send_address, addressee_name, addressee_mobile,
                 in_status, relation_type, invoiceType, msg, mark,
                 order_time, sale_manager, sale_user, custom_user_id, customer_name,
                 supplier_name, currency_type, pay_way, goods_amount,
                 delivery_time, taxes, totalPrice, class_id, out_bill_type_id,
                 add_user_id, exp_type_id)
            VALUES
                (NOW(), 0, %(ono)s, %(ot)s, %(st)s,
                 %(mobile)s, %(rev)s, %(addr)s, %(an)s, %(am)s,
                 0, 0, %(inv)s, %(msg)s, %(msg)s,
                 %(otm)s, %(sm)s, %(su)s, %(cuid)s, %(cust)s,
                 %(sup)s, %(ct)s, %(pw)s, %(ga)s,
                 %(delv)s, %(tx)s, %(tp)s, %(class_id)s, %(obt)s,
                 %(add_uid)s, %(exp_type)s)
            """,
            params,
        )
    except Exception:
        order_pk = execute_insert(
            """
            INSERT INTO experiment_order
                (addTime, deleteStatus, order_id, order_type, order_status,
                 totalPrice, sale_manager, sale_user, customer_name, supplier_name,
                 currency_type, invoiceType, class_id, msg, mark)
            VALUES
                (NOW(), 0, %(ono)s, %(ot)s, %(st)s,
                 %(tp)s, %(sm)s, %(su)s, %(cust)s, %(sup)s,
                 %(ct)s, %(inv)s, %(class_id)s, %(msg)s, %(msg)s)
            """,
            params,
        )
        if order_pk:
            for sql, p in (
                (
                    """
                    UPDATE experiment_order SET
                        order_time=%(otm)s, delivery_time=%(delv)s, pay_way=%(pw)s,
                        taxes=%(tx)s, custom_user_id=%(cuid)s, reverso_context=%(rev)s,
                        send_address=%(addr)s, addressee_name=%(an)s, addressee_mobile=%(am)s,
                        goods_amount=%(ga)s, in_status=0, relation_type=0,
                        out_bill_type_id=%(obt)s, exp_type_id=%(exp_type)s,
                        add_user_id=%(add_uid)s, mobile=%(mobile)s
                    WHERE id=%(id)s
                    """,
                    {**params, "id": order_pk},
                ),
            ):
                try:
                    execute(sql, p)
                except Exception:
                    pass
    if not order_pk:
        return False, "订单提交失败，请联系管理员!", None

    for i, ch in enumerate(children):
        child_no = f"{order_no}-{i + 1}"
        goods_id = _pick(ch, "goods_id", "goodsId", default="")
        goods_name = str(_pick(ch, "goods_name", "goodsName", default="")).strip()
        goods_spec = str(_pick(ch, "goods_spec", "goodsSpec", default="")).strip()
        goods_brand_id = _pick(ch, "goods_brand_id", "goodsBrandId", default="")
        goods_brand_name = str(
            _pick(ch, "goods_brand_name", "goodsBrandName", default="")
        ).strip()
        try:
            goods_nums = float(_pick(ch, "goods_nums", "goodsNums", "count", default=1) or 1)
        except (TypeError, ValueError):
            goods_nums = 1.0
        try:
            goods_price = float(
                _pick(ch, "goods_price", "goodsPrice", "price", default=0) or 0
            )
        except (TypeError, ValueError):
            goods_price = 0.0
        try:
            reference_price = float(
                _pick(ch, "reference_price", "referencePrice", default=goods_price) or 0
            )
        except (TypeError, ValueError):
            reference_price = goods_price
        project_id = _pick(ch, "experiment_project_id", "experimentProjectId", default="")
        project_name = str(
            _pick(ch, "experiment_project_name", "experimentProjectName", default="")
        ).strip()
        class_cid = _pick(ch, "experiment_class_id", "experimentClassId", default="")
        class_cname = str(
            _pick(ch, "experiment_class_name", "experimentClassName", default="")
        ).strip()

        # 商品字段反写
        if goods_id and str(goods_id).isdigit():
            g = fetch_one(
                """
                SELECT t.goods_name, t.goods_brand_id, b.name AS brand_name
                FROM experiment_goods t
                LEFT JOIN goodsbrand b ON t.goods_brand_id = b.id
                WHERE t.id = %(id)s LIMIT 1
                """,
                {"id": int(goods_id)},
            )
            if g:
                goods_name = str(g.get("goods_name") or goods_name)
                if g.get("goods_brand_id") is not None:
                    goods_brand_id = g["goods_brand_id"]
                if g.get("brand_name"):
                    goods_brand_name = str(g["brand_name"])

        child_params = {
            "oid": order_pk,
            "cno": child_no[:80],
            "gid": int(goods_id) if str(goods_id).isdigit() else None,
            "gn": goods_name[:200],
            "gs": goods_spec[:200],
            "gbid": int(goods_brand_id) if str(goods_brand_id).isdigit() else None,
            "gb": goods_brand_name[:100],
            "nums": goods_nums,
            "price": goods_price,
            "ref": reference_price,
            "epid": int(project_id) if str(project_id).isdigit() else None,
            "epn": project_name[:200],
            "ecid": int(class_cid) if str(class_cid).isdigit() else None,
            "ecn": class_cname[:200],
            "ct": int(currency_type) if str(currency_type).isdigit() else 1,
        }
        child_pk = None
        try:
            child_pk = execute_insert(
                """
                INSERT INTO experiment_order_child
                    (addTime, deleteStatus, order_form_id, order_id,
                     goods_id, goods_name, goods_spec, goods_brand_id, goods_brand_name,
                     goods_nums, goods_price, reference_price,
                     experiment_project_id, experiment_project_name,
                     experiment_class_id, experiment_class_name,
                     order_status, in_status, op_status, fcsq, is_meeting, currency_type)
                VALUES
                    (NOW(), 0, %(oid)s, %(cno)s,
                     %(gid)s, %(gn)s, %(gs)s, %(gbid)s, %(gb)s,
                     %(nums)s, %(price)s, %(ref)s,
                     %(epid)s, %(epn)s, %(ecid)s, %(ecn)s,
                     1, 0, 1, 0, 0, %(ct)s)
                """,
                child_params,
            )
        except Exception:
            try:
                child_pk = execute_insert(
                    """
                    INSERT INTO experiment_order_child
                        (addTime, deleteStatus, order_form_id, order_id,
                         goods_id, goods_name, goods_spec, goods_brand_name, goods_nums,
                         price, reference_price, experiment_project_id, experiment_project_name,
                         experiment_class_id, experiment_class_name,
                         order_status, op_status, currency_type)
                    VALUES
                        (NOW(), 0, %(oid)s, %(cno)s,
                         %(gid)s, %(gn)s, %(gs)s, %(gb)s, %(nums)s,
                         %(price)s, %(ref)s, %(epid)s, %(epn)s,
                         %(ecid)s, %(ecn)s,
                         1, 1, %(ct)s)
                    """,
                    child_params,
                )
            except Exception:
                child_pk = execute_insert(
                    """
                    INSERT INTO experiment_order_child
                        (addTime, deleteStatus, order_form_id, order_id,
                         goods_name, goods_nums, price, order_status, op_status)
                    VALUES
                        (NOW(), 0, %(oid)s, %(cno)s,
                         %(gn)s, %(nums)s, %(price)s, 1, 1)
                    """,
                    child_params,
                )
        if child_pk:
            try:
                execute(
                    """
                    INSERT INTO experiment_order_child_log
                        (addTime, deleteStatus, of_id, log_info, log_user_id)
                    VALUES (NOW(), 0, %(oid)s, %(info)s, %(uid)s)
                    """,
                    {
                        "oid": child_pk,
                        "info": "创建子订单",
                        "uid": add_uid or None,
                    },
                )
            except Exception:
                try:
                    execute(
                        """
                        INSERT INTO experiment_order_child_log
                            (addTime, deleteStatus, of_id, log_info)
                        VALUES (NOW(), 0, %(oid)s, %(info)s)
                        """,
                        {"oid": child_pk, "info": "创建子订单"},
                    )
                except Exception:
                    pass

    _write_order_log(int(order_pk), "创建订单", user_id=add_uid or None)

    aids = accessory_ids
    if aids is None:
        raw_acc = header.get("accessoryId") or header.get("accessoryIds") or header.get("orderdata")
        if isinstance(raw_acc, (list, tuple)):
            aids = list(raw_acc)
        elif raw_acc not in (None, ""):
            aids = str(raw_acc).split(",")
        else:
            aids = []
    for aid in aids or []:
        s = str(aid).strip()
        if not s.isdigit():
            continue
        try:
            execute(
                """
                UPDATE accessory
                SET exp_of_id = %(oid)s, type = IFNULL(NULLIF(type, 0), 3)
                WHERE id = %(aid)s AND IFNULL(deleteStatus, 0) = 0
                """,
                {"oid": order_pk, "aid": int(s)},
            )
        except Exception:
            pass

    return True, str(order_pk), int(order_pk)


# 对齐 Java excel-config.xml id=experimentOrder 的订单状态 format
_EXPORT_ORDER_STATUS_LABEL = {
    0: "已取消",
    5: "待提交审核",
    10: "已驳回",
    20: "待审核",
    30: "已审核",
    40: "已确认",
    50: "已完成",
    60: "已评价",
    66: "待平台确认",
    67: "待客户确认",
}

# 对齐 Java excel-config.xml id=experimentOrder 列标题
EXPERIMENT_ORDER_EXPORT_HEADERS = [
    "序号",
    "下单时间",
    "订单编号",
    "客户公司",
    "子订单的产品名称",
    "产品型号",
    "实验测试项目",
    "实验测试项目的隶属国家",
    "订单总金额",
    "子订单价格",
    "开票状态",
    "开票时间",
    "开票金额",
    "付款状态",
    "付款时间",
    "付款金额",
    "订单状态",
]


def _export_order_status_label(status: Any) -> str:
    try:
        st = int(status) if status is not None else None
    except (TypeError, ValueError):
        st = None
    if st is None:
        return ""
    return _EXPORT_ORDER_STATUS_LABEL.get(st, str(st))


def _fmt_export_dt(value: Any, *, date_only: bool = False) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if date_only:
        return text[:10]
    return text[:19].replace("T", " ")


def _to_decimal(value: Any):
    from decimal import Decimal, InvalidOperation

    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def build_experiment_order_export_matrix(
    *,
    limit: int = 5000,
    scope: dict[str, Any] | None = None,
    **filters: Any,
) -> tuple[list[str], list[list]]:
    """对齐 Java experimentOrder/export.htm：按子单展开行，首行保留主单字段。"""
    orders, _ = list_orders(
        order_type="6",
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
        scope=scope,
    )
    if not orders:
        return EXPERIMENT_ORDER_EXPORT_HEADERS, []

    order_ids = [int(o["id"]) for o in orders if o.get("id") is not None]
    if not order_ids:
        return EXPERIMENT_ORDER_EXPORT_HEADERS, []

    placeholders = ", ".join(f"%(oid{i})s" for i in range(len(order_ids)))
    oid_params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    child_rows = fetch_all(
        f"""
        SELECT
            c.order_form_id AS ofId,
            c.goods_name AS goodsName,
            c.goods_spec AS goodsSpec,
            c.experiment_project_name AS projectName,
            c.goods_nums AS goodsNums,
            c.goods_price AS goodsPrice,
            ep.country AS country
        FROM experiment_order_child c
        LEFT JOIN experiment_project ep ON c.experiment_project_id = ep.id
        WHERE c.order_form_id IN ({placeholders})
          AND IFNULL(c.delete_status, 2) = 2
          AND c.order_status > 0
        ORDER BY c.order_form_id ASC, c.id ASC
        """,
        oid_params,
    )
    children_by_of: dict[int, list[dict[str, Any]]] = {}
    for ch in child_rows:
        try:
            of_id = int(ch.get("ofId"))
        except (TypeError, ValueError):
            continue
        children_by_of.setdefault(of_id, []).append(ch)

    bill_rows = fetch_all(
        f"""
        SELECT
            exp_of_id AS ofId,
            type AS billType,
            money,
            bill_date AS billDate
        FROM qd_bill
        WHERE exp_of_id IN ({placeholders})
        ORDER BY bill_date ASC, id ASC
        """,
        oid_params,
    )
    first_kp: dict[int, str] = {}
    first_sk: dict[int, str] = {}
    for b in bill_rows:
        try:
            of_id = int(b.get("ofId"))
            btype = int(b.get("billType"))
        except (TypeError, ValueError):
            continue
        dt = _fmt_export_dt(b.get("billDate"), date_only=True)
        if btype == 1 and of_id not in first_kp:
            first_kp[of_id] = dt
        elif btype == 2 and of_id not in first_sk:
            first_sk[of_id] = dt

    matrix: list[list] = []
    nums = 0
    for of in orders:
        try:
            of_id = int(of["id"])
        except (TypeError, ValueError, KeyError):
            continue
        kids = children_by_of.get(of_id) or []
        if not kids:
            continue
        nums += 1
        kp_cnt = int(of.get("kpCount") or 0)
        sk_cnt = int(of.get("skCount") or 0)
        iskp = "已开票" if kp_cnt > 0 else "未开票"
        isfk = "已付款" if sk_cnt > 0 else "未付款"
        kpje = of.get("invoiceAmount")
        skje = of.get("receiveAmount")
        order_time = _fmt_export_dt(of.get("orderTime") or of.get("addTime"))
        order_id = of.get("orderId") or ""
        company = of.get("customerName") or ""
        total_price = of.get("totalPrice")
        status_label = _export_order_status_label(of.get("orderStatus"))
        xskprq = first_kp.get(of_id, "")
        xsskrq = first_sk.get(of_id, "")

        for i, ch in enumerate(kids):
            goods_total = None
            child_price = _to_decimal(ch.get("goodsPrice"))
            child_nums = _to_decimal(ch.get("goodsNums"))
            if child_price is not None and child_nums is not None:
                goods_total = child_price * child_nums
            if i == 0:
                row = [
                    str(nums),
                    order_time,
                    order_id,
                    company,
                    ch.get("goodsName") or "",
                    ch.get("goodsSpec") or "",
                    ch.get("projectName") or "",
                    ch.get("country") or "",
                    total_price if total_price is not None else "",
                    goods_total if goods_total is not None else "",
                    iskp,
                    xskprq,
                    kpje if kpje is not None else "",
                    isfk,
                    xsskrq,
                    skje if skje is not None else "",
                    status_label,
                ]
            else:
                row = [
                    "",
                    "",
                    "",
                    "",
                    ch.get("goodsName") or "",
                    ch.get("goodsSpec") or "",
                    ch.get("projectName") or "",
                    ch.get("country") or "",
                    "",
                    goods_total if goods_total is not None else "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            matrix.append(row)
    return EXPERIMENT_ORDER_EXPORT_HEADERS, matrix


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
        scope=filters.get("scope"),
    )
    return rows
