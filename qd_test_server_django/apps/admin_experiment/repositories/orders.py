from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from apps.admin_experiment.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

logger = logging.getLogger(__name__)

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


def _sale_user_ids_for_user(user_id: str) -> list[str]:
    """对齐 Java syUserSaleUserService.findSaleUserIdByUserId。"""
    rows = fetch_all(
        """
        SELECT saleuser_id AS sid
        FROM sy_user_saleuser
        WHERE IFNULL(deleteStatus, 0) = 0
          AND CAST(pt_type AS CHAR) = '2'
          AND CAST(user_id AS CHAR) = CAST(%(uid)s AS CHAR)
        """,
        {"uid": user_id},
    )
    return [str(r["sid"]) for r in (rows or []) if r.get("sid") not in (None, "")]


def build_sub_order_list_scope(
    user: dict[str, Any] | None,
    *,
    order_type: str = "10",
) -> dict[str, Any]:
    """
    对齐 Java experimentChildOrder/list_dpt1.ajax 数据范围：
    - 系统管理员：不限制（userId2 为空）
    - 其他：userId2 = 当前用户；可见本人相关子单，以及绑定公司、下属销售人员订单
    """
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    empty = {"user_id": "", "supplier_ids": [], "sale_user_ids": []}
    if not uid:
        return empty

    urow = fetch_one(
        "SELECT utoo_type AS utooType FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1",
        {"id": uid},
    )
    utoo = str((urow or {}).get("utooType") or (user or {}).get("utoo_type") or "").strip()
    role = _resolve_utoo_role_name(utoo)
    if role == "系统管理员":
        return empty

    supplier_ids = list(_companies_by_syuser(uid))
    sale_user_ids: list[str] = []
    ot = str(order_type or "10")
    if _has_exp_order_type_perm(uid, ot):
        for cid in _companies_from_sy_user_company(uid):
            if cid not in supplier_ids:
                supplier_ids.append(cid)
        sale_user_ids = _sale_user_ids_for_user(uid)

    return {
        "user_id": uid,
        "supplier_ids": supplier_ids,
        "sale_user_ids": sale_user_ids,
        "role": role,
        "utoo_type": utoo,
    }


def _append_sub_list_scope_sql(
    where: str,
    params: dict[str, Any],
    scope: dict[str, Any] | None,
    *,
    alias: str = "t",
    parent_alias: str = "p",
) -> str:
    """对齐 Java listPagesdpt1024 的 userId2 / supplier_nameg2 / saleUser2。"""
    if not scope:
        return where
    uid = str(scope.get("user_id") or "").strip()
    if not uid:
        return where

    params["scope_uid"] = uid
    params["scope_uid_like"] = f"%{uid}%"
    parts = [
        f"CAST({alias}.sale_user AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({alias}.add_user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({alias}.sale_manager AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({alias}.test_manager AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({alias}.warehouse_user AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({parent_alias}.sale_user AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({parent_alias}.add_user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"CAST({parent_alias}.sale_manager AS CHAR) = CAST(%(scope_uid)s AS CHAR)",
        f"IFNULL({parent_alias}.user_scale_info, '') LIKE %(scope_uid_like)s",
        f"IFNULL({parent_alias}.cb_user_scale_info, '') LIKE %(scope_uid_like)s",
        f"IFNULL({parent_alias}.salecb_user_scale_info, '') LIKE %(scope_uid_like)s",
        f"""EXISTS (
              SELECT 1 FROM exp_qd_purchase_order_child poc
              JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
              WHERE poc.purchase_order_id = {alias}.id
                AND CAST(IFNULL(ocf.test_user_id, '') AS CHAR) LIKE %(scope_uid_like)s
            )""",
    ]
    supplier_ids = [str(x) for x in (scope.get("supplier_ids") or []) if str(x)]
    if supplier_ids:
        in_keys = []
        for i, sid in enumerate(supplier_ids):
            k = f"scope_sub_sup_{i}"
            params[k] = sid
            in_keys.append(f"%({k})s")
        # Java order_type 9/10：父单 supplier_name
        parts.append(
            f"CAST({parent_alias}.supplier_name AS CHAR) IN ({', '.join(in_keys)})"
        )
    sale_user_ids = [str(x) for x in (scope.get("sale_user_ids") or []) if str(x)]
    if sale_user_ids:
        in_keys = []
        for i, sid in enumerate(sale_user_ids):
            k = f"scope_sub_su_{i}"
            params[k] = sid
            in_keys.append(f"%({k})s")
        parts.append(f"CAST({parent_alias}.sale_user AS CHAR) IN ({', '.join(in_keys)})")

    where += " AND (" + " OR ".join(parts) + ")"
    return where


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
    # 创建子单时可能未写 pay_status（NULL），与 Java 字典 0=未申请对齐
    if v is None or v == "":
        return PAY_STATUS_LABEL[0]
    try:
        return PAY_STATUS_LABEL.get(int(v), str(v))
    except (TypeError, ValueError):
        return PAY_STATUS_LABEL[0]


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
    test_manager: str = "",
    sale_user: str = "",
    order_status: str = "",
    pay_status: str = "",
    test_user_id: str = "",
    is_confirm: str = "",
    finish_start: str = "",
    finish_end: str = "",
    require_finish_log: bool = False,
    page: int,
    page_size: int,
    scope: dict[str, Any] | None = None,
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
    if test_manager:
        # 对齐 Java ExpSubPurchaseOrder todoCheckList：测试主管按 test_manager 筛
        where += " AND CAST(t.test_manager AS CHAR) = CAST(%(test_manager)s AS CHAR)"
        params["test_manager"] = test_manager
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
    if finish_start or finish_end or require_finish_log:
        # Java：按 order_log「测试完成」最早时间过滤；bjexport 的 getAllOrders1 要求 cewctime 非空
        where += """
          AND EXISTS (
            SELECT 1 FROM experiment_order_log log
            WHERE log.of_id = t.id AND log.log_info LIKE %(finish_kw)s
              AND IFNULL(log.deleteStatus, 0) = 0
        """
        params["finish_kw"] = "%测试完成%"
        if finish_start:
            where += " AND log.addTime >= %(finish_start)s"
            params["finish_start"] = finish_start
        if finish_end:
            where += " AND log.addTime <= %(finish_end)s"
            params["finish_end"] = f"{finish_end} 23:59:59"
        where += ")"

    # 对齐 Java list_dpt1 userId2 数据权限
    where = _append_sub_list_scope_sql(where, params, scope, alias="t", parent_alias="p")

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_order t
            LEFT JOIN experiment_order p ON t.parent_id = p.id
            LEFT JOIN qd_user_company q ON CAST(t.customer_name AS CHAR) = CAST(q.id AS CHAR)
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
        LEFT JOIN qd_user_company q ON CAST(t.customer_name AS CHAR) = CAST(q.id AS CHAR)
        LEFT JOIN qd_user_company qs ON CAST(t.stock_company_name AS CHAR) = CAST(qs.id AS CHAR)
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


def list_welcome_timeout_orders(
    *,
    user: dict[str, Any] | None,
    order_status_out: str = "",
    is_timeout: str = "",
    order_id: str = "",
    parent_order_id: str = "",
    customer_name: str = "",
    sale_manager: str = "",
    sale_user: str = "",
    order_status: str = "",
    test_user_id: str = "",
    finish_start: str = "",
    finish_end: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java experimentChildOrder/list_dpt_welcome.ajax（listPagesdpthyy）。

    以 statistic_experiment_timeout 为主表，限定子单 order_type=10。
    """
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    utoo = str((user or {}).get("utoo_type") or "").strip()
    if not utoo and uid:
        urow = fetch_one(
            "SELECT utoo_type AS utooType FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1",
            {"id": uid},
        )
        utoo = str((urow or {}).get("utooType") or "").strip()
    role = _resolve_utoo_role_name(utoo)

    where = """
        WHERE IFNULL(seto.deleteStatus, 0) = 0
          AND IFNULL(t.deleteStatus, 0) = 0
          AND t.order_status > 0
          AND CAST(t.order_type AS CHAR) = '10'
    """
    params: dict[str, Any] = {}
    if order_status_out not in ("", "null", "None"):
        where += " AND seto.order_status = %(order_status_out)s"
        params["order_status_out"] = int(order_status_out)
    if is_timeout not in ("", "null", "None"):
        where += " AND seto.is_timeout = %(is_timeout)s"
        params["is_timeout"] = int(is_timeout)
    if order_id:
        where += " AND t.order_id LIKE %(order_id)s"
        params["order_id"] = f"%{order_id}%"
    if parent_order_id:
        where += " AND p.order_id LIKE %(parent_order_id)s"
        params["parent_order_id"] = f"%{parent_order_id}%"
    if customer_name:
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
    if test_user_id:
        where += """
          AND EXISTS (
            SELECT 1 FROM exp_qd_purchase_order_child poc
            JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
            WHERE poc.purchase_order_id = t.id AND ocf.test_user_id = %(test_user_id)s
          )
        """
        params["test_user_id"] = test_user_id
    if finish_start:
        where += """
          AND EXISTS (
            SELECT 1 FROM experiment_order_log log
            WHERE log.of_id = t.id AND log.log_info LIKE %(finish_kw)s
              AND IFNULL(log.deleteStatus, 0) = 0
              AND log.addTime >= %(finish_start)s
          )
        """
        params["finish_kw"] = "%测试完成%"
        params["finish_start"] = finish_start
    if finish_end:
        where += """
          AND EXISTS (
            SELECT 1 FROM experiment_order_log log
            WHERE log.of_id = t.id AND log.log_info LIKE %(finish_kw2)s
              AND IFNULL(log.deleteStatus, 0) = 0
              AND log.addTime <= %(finish_end)s
          )
        """
        params["finish_kw2"] = "%测试完成%"
        params["finish_end"] = f"{finish_end} 23:59:59"

    # 对齐 Java list_dpt_welcome：仅 utoo_type 精确「销售主管」走 parent.sale_manager；
    # 测试主管/测试人员等走 seto 上的 test/sale/audit/lab_manager 命中（勿用 role 映射把测试主管当成销售主管）
    if uid and role != "系统管理员":
        if str(utoo).strip() == "销售主管":
            where += " AND CAST(p.sale_manager AS CHAR) = CAST(%(scope_uid)s AS CHAR)"
            params["scope_uid"] = uid
        else:
            where += """
              AND (
                CAST(seto.test_user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
                OR CAST(seto.sale_user_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
                OR CAST(seto.audit_manager_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
                OR CAST(seto.lab_manager_id AS CHAR) = CAST(%(scope_uid)s AS CHAR)
              )
            """
            params["scope_uid"] = uid

    from_sql = """
        FROM statistic_experiment_timeout seto
        INNER JOIN experiment_order t ON seto.order_id = t.id
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
    """

    total = int(
        scalar(
            f"SELECT COUNT(DISTINCT t.id) {from_sql} {where}",
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
            t.pay_status AS payStatus, seto.is_timeout AS isTimeout,
            seto.order_status AS timeoutOrderStatus,
            q.name AS customerName,
            p.order_id AS parentOrderId,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName,
            tu.user_name AS testName, tu.true_name AS testTrueName
        {from_sql}
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for r in rows:
        r["orderStatusLabel"] = _sub_status_label(r.get("orderStatus"))
        r["customerName"] = r.get("customerName") or "-"
        parent = r.get("parentOrderId")
        if not parent:
            pt = str(r.get("purchaseType") or "")
            parent = "自主发起" if pt == "1" else ("自主发起配件采购" if pt == "2" else "")
        r["parentOrderId"] = parent or ""
        r["saleManager"] = str(r.get("managerName") or r.get("managerTrueName") or "").strip()
        r["saleUser"] = str(r.get("saleUserName") or r.get("saleUserTrueName") or "").strip()
        r["testName"] = str(r.get("testName") or r.get("testTrueName") or "").strip()
        otm = r.get("orderTime") or r.get("addTime")
        r["orderTime"] = str(otm)[:19] if otm else ""
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
    """抢单列表：实验子订单(10) + 实验分包子订单(9)，子行 test_user_id=22。"""
    where = """
        WHERE t.order_status > 0 AND t.order_type IN ('9', '10')
          AND (
            EXISTS (
              SELECT 1
              FROM exp_qd_purchase_order_child poc
              JOIN experiment_order_child ocf ON poc.order_child_id = ocf.id
              WHERE poc.purchase_order_id = t.id
                AND ocf.test_user_id = %(pool_uid)s
                AND ocf.order_status <= 36
                AND IFNULL(ocf.delete_status, 2) <> 1
            )
            OR EXISTS (
              SELECT 1
              FROM experiment_order_child ocf2
              WHERE ocf2.order_form_id = t.id
                AND ocf2.test_user_id = %(pool_uid)s
                AND ocf2.order_status <= 36
                AND IFNULL(ocf2.delete_status, 2) <> 1
            )
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
            t.order_type AS orderType,
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
        r["orderType"] = str(r.get("orderType") or "10")
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
        """
        UPDATE experiment_order_child
        SET test_user_id = %(uid)s
        WHERE id = %(id)s
          AND CAST(IFNULL(test_user_id, '') AS CHAR) = CAST(%(pool)s AS CHAR)
        """,
        {"uid": str(user_id).strip(), "id": child["id"], "pool": GRAB_POOL_TEST_USER_ID},
    )
    # 确认已写入，避免静默未更新
    after = fetch_one(
        """
        SELECT test_user_id AS testUserId
        FROM experiment_order_child
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": child["id"]},
    )
    if str((after or {}).get("testUserId") or "").strip() != str(user_id).strip():
        return False, "抢单写入失败，请重试"
    try:
        execute(
            """
            UPDATE statistic_experiment_finish
            SET test_user_id = %(uid)s
            WHERE child_id = %(cid)s
            """,
            {"uid": str(user_id).strip(), "cid": child["id"]},
        )
    except Exception:
        pass
    return True, "抢单成功！"


def _is_child_order_type(order_type: Any) -> bool:
    return str(order_type or "") in ("9", "10")


def _truthy_flag(val: Any, *, yes_values: tuple[str, ...] = ("1", "ON", "TRUE", "YES")) -> bool:
    """兼容 Java int(1/0/2) 与历史 ON/OFF 字符串。"""
    if val is None:
        return False
    s = str(val).strip().upper()
    if not s or s in ("0", "2", "OFF", "FALSE", "NO", "NONE"):
        return False
    return s in yes_values


def _reverso_is_yes(val: Any) -> bool:
    """样品回收：Java reverso_context 1=回收，2=不回收；亦兼容 ON。"""
    return _truthy_flag(val, yes_values=("1", "ON", "TRUE", "YES"))


def _video_is_yes(val: Any) -> bool:
    """是否云视频：Java is_video 1=是，0=否。"""
    return _truthy_flag(val, yes_values=("1", "ON", "TRUE", "YES"))


def get_order(order_id: int) -> dict[str, Any] | None:
    """对齐 Java orderdetail.htm 主单头字段（admin 侧精简版）。"""
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.order_id AS orderId, t.order_type AS orderType,
            t.order_status AS orderStatus, t.totalPrice AS totalPrice,
            t.order_time AS orderTime, t.is_confirm AS isConfirm,
            t.stock_company_name AS stockCompanyId,
            qs.name AS stockCompanyName, t.mark, t.msg AS msg,
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
            t.add_user_id AS addUserId,
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
            COALESCE(cu.mobile, cu2.mobile) AS customUserMobile,
            COALESCE(cu.userName, cu2.userName, cu.trueName, cu2.trueName) AS customUserName,
            COALESCE(pcu.mobile, pcu2.mobile) AS parentCustomUserMobile,
            COALESCE(pcu.userName, pcu2.userName, pcu.trueName, pcu2.trueName) AS parentCustomUserName,
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
            tab2.test_user_id AS testUserId,
            tu.user_name AS testName, tu.true_name AS testTrueName
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON CAST(t.customer_name AS CHAR) = CAST(q.id AS CHAR)
        LEFT JOIN qd_user_company qs ON CAST(t.stock_company_name AS CHAR) = CAST(qs.id AS CHAR)
        LEFT JOIN `user` u ON t.supplier_name = u.id
        LEFT JOIN exp_user cu ON CAST(t.custom_user_id AS CHAR) = CAST(cu.id AS CHAR)
        LEFT JOIN `user` cu2 ON CAST(t.custom_user_id AS CHAR) = CAST(cu2.id AS CHAR)
        LEFT JOIN exp_user pcu ON CAST(p.custom_user_id AS CHAR) = CAST(pcu.id AS CHAR)
        LEFT JOIN `user` pcu2 ON CAST(p.custom_user_id AS CHAR) = CAST(pcu2.id AS CHAR)
        LEFT JOIN sy_users sm ON CAST(t.sale_manager AS CHAR) = CAST(sm.id AS CHAR)
        LEFT JOIN sy_users su ON CAST(t.sale_user AS CHAR) = CAST(su.id AS CHAR)
        LEFT JOIN sy_users au ON CAST(t.add_user_id AS CHAR) = CAST(au.id AS CHAR)
        LEFT JOIN sy_users tm ON CAST(t.test_manager AS CHAR) = CAST(tm.id AS CHAR)
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
    stock_id = str(row.get("stockCompanyId") or "").strip()
    stock_name = str(row.get("stockCompanyName") or "").strip()
    row["stockCompanyId"] = stock_id
    # stock_company_name 库内存公司 id；展示名需 JOIN qd_user_company
    row["stockCompanyName"] = stock_name or "-"
    if ot == "9":
        # 分包子单：公司名单独展示，不把 stock 冒充客户
        row["companyName"] = q_name or "-"
        row["customerName"] = q_name or "-"
    else:
        # 对齐 Java：客户名称仅来自 customer_name→qd_user_company，不用进货公司冒充
        row["companyName"] = q_name or "-"
        row["customerName"] = q_name or ""
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
    # 业务咨询/预约单（对齐 Java 订单详情底部咨询表：预约单号/咨询时间/…）
    row["appointmentNo"] = ""
    row["appointmentId"] = None
    row["consultList"] = []
    consult_id = row.get("consultId")
    order_no = str(row.get("orderId") or "").strip()
    consult = None
    try:
        if consult_id not in (None, "", 0, "0"):
            consult = fetch_one(
                """
                SELECT
                    sc.id,
                    sc.order_num AS appointmentNo,
                    sc.order_id AS linkedOrderId,
                    sc.status AS appointmentStatus,
                    sc.addTime AS consultTime,
                    sc.userName AS consultUserName,
                    sc.mobile AS appointmentMobile,
                    sc.company_name AS appointmentCompany,
                    sc.class_id AS consultClassId,
                    em.name AS consultClassName
                FROM service_consult sc
                LEFT JOIN experiment_manage em ON sc.class_id = em.id
                WHERE sc.id = %(id)s
                LIMIT 1
                """,
                {"id": consult_id},
            )
        if not consult and order_no:
            consult = fetch_one(
                """
                SELECT
                    sc.id,
                    sc.order_num AS appointmentNo,
                    sc.order_id AS linkedOrderId,
                    sc.status AS appointmentStatus,
                    sc.addTime AS consultTime,
                    sc.userName AS consultUserName,
                    sc.mobile AS appointmentMobile,
                    sc.company_name AS appointmentCompany,
                    sc.class_id AS consultClassId,
                    em.name AS consultClassName
                FROM service_consult sc
                LEFT JOIN experiment_manage em ON sc.class_id = em.id
                WHERE sc.order_num = %(ono)s
                   OR CAST(sc.order_id AS CHAR) = %(ono)s
                ORDER BY sc.id DESC
                LIMIT 1
                """,
                {"ono": order_no},
            )
        if consult:
            try:
                st = int(
                    consult.get("appointmentStatus")
                    if consult.get("appointmentStatus") is not None
                    else -1
                )
            except (TypeError, ValueError):
                st = -1
            status_label = {
                0: "待处理",
                1: "已处理",
                2: "已生成订单",
                3: "已取消",
            }.get(st, "未回复" if st < 0 else str(st))
            appt_no = str(consult.get("appointmentNo") or "").strip()
            # 对齐 Java：预约单号用咨询原始 order_num，不用实验单号顶替；
            # 历史数据若曾被错误写成实验单号，则回退咨询主键便于跳转。
            if not appt_no or appt_no == order_no:
                appt_no = str(consult.get("id") or "")
            if not appt_no:
                appt_no = str(consult.get("linkedOrderId") or "")
            consult_time = consult.get("consultTime")
            if consult_time:
                consult_time = str(consult_time)[:19]
            item = {
                "id": consult.get("id"),
                "appointmentNo": appt_no,
                "consultTime": consult_time or "",
                "className": str(consult.get("consultClassName") or "").strip(),
                "userName": str(consult.get("consultUserName") or "").strip(),
                "mobile": str(consult.get("appointmentMobile") or "").strip(),
                "companyName": str(consult.get("appointmentCompany") or "").strip(),
                "status": st,
                "statusLabel": status_label,
            }
            row["appointmentId"] = item["id"]
            row["appointmentNo"] = item["appointmentNo"]
            row["appointmentStatus"] = st
            row["appointmentStatusLabel"] = status_label
            row["appointmentMobile"] = item["mobile"]
            row["appointmentCompany"] = item["companyName"]
            row["consultList"] = [item]
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
    # 咨询转订单历史数据：已开票但未写出项类型时，回填默认出项开票类型
    if str(row.get("invoiceType") or "") == "1" and out_id in (None, "", 0, "0"):
        try:
            bt = fetch_one(
                """
                SELECT id, name
                FROM bill_type
                WHERE type = 1
                  AND IFNULL(delete_status, 0) = 0
                ORDER BY id ASC
                LIMIT 1
                """
            )
            if bt and bt.get("id") not in (None, ""):
                pk = row.get("id")
                if pk not in (None, ""):
                    execute(
                        """
                        UPDATE experiment_order
                        SET out_bill_type_id = %(bid)s
                        WHERE id = %(oid)s
                          AND (out_bill_type_id IS NULL OR out_bill_type_id = 0)
                        """,
                        {"bid": bt["id"], "oid": pk},
                    )
                out_id = bt["id"]
                out_name = str(bt.get("name") or "").strip()
        except Exception:
            pass
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
    row["isVideoLabel"] = "是" if _video_is_yes(row.get("isVideo")) else "否"
    row["showShipAddress"] = False
    # type=9/10：样品回收/电话/云视频/寄回地址对齐 Java —— 均以父主单为准
    # （ExpSubPurchaseOrderController：reverso/mobile/send_address 取 orderParent）
    if ot in ("9", "10"):
        rev = row.get("parentReversoContext")
        if rev is None or str(rev).strip() == "":
            rev = row.get("reversoContext")
        pv = row.get("parentIsVideo")
        if pv is None or str(pv).strip() == "":
            pv = row.get("isVideo")
        phone = (
            str(row.get("parentMobile") or "").strip()
            or str(row.get("mobile") or "").strip()
            or str(row.get("shipPhone") or "").strip()
        )
        rev_yes = _reverso_is_yes(rev)
        row["reversoLabel"] = "是" if rev_yes else "否"
        row["reversoYes"] = rev_yes
        row["isVideoLabel"] = "是" if _video_is_yes(pv) else "否"
        row["contactPhone"] = phone or "-"
        if not str(row.get("mobile") or "").strip() and phone:
            row["mobile"] = phone
        # 回收=是就展示寄回地址；空地址以 - 呈现，避免只看到「是」却没有地址字段。
        if rev_yes:
            addr = (
                str(row.get("parentSendAddress") or "").strip()
                or str(row.get("shipAddress") or "").strip()
            )
            row["shipAddress"] = addr
            row["showShipAddress"] = True
        else:
            row["shipAddress"] = ""
            row["showShipAddress"] = False
        # 子单客户公司名可回退父单
        if ot == "10" and (not row.get("customerName") or row.get("customerName") in ("", "-")):
            parent_pk = row.get("parentPkId")
            if parent_pk not in (None, "", 0, "0"):
                try:
                    pc = fetch_one(
                        """
                        SELECT
                            q.name AS companyName,
                            COALESCE(cu.mobile, cu2.mobile) AS customMobile,
                            COALESCE(cu.userName, cu2.userName, cu.trueName, cu2.trueName) AS customUserName,
                            p.mobile AS parentMobile,
                            p.custom_user_id AS customUserId,
                            p.customer_name AS customerId
                        FROM experiment_order p
                        LEFT JOIN qd_user_company q ON p.customer_name = q.id
                        LEFT JOIN exp_user cu ON CAST(p.custom_user_id AS CHAR) = CAST(cu.id AS CHAR)
                        LEFT JOIN `user` cu2 ON CAST(p.custom_user_id AS CHAR) = CAST(cu2.id AS CHAR)
                        WHERE p.id = %(id)s
                        LIMIT 1
                        """,
                        {"id": parent_pk},
                    )
                    if pc:
                        pname = str(pc.get("companyName") or "").strip()
                        if pname:
                            row["customerName"] = pname
                            if row.get("companyName") in (None, "", "-"):
                                row["companyName"] = pname
                        pcm = (
                            str(pc.get("customMobile") or "").strip()
                            or str(pc.get("customUserName") or "").strip()
                        )
                        if not str(row.get("customUserMobile") or "").strip():
                            row["customUserMobile"] = pcm
                        if not str(row.get("parentCustomUserMobile") or "").strip():
                            row["parentCustomUserMobile"] = pcm
                        if not phone and pc.get("parentMobile"):
                            phone = str(pc.get("parentMobile") or "").strip()
                            row["contactPhone"] = phone or "-"
                            row["parentMobile"] = phone
                except Exception:
                    pass
    else:
        rev = row.get("reversoContext")
        row["reversoLabel"] = "是" if _reverso_is_yes(rev) else "否"
        row["reversoYes"] = _reverso_is_yes(rev)
        row["contactPhone"] = str(row.get("mobile") or row.get("shipPhone") or "").strip() or "-"
        row["showShipAddress"] = True
    # 客户账号：exp_user.mobile（对齐 Java customUser）；空则用户名/父单，勿用联系电话冒充
    cm = (
        str(row.get("customUserMobile") or "").strip()
        or str(row.get("customUserName") or "").strip()
        or str(row.get("parentCustomUserMobile") or "").strip()
        or str(row.get("parentCustomUserName") or "").strip()
    )
    row["customMobile"] = cm or "-"
    if row.get("customUserName") in (None, ""):
        row["customUserName"] = cm or ""
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
    # 详情里再按销售主管/admin 收紧（见 apply_audit_permission）
    row["canAudit"] = st == 20
    try:
        inv_bill_cnt = int(row.get("invoiceBillCount") or 0)
        recv_bill_cnt = int(row.get("receiveBillCount") or 0)
    except (TypeError, ValueError):
        inv_bill_cnt, recv_bill_cnt = 0, 0
    # Java isDisabled=true 才显示「编辑订单」；有票/主单已分钱/子行 is_sure=1 则禁编
    # 子单对齐 Java：仅收款票影响 isDisabled；主单开票+收款都算
    if child_kind:
        edit_allowed_by_bill = recv_bill_cnt <= 0
    else:
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
            # Java selSaleOrderBillList(parent_id, is_split=1)
            split_cnt = int(
                scalar(
                    """
                    SELECT COUNT(*) FROM qd_bill
                    WHERE exp_of_id = %(pid)s
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
    # Java isSave：仅实验子订单 type=10，且 status∉{0,50}；具体人员在详情 bundle 再按 viewer 收窄
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
    # 对齐 Java：仅线下单(is_online=0)显示「生成预约单」；线上单收款后自动生成
    row["canGenerateAppointment"] = (
        parent_kind and is_online == 0 and is_yyd == 0 and st not in (0,)
    )
    # 预约单只允许生成一次（与 Java 一致，无重新生成）
    row["canRegenerateAppointment"] = False
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
                SELECT COUNT(*) FROM experiment_order_child c
                WHERE c.order_form_id = %(oid)s
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND IFNULL(c.op_status, 0) = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM exp_qd_purchase_order_child p
                      INNER JOIN experiment_order o ON o.id = p.purchase_order_id
                      WHERE p.order_child_id = c.id
                        AND IFNULL(o.deleteStatus, 0) = 0
                        AND IFNULL(o.order_status, -1) <> 0
                  )
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
        # 仅已选择开票（1）才允许上传；兼容历史 invoiceType=0 的「否」单据。
        row["canUploadInvoice"] = st >= 30 and not inv_slots_full and inv_type == 1
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
            c.experiment_project_name AS deviceName,
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
        LEFT JOIN sy_users u ON CAST(c.test_user_id AS CHAR) = CAST(u.id AS CHAR)
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        LEFT JOIN (
            SELECT v1.*
            FROM experiment_video v1
            INNER JOIN (
                SELECT child_id, MAX(id) AS max_id
                FROM experiment_video
                GROUP BY child_id
            ) vx ON v1.id = vx.max_id
        ) v ON c.id = v.child_id
        LEFT JOIN order_sample_information osi ON c.sample_id = osi.id
        LEFT JOIN (
            SELECT t1.*
            FROM exp_goods_out_treasury_child t1
            INNER JOIN (
                SELECT t3.order_child_id, MAX(t3.id) AS max_id
                FROM exp_goods_out_treasury_child t3
                LEFT JOIN exp_goods_out_treasury t4 ON t3.out_id = t4.id
                -- 对齐 Java selCgChildListByParm：仅排除主单作废(status=3)；
                -- 寄回(got_status=3)/报废(5)后仍应展示样品管理单号
                WHERE IFNULL(t4.status, 0) != 3
                GROUP BY t3.order_child_id
            ) tx ON t1.id = tx.max_id
        ) gotc ON c.id = gotc.order_child_id
        LEFT JOIN sample_goods_storehouse gs ON gotc.store_id = gs.id
        LEFT JOIN sample_goods_store_position p ON gotc.store_position_id = p.id
        LEFT JOIN sample_goods_store_block b ON p.sample_block_id = b.id
        LEFT JOIN (
            SELECT * FROM exp_goods_out_treasury WHERE IFNULL(status, 0) != 3
        ) got ON gotc.out_id = got.id
"""


def _fetch_children_basic(order_id: int) -> list[dict[str, Any]]:
    """产品行读取：子单优先走采购挂接（对齐 Java getChildsByPurchaseId*）。

    若先按 order_form_id=子单 id 查，可能命中历史错挂行，导致详情与编辑/保存的挂接行不一致，
    表现为「编辑保存成功但详情仍显示旧测试人员/平台/预计完成时间」。
    """
    linked = fetch_all(
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
    if linked:
        return linked
    return fetch_all(
        f"""
        SELECT {_CHILD_LINE_SELECT}
        FROM experiment_order_child c
        {_CHILD_LINE_JOINS}
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )


def _fetch_children_fallback(order_id: int) -> list[dict[str, Any]]:
    """与 _fetch_children_basic 一致：子单优先按采购挂接读取。"""
    linked = fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.goods_id AS goodsId, c.goods_brand_id AS goodsBrandId,
            c.experiment_project_id AS projectId,
            c.goods_name AS goodsName, c.goods_spec AS goodsSpec,
            c.goods_brand_name AS goodsBrand, c.goods_nums AS goodsCount,
            c.experiment_project_name AS projectName,
            c.experiment_class_name AS className,
            c.experiment_project_name AS deviceName,
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
        LEFT JOIN sy_users u ON CAST(c.test_user_id AS CHAR) = CAST(u.id AS CHAR)
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        WHERE poc.purchase_order_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id ASC
        """,
        {"oid": order_id},
    )
    if linked:
        return linked
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
            c.experiment_project_name AS deviceName,
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
        LEFT JOIN sy_users u ON CAST(c.test_user_id AS CHAR) = CAST(u.id AS CHAR)
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
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


def list_edit_selectable_children(
    order_id: int, *, viewer_user_id: str | None = None
) -> list[dict[str, Any]]:
    """子单编辑可选产品行：对齐 Java getChildsByCanceledAndChecked(2)。

    含：本子单已挂接行 ∪ 父单待处理(op_status=1)行。
    linkedToThis=True 表示当前已挂到本子单（编辑页默认勾选）。
    """
    row = get_order(order_id)
    if not row:
        return []
    ot = str(row.get("orderType") or "").strip()
    if ot not in ("9", "10"):
        return list_order_children(order_id, viewer_user_id=viewer_user_id)
    parent_pk = row.get("parentPkId") or row.get("parentId")
    try:
        parent_id = int(parent_pk) if parent_pk not in (None, "", 0, "0") else 0
    except (TypeError, ValueError):
        parent_id = 0
    try:
        rows = fetch_all(
            f"""
            SELECT {_CHILD_LINE_SELECT},
                   CASE
                     WHEN EXISTS (
                       SELECT 1 FROM exp_qd_purchase_order_child px
                       WHERE px.order_child_id = c.id
                         AND px.purchase_order_id = %(oid)s
                     ) THEN 1 ELSE 0
                   END AS linkedToThis
            FROM experiment_order_child c
            {_CHILD_LINE_JOINS}
            WHERE IFNULL(c.delete_status, 2) <> 1
              AND (
                (c.order_form_id = %(pid)s AND IFNULL(c.op_status, 0) = 1)
                OR EXISTS (
                  SELECT 1 FROM exp_qd_purchase_order_child poc
                  WHERE poc.order_child_id = c.id
                    AND poc.purchase_order_id = %(oid)s
                )
              )
            ORDER BY linkedToThis DESC, c.id ASC
            """,
            {"oid": order_id, "pid": parent_id or -1},
        )
    except Exception:
        # 无 parent 或 SQL 失败时退回已挂接行
        rows = _fetch_children_basic(order_id)
        for r in rows or []:
            r["linkedToThis"] = 1
    # 复用 list_order_children 的标注（状态文案 / canGrab 等）
    if not rows:
        return []
    # 去重
    deduped: list[dict[str, Any]] = []
    seen: set[int] = set()
    for r in rows:
        try:
            cid = int(r.get("id"))
        except (TypeError, ValueError):
            deduped.append(r)
            continue
        if cid in seen:
            continue
        seen.add(cid)
        try:
            r["linkedToThis"] = bool(int(r.get("linkedToThis") or 0))
        except (TypeError, ValueError):
            r["linkedToThis"] = False
        deduped.append(r)
    # 走统一标注逻辑：临时拼成「假订单 children」路径太重，直接复用 list 后按 id 回填
    annotated = list_order_children(order_id, viewer_user_id=viewer_user_id)
    by_id = {}
    for a in annotated:
        try:
            by_id[int(a.get("id"))] = a
        except (TypeError, ValueError):
            pass
    out: list[dict[str, Any]] = []
    for r in deduped:
        try:
            cid = int(r.get("id"))
        except (TypeError, ValueError):
            out.append(r)
            continue
        base = by_id.get(cid)
        if base:
            merged = {**base}
            merged["linkedToThis"] = bool(r.get("linkedToThis"))
            out.append(merged)
        else:
            # 父单待处理未挂接行：补基础标签
            r["orderStatusLabel"] = _child_line_status_label(r.get("orderStatus"))
            r["testUserName"] = str(r.get("testUserTrueName") or r.get("testUserName") or "-")
            r["linkedToThis"] = bool(r.get("linkedToThis"))
            r["canCreateSubLine"] = True
            out.append(r)
    return out


def list_order_children(
    order_id: int, *, viewer_user_id: str | None = None
) -> list[dict[str, Any]]:
    """对齐 Java getChildsByPurchaseId2：产品行 + 仓位/云视频/样品管理单等。

    canGrab 对齐 Java qdorderdetail：待抢池 + 状态<=36 + isqdqx（角色/三级分类）且非 R 类。
    """
    try:
        rows = _fetch_children_basic(order_id)
    except Exception:
        try:
            rows = _fetch_children_fallback(order_id)
        except Exception:
            rows = []
    grab_ctx = _load_grab_perm_ctx(viewer_user_id)
    # 防御：JOIN 仍可能放大时按子行 id 去重
    deduped: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for r in rows:
        try:
            cid = int(r.get("id"))
        except (TypeError, ValueError):
            deduped.append(r)
            continue
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        deduped.append(r)
    rows = deduped
    # 已挂接到未取消分包/实验子单的产品行：创建页不可再选
    linked_active: set[int] = set()
    if seen_ids:
        try:
            id_list = sorted(seen_ids)
            placeholders = ", ".join(f"%(c{i})s" for i in range(len(id_list)))
            params = {f"c{i}": cid for i, cid in enumerate(id_list)}
            linked_rows = fetch_all(
                f"""
                SELECT DISTINCT p.order_child_id AS cid
                FROM exp_qd_purchase_order_child p
                INNER JOIN experiment_order o ON o.id = p.purchase_order_id
                WHERE p.order_child_id IN ({placeholders})
                  AND IFNULL(o.deleteStatus, 0) = 0
                  AND IFNULL(o.order_status, -1) <> 0
                """,
                params,
            )
            for lr in linked_rows or []:
                try:
                    linked_active.add(int(lr["cid"]))
                except (TypeError, ValueError, KeyError):
                    pass
        except Exception:
            linked_active = set()
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
        try:
            op_i = int(r.get("opStatus")) if r.get("opStatus") is not None else 0
        except (TypeError, ValueError):
            op_i = 0
        try:
            cid_i = int(r.get("id"))
        except (TypeError, ValueError):
            cid_i = 0
        already = cid_i in linked_active
        r["alreadyLinked"] = already
        # 创建子单可选：待处理(op=1) 且未挂接有效子单
        r["canCreateSubLine"] = bool(op_i == 1 and not already)
    _attach_child_runtime_fields(rows)
    return rows


def list_order_logs(order_id: int) -> list[dict[str, Any]]:
    """对齐 Java getByOfId + findUserById 回填操作人（trueName / userName）。"""
    rows = fetch_all(
        """
        SELECT
            l.id, l.addTime, l.log_info AS logInfo, l.log_user_id AS logUserId,
            COALESCE(
                NULLIF(TRIM(u.true_name), ''),
                NULLIF(TRIM(u.user_name), ''),
                NULLIF(TRIM(eu.trueName), ''),
                NULLIF(TRIM(eu.userName), '')
            ) AS logUserName
        FROM experiment_order_log l
        LEFT JOIN sy_users u ON CAST(l.log_user_id AS CHAR) = CAST(u.id AS CHAR)
        LEFT JOIN exp_user eu ON CAST(l.log_user_id AS CHAR) = CAST(eu.id AS CHAR)
        WHERE l.of_id = %(oid)s
          AND IFNULL(l.deleteStatus, 0) = 0
        ORDER BY l.addTime DESC
        LIMIT 200
        """,
        {"oid": order_id},
    )
    out: list[dict[str, Any]] = []
    for r in rows or []:
        uid = str(r.get("logUserId") or "").strip()
        name = str(r.get("logUserName") or "").strip()
        if uid and not name:
            looked = str(_user_display_name(uid) or "").strip()
            if looked and looked != uid:
                name = looked
        r["logUserName"] = name
        # 同步给前端 prop=logUser / logUserName
        r["logUser"] = name or "-"
        at = r.get("addTime")
        r["addTime"] = str(at)[:19] if at else ""
        r["logInfo"] = r.get("logInfo") or ""
        out.append(r)
    return out


def list_linked_child_orders(parent_id: int, *, child_order_type: str) -> list[dict[str, Any]]:
    """主单下挂的实验子订单(10) / 分包子订单(9)。"""
    rows = fetch_all(
        """
        SELECT
            t.id, t.order_id AS orderId, t.order_status AS orderStatus,
            t.totalPrice AS totalPrice, t.order_time AS orderTime, t.addTime,
            t.is_confirm AS isConfirm, t.order_type AS orderType,
            t.currency_type AS currencyType,
            t.stock_company_name AS stockCompanyId,
            qs.name AS stockCompanyName,
            u.company_name AS supplierName,
            sm.user_name AS managerName, sm.true_name AS managerTrueName,
            su.user_name AS saleUserName, su.true_name AS saleUserTrueName
        FROM experiment_order t
        LEFT JOIN qd_user_company qs ON CAST(t.stock_company_name AS CHAR) = CAST(qs.id AS CHAR)
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
        if str(child_order_type) == "9":
            r["purchaseTotalPrice"] = r.get("totalPrice")
            r["stockCompanyId"] = str(r.get("stockCompanyId") or "").strip()
            stock = str(r.get("stockCompanyName") or "").strip()
            r["stockCompanyName"] = stock or "-"
            try:
                ct_i = int(r.get("currencyType") or 1)
            except (TypeError, ValueError):
                ct_i = 1
            r["currencyLabel"] = "美金" if ct_i == 2 else "人民币"
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
        try:
            r["id"] = int(r.get("id") or 0)
        except (TypeError, ValueError):
            r["id"] = r.get("id")
        # Java relatedOrderType：5=实验订单(type6)，6=实验分包(type8)
        r["relatedOrderType"] = {"6": "5", "8": "6"}.get(ot, "")
        ordered.append(r)
    return ordered


def _enrich_accessory_urls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from django.conf import settings

    from apps.core.services.sysconfig import get_config_row, image_web_server
    from apps.orders.services.sale_detail_enrich import accessory_url, enrich_accessory_rows

    config = get_config_row()
    # 对齐 Java 订单附件：公网 OSS 域优先，便于 path/name 直链
    base = (
        (getattr(settings, "OSS_PUBLIC_BASE_URL", "") or "").rstrip("/")
        or image_web_server(config)
    )
    out = enrich_accessory_rows(rows, base)
    for a in out:
        a["url"] = accessory_url(base, a)
        if not a.get("info"):
            a["info"] = a.get("name") or ""
    return out


def list_order_files(order_id: int, *, order_type: str | int | None = None) -> list[dict[str, Any]]:
    """对齐 Java：type=6 用 exp_of_id；type=9/10 用 child_of_id（兼查 exp_of_id 兼容旧数据）。"""
    from apps.orders.repositories import accessory_list as acc_repo

    ot = str(order_type or "")
    if ot in ("9", "10"):
        by_child = acc_repo.load_accessories(child_of_id=order_id, exclude_types=(5,))
        by_exp = acc_repo.load_accessories(exp_of_id=order_id, exclude_types=(5,))
        seen: set[int] = set()
        merged: list[dict[str, Any]] = []
        for r in (by_child or []) + (by_exp or []):
            try:
                rid = int(r.get("id") or 0)
            except (TypeError, ValueError):
                rid = 0
            if rid and rid in seen:
                continue
            if rid:
                seen.add(rid)
            merged.append(r)
        return _enrich_accessory_urls(merged)
    rows = acc_repo.load_accessories(exp_of_id=order_id, exclude_types=(5,))
    return _enrich_accessory_urls(rows)


def list_invoice_files(order_id: int, *, order_type: str | int | None = None) -> list[dict[str, Any]]:
    """发票资料：accessory.type = 5。

    主单(type6/8)写 exp_of_id；子单(type9/10)写 child_of_id（上传侧已按订单类型区分）。
    """
    from apps.orders.repositories import accessory_list as acc_repo

    ot = str(order_type or "")
    if ot in ("9", "10"):
        by_child = acc_repo.load_accessories(child_of_id=order_id, file_type=5)
        by_exp = acc_repo.load_accessories(exp_of_id=order_id, file_type=5)
        seen: set[int] = set()
        merged: list[dict[str, Any]] = []
        for r in (by_child or []) + (by_exp or []):
            try:
                rid = int(r.get("id") or 0)
            except (TypeError, ValueError):
                rid = 0
            if rid and rid in seen:
                continue
            if rid:
                seen.add(rid)
            merged.append(r)
        return _enrich_accessory_urls(merged)
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


def _is_audit_admin(user_id: str | int | None) -> bool:
    """对齐 Java isshqx：is_czqx==1；另保留 admin / 系统管理员。"""
    uid = str(user_id or "").strip()
    if not uid:
        return False
    row = fetch_one(
        """
        SELECT user_name AS userName, utoo_type AS utooType, is_czqx AS isCzqx
        FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1
        """,
        {"id": uid},
    )
    if not row:
        return False
    name = str(row.get("userName") or "").strip().lower()
    utoo = str(row.get("utooType") or "").strip()
    try:
        czqx = int(row.get("isCzqx") or 0)
    except (TypeError, ValueError):
        czqx = 0
    return name == "admin" or czqx == 1 or utoo in ("系统管理员",)


def apply_audit_permission(row: dict[str, Any], viewer_user_id: str | int | None) -> None:
    """对齐 Java 详情审核按钮。

    - type=9 分包子单：test_manager 或 isCzqx/admin（isshqx）
    - 其它：sale_manager 或 isCzqx/admin
    """
    try:
        st = int(row.get("orderStatus")) if row.get("orderStatus") is not None else -1
    except (TypeError, ValueError):
        st = -1
    if st != 20:
        row["canAudit"] = False
        return
    uid = str(viewer_user_id or "").strip()
    if not uid:
        row["canAudit"] = False
        return
    if _is_audit_admin(uid):
        row["canAudit"] = True
        return
    ot = str(row.get("orderType") or "")
    if ot == "9":
        tm = str(row.get("testManagerId") or "").strip()
        row["canAudit"] = bool(tm and uid == tm)
    else:
        sm = str(row.get("saleManagerId") or "").strip()
        row["canAudit"] = bool(sm and uid == sm)


def apply_pay_audit_permission(row: dict[str, Any], viewer_user_id: str | int | None) -> None:
    """对齐 Java 付款审核：sale_manager 或 isxsshqx（销售主管且为本单销售主管）。"""
    if not row.get("canAuditPay"):
        return
    uid = str(viewer_user_id or "").strip()
    sm = str(row.get("saleManagerId") or "").strip()
    if not uid:
        row["canAuditPay"] = False
        return
    if _is_audit_admin(uid):
        return
    if uid == sm:
        return
    # 销售主管角色且挂接为本单销售主管（与 uid==sm 等价兜底）
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
    if ("销售主管" in utoo or utoo == "销售主管") and uid == sm:
        return
    row["canAuditPay"] = False


def _apply_save_finish_permission(
    row: dict[str, Any], viewer_user_id: str | int | None
) -> None:
    """对齐 Java isSave：管理员 / 父单或本单销售主管 / 子行测试员。仓库管理员不可保存。"""
    if not row.get("canSaveFinish"):
        return
    uid = str(viewer_user_id or "").strip()
    if not uid:
        row["canSaveFinish"] = False
        return
    if _is_audit_admin(uid):
        return
    allowed: set[str] = set()
    for key in ("saleManagerId",):
        v = str(row.get(key) or "").strip()
        if v:
            allowed.add(v)
    # 父单销售主管
    parent_pk = row.get("parentPkId") or row.get("parentId")
    try:
        pid = int(parent_pk) if parent_pk not in (None, "", 0, "0") else 0
    except (TypeError, ValueError):
        pid = 0
    if pid:
        parent = fetch_one(
            "SELECT sale_manager AS saleManagerId FROM experiment_order WHERE id = %(id)s LIMIT 1",
            {"id": pid},
        )
        v = str((parent or {}).get("saleManagerId") or "").strip()
        if v:
            allowed.add(v)
    try:
        oid = int(row.get("id") or 0)
    except (TypeError, ValueError):
        oid = 0
    if oid:
        testers = fetch_all(
            """
            SELECT DISTINCT c.test_user_id AS tid
            FROM experiment_order_child c
            WHERE (
                c.order_form_id = %(oid)s
                OR EXISTS (
                    SELECT 1 FROM exp_qd_purchase_order_child poc
                    WHERE poc.purchase_order_id = %(oid)s
                      AND poc.order_child_id = c.id
                )
            )
              AND IFNULL(c.delete_status, 2) <> 1
              AND c.test_user_id IS NOT NULL
              AND CAST(c.test_user_id AS CHAR) NOT IN ('0', '22', '')
            """,
            {"oid": oid},
        )
        for t in testers or []:
            tid = str(t.get("tid") or "").strip()
            if tid:
                allowed.add(tid)
    if uid not in allowed:
        row["canSaveFinish"] = False


def _apply_child_edit_permission(
    row: dict[str, Any],
    viewer_user_id: str | int | None,
    *,
    role_ctx: dict[str, Any] | None = None,
) -> None:
    """对齐 Java 子单详情：编辑/取消仅相关人员 + 管理员；H/R 整段操作按钮不展示。"""
    ot = str(row.get("orderType") or "")
    ctx = role_ctx or _viewer_role_context(viewer_user_id)
    role = str(ctx.get("role") or "")
    if role in ("H类用户", "R类人员"):
        row["canEdit"] = False
        row["canCancel"] = False
        row["canSubmitAudit"] = False
        row["canWithdrawAudit"] = False
        row["canAudit"] = False
        row["canSaveFinish"] = False
        return
    if ot not in ("9", "10"):
        return
    if not row.get("canEdit") and not row.get("canCancel"):
        return
    uid = str(viewer_user_id or "").strip()
    if not uid:
        row["canEdit"] = False
        row["canCancel"] = False
        return
    if _is_audit_admin(uid):
        return
    allowed = {
        str(row.get("addUserId") or "").strip(),
        str(row.get("saleManagerId") or "").strip(),
        str(row.get("saleUserId") or "").strip(),
        str(row.get("testUserId") or "").strip(),
        str(row.get("testManagerId") or "").strip(),
    }
    # 子行测试员也可取消/编辑（对齐 Java testUser）
    try:
        oid = int(row.get("id") or 0)
    except (TypeError, ValueError):
        oid = 0
    if oid:
        try:
            testers = fetch_all(
                """
                SELECT DISTINCT c.test_user_id AS tid
                FROM experiment_order_child c
                WHERE (
                    c.order_form_id = %(oid)s
                    OR EXISTS (
                        SELECT 1 FROM exp_qd_purchase_order_child poc
                        WHERE poc.purchase_order_id = %(oid)s
                          AND poc.order_child_id = c.id
                    )
                )
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND c.test_user_id IS NOT NULL
                """,
                {"oid": oid},
            )
            for t in testers or []:
                allowed.add(str(t.get("tid") or "").strip())
        except Exception:
            pass
    allowed.discard("")
    if uid not in allowed:
        row["canEdit"] = False
        row["canCancel"] = False


def list_order_bills(order_id: int) -> list[dict[str, Any]]:
    """收款/开票票据列表，对齐 Java openBills / 实际收款分行。"""
    rows = fetch_all(
        """
        SELECT
            b.id, b.money, b.type, b.bill_date AS billDate, b.add_time AS addTime,
            b.mark AS mark,
            COALESCE(u.true_name, u.user_name, '') AS addUserName
        FROM qd_bill b
        LEFT JOIN sy_users u ON CAST(b.add_user_id AS CHAR) = CAST(u.id AS CHAR)
        WHERE b.exp_of_id = %(oid)s
        ORDER BY IFNULL(b.bill_date, b.add_time) ASC, b.id ASC
        """,
        {"oid": order_id},
    )
    online_ids: set[int] = set()
    try:
        online_rows = fetch_all(
            "SELECT qd_bill_id AS bid FROM exp_online_qd_bill WHERE exp_of_id = %(oid)s",
            {"oid": order_id},
        ) or []
        for r in online_rows:
            try:
                online_ids.add(int(r.get("bid")))
            except (TypeError, ValueError):
                pass
    except Exception:
        online_ids = set()
    out: list[dict[str, Any]] = []
    for r in rows or []:
        try:
            btype = int(r.get("type") or 0)
        except (TypeError, ValueError):
            btype = 0
        try:
            bid = int(r.get("id") or 0)
        except (TypeError, ValueError):
            bid = 0
        bd = r.get("billDate") or r.get("addTime")
        out.append(
            {
                "id": r.get("id"),
                "money": r.get("money"),
                "type": btype,
                "typeLabel": "开票" if btype == 1 else ("收款" if btype == 2 else str(btype)),
                "billDate": str(bd)[:19] if bd else "",
                "mark": str(r.get("mark") or ""),
                "isOnline": 1 if bid in online_ids else 0,
                "addUserName": str(r.get("addUserName") or "").strip() or "-",
            }
        )
    return out


def list_online_receive_bills(order_id: int) -> list[dict[str, Any]]:
    """线上收款单（exp_online_qd_bill type=2），对齐 Java 实际线上收款时间/金额。"""
    try:
        rows = fetch_all(
            """
            SELECT
                b.id, b.money, b.type,
                b.bill_date AS billDate, b.add_time AS addTime,
                b.mark AS mark, b.qd_bill_id AS qdBillId
            FROM exp_online_qd_bill b
            WHERE b.exp_of_id = %(oid)s AND b.type = 2
            ORDER BY IFNULL(b.bill_date, b.add_time) ASC, b.id ASC
            """,
            {"oid": order_id},
        )
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for r in rows or []:
        bd = r.get("billDate") or r.get("addTime")
        out.append(
            {
                "id": r.get("id"),
                "money": r.get("money"),
                "type": 2,
                "typeLabel": "线上收款",
                "billDate": str(bd)[:19] if bd else "",
                "mark": str(r.get("mark") or ""),
                "qdBillId": r.get("qdBillId"),
                "isOnline": 1,
            }
        )
    return out


def attach_expect_pay_actuals(row: dict[str, Any], bills: list[dict[str, Any]]) -> None:
    """把预计收款槽位与实际收款/开票按序号对齐，便于详情分行展示时间。"""
    expect = list(row.get("expectPayList") or [])
    recv = [b for b in bills if int(b.get("type") or 0) == 2]
    inv = [b for b in bills if int(b.get("type") or 0) == 1]
    try:
        oid = int(row.get("id") or 0)
    except (TypeError, ValueError):
        oid = 0
    online_recv = list_online_receive_bills(oid) if oid else []
    for i, ep in enumerate(expect):
        if i < len(online_recv):
            ep["actualOnlineReceiveTime"] = online_recv[i].get("billDate") or ""
            ep["actualOnlineReceiveAmount"] = online_recv[i].get("money")
        if i < len(recv):
            ep["actualReceiveTime"] = recv[i].get("billDate") or ""
            ep["actualReceiveAmount"] = recv[i].get("money")
            ep["actualReceiveOnline"] = int(recv[i].get("isOnline") or 0) == 1
        if i < len(inv):
            ep["actualInvoiceTime"] = inv[i].get("billDate") or ""
            ep["actualInvoiceAmount"] = inv[i].get("money")
    row["expectPayList"] = expect
    row["receiveBills"] = recv
    row["onlineReceiveBills"] = online_recv
    row["invoiceBills"] = inv


def _link_exp_purchase_child(
    *, purchase_order_id: int, order_child_id: int, order_type: str
) -> bool:
    """写入 exp_qd_purchase_order_child。

    Java getChildsByPurchaseId2 强制 poc.order_type=9/10，缺该字段时老系统产品表为空。
    部分库无 addTime / order_type；失败语句必须走 savepoint，避免污染外层事务。
    """
    ot = str(order_type or "").strip()
    params = {"pid": int(purchase_order_id), "cid": int(order_child_id), "ot": ot}
    variants = (
        """
            INSERT INTO exp_qd_purchase_order_child
                (purchase_order_id, order_child_id, order_type, addTime)
            VALUES (%(pid)s, %(cid)s, %(ot)s, NOW())
            """,
        """
            INSERT INTO exp_qd_purchase_order_child
                (purchase_order_id, order_child_id, order_type)
            VALUES (%(pid)s, %(cid)s, %(ot)s)
            """,
        """
            INSERT INTO exp_qd_purchase_order_child (purchase_order_id, order_child_id, addTime)
            VALUES (%(pid)s, %(cid)s, NOW())
            """,
        """
            INSERT INTO exp_qd_purchase_order_child (purchase_order_id, order_child_id)
            VALUES (%(pid)s, %(cid)s)
            """,
    )
    for sql in variants:
        try:
            with transaction.atomic():
                execute(sql, params)
            return True
        except Exception:
            continue
    return False


def _sync_sub_order_purchase_children(
    *, order_id: int, order_type: str, keep_ids: set[int]
) -> tuple[bool, str]:
    """子单编辑按勾选同步挂接：对齐 Java updatePurchaseOrder(checkChilds)。

    - 取消勾选：删 purchase 关联，op_status 回 1（产品行仍属主单，勿软删）
    - 新勾选：建关联，op_status=2
    """
    if not keep_ids:
        return False, "请至少选择一个子订单"
    ot = str(order_type or "").strip()
    order = get_order(order_id)
    parent_id = int((order or {}).get("parentPkId") or (order or {}).get("parentId") or 0)
    if not parent_id:
        return False, "子订单缺少来源主订单"
    # 禁止勾选已挂到其他有效子单的产品行
    id_list = sorted(keep_ids)
    placeholders = ", ".join(f"%(c{i})s" for i in range(len(id_list)))
    params: dict[str, Any] = {f"c{i}": cid for i, cid in enumerate(id_list)}
    params["oid"] = order_id
    conflict = fetch_all(
        f"""
        SELECT DISTINCT p.order_child_id AS cid, o.order_id AS ono
        FROM exp_qd_purchase_order_child p
        INNER JOIN experiment_order o ON o.id = p.purchase_order_id
        WHERE p.order_child_id IN ({placeholders})
          AND p.purchase_order_id <> %(oid)s
          AND IFNULL(o.deleteStatus, 0) = 0
          AND IFNULL(o.order_status, -1) <> 0
        """,
        params,
    )
    if conflict:
        nos = ", ".join(str(x.get("ono") or x.get("cid")) for x in conflict[:5])
        return False, f"所选产品行已挂接其他子订单：{nos}"
    owned_rows = fetch_all(
        f"""
        SELECT DISTINCT c.id
        FROM experiment_order_child c
        LEFT JOIN exp_qd_purchase_order_child poc
          ON poc.order_child_id = c.id AND poc.purchase_order_id = %(oid)s
        WHERE c.id IN ({placeholders})
          AND IFNULL(c.delete_status, 2) <> 1
          AND (c.order_form_id = %(pid)s OR poc.purchase_order_id = %(oid)s)
        """,
        {**params, "pid": parent_id},
    )
    if {int(r["id"]) for r in owned_rows} != keep_ids:
        return False, "所选产品不属于当前子订单的来源主单"
    try:
        with transaction.atomic():
            # 锁住待挂接的主单产品行：并发编辑同一行时，后一请求必须等前者完成，
            # 再依据事务内的关联记录判断冲突，避免双挂接。
            locked_rows = fetch_all(
                f"""
                SELECT id FROM experiment_order_child
                WHERE id IN ({placeholders})
                FOR UPDATE
                """,
                params,
            )
            if {int(r["id"]) for r in locked_rows} != keep_ids:
                return False, "所选产品不存在"
            conflict_after_lock = fetch_all(
                f"""
                SELECT DISTINCT p.order_child_id AS cid, o.order_id AS ono
                FROM exp_qd_purchase_order_child p
                INNER JOIN experiment_order o ON o.id = p.purchase_order_id
                WHERE p.order_child_id IN ({placeholders})
                  AND p.purchase_order_id <> %(oid)s
                  AND IFNULL(o.deleteStatus, 0) = 0
                  AND IFNULL(o.order_status, -1) <> 0
                """,
                params,
            )
            if conflict_after_lock:
                nos = ", ".join(
                    str(x.get("ono") or x.get("cid")) for x in conflict_after_lock[:5]
                )
                return False, f"所选产品行已挂接其他子订单：{nos}"
            linked_rows = fetch_all(
                """
                SELECT order_child_id AS cid
                FROM exp_qd_purchase_order_child
                WHERE purchase_order_id = %(oid)s
                """,
                {"oid": order_id},
            )
            linked_ids = {int(r["cid"]) for r in linked_rows if r.get("cid") not in (None, "")}
            for eid in linked_ids:
                execute(
                    "UPDATE experiment_order_child SET op_status = 1 WHERE id = %(cid)s",
                    {"cid": eid},
                )
            execute(
                "DELETE FROM exp_qd_purchase_order_child WHERE purchase_order_id = %(oid)s",
                {"oid": order_id},
            )
            for cid in sorted(keep_ids):
                if not _link_exp_purchase_child(
                    purchase_order_id=order_id, order_child_id=cid, order_type=ot
                ):
                    raise RuntimeError("写入产品挂接失败")
                execute(
                    """
                    UPDATE experiment_order_child
                    SET op_status = 2,
                        order_status = CASE
                            WHEN IFNULL(order_status, 0) < 2 THEN 2 ELSE order_status
                        END
                    WHERE id = %(cid)s
                    """,
                    {"cid": cid},
                )
    except Exception as exc:
        logger.exception("sync purchase children failed order=%s", order_id)
        return False, f"更新产品挂接失败：{exc}"
    repair_exp_purchase_child_order_types(order_id)
    logger.info(
        "edit sync purchase children order=%s ot=%s keep=%s was=%s",
        order_id,
        ot,
        sorted(keep_ids),
        sorted(linked_ids),
    )
    return True, "ok"


def repair_exp_purchase_child_order_types(purchase_order_id: int | None = None) -> None:
    """回填历史关联行缺失的 order_type，供 Java 详情查询。"""
    try:
        if purchase_order_id:
            execute(
                """
                UPDATE exp_qd_purchase_order_child poc
                INNER JOIN experiment_order o ON o.id = poc.purchase_order_id
                SET poc.order_type = CAST(o.order_type AS CHAR)
                WHERE poc.purchase_order_id = %(pid)s
                  AND (
                    poc.order_type IS NULL
                    OR poc.order_type = ''
                    OR CAST(poc.order_type AS CHAR) <> CAST(o.order_type AS CHAR)
                  )
                  AND CAST(o.order_type AS CHAR) IN ('9', '10')
                """,
                {"pid": int(purchase_order_id)},
            )
        else:
            execute(
                """
                UPDATE exp_qd_purchase_order_child poc
                INNER JOIN experiment_order o ON o.id = poc.purchase_order_id
                SET poc.order_type = CAST(o.order_type AS CHAR)
                WHERE (poc.order_type IS NULL OR poc.order_type = '')
                  AND CAST(o.order_type AS CHAR) IN ('9', '10')
                """
            )
    except Exception:
        pass


def get_order_detail_bundle(
    order_id: int, *, viewer_user_id: str | None = None
) -> dict[str, Any] | None:
    """Java orderdetail 聚合：主信息 + 产品行 + 关联子单 + 关联订单 + 操作日志 + 订单资料。"""
    row = get_order(order_id)
    if not row:
        return None
    apply_audit_permission(row, viewer_user_id)
    apply_pay_audit_permission(row, viewer_user_id)
    ot = str(row.get("orderType") or "")
    # 打开子单详情时顺带回填，修复历史单在 Java 端产品表为空
    if ot in ("9", "10"):
        repair_exp_purchase_child_order_types(order_id)
    children = list_order_children(order_id, viewer_user_id=viewer_user_id)
    role_ctx = _viewer_role_context(viewer_user_id)
    logs = _filter_order_logs_for_viewer(
        list_order_logs(order_id),
        viewer_user_id=viewer_user_id,
        role_ctx=role_ctx,
    )
    bills = list_order_bills(order_id)
    attach_expect_pay_actuals(row, bills)
    linked: list[dict[str, Any]] = []
    if ot == "6":
        linked = list_linked_child_orders(order_id, child_order_type="10")
    elif ot == "8":
        linked = list_linked_child_orders(order_id, child_order_type="9")
    related = list_related_orders(row.get("relatedOrderNum"))
    files = list_order_files(order_id, order_type=ot)
    # 对齐 Java：子单订单资料附带主单「预约单」附件
    if ot in ("9", "10"):
        parent_pk = row.get("parentPkId") or row.get("parentId")
        try:
            pid = int(parent_pk) if parent_pk not in (None, "", 0, "0") else 0
        except (TypeError, ValueError):
            pid = 0
        if pid:
            parent_files = list_order_files(pid, order_type=str(row.get("parentOrderType") or "6"))
            seen_ids = set()
            for f in files:
                try:
                    seen_ids.add(int(f.get("id") or 0))
                except (TypeError, ValueError):
                    pass
            for f in parent_files:
                info = str(f.get("info") or f.get("name") or "")
                if not info.endswith("预约单"):
                    continue
                try:
                    fid = int(f.get("id") or 0)
                except (TypeError, ValueError):
                    fid = 0
                if fid and fid in seen_ids:
                    continue
                if fid:
                    seen_ids.add(fid)
                files.append(f)
    invoice_files = list_invoice_files(order_id, order_type=ot)
    yyd_files = [f for f in files if str(f.get("type") or "") == "6"]
    can_view_share = bool(role_ctx.get("can_view_share"))
    row["canViewShareInfo"] = can_view_share
    row["canViewLogs"] = bool(role_ctx.get("can_view_logs"))
    # Java isFlag 仅实验分包采购子单详情（type 9/10）隐藏财务；实验主单详情始终展示总价/币种/开票等
    can_view_finance = bool(role_ctx.get("can_view_finance", True))
    if ot not in ("9", "10"):
        can_view_finance = True
    row["canViewFinance"] = can_view_finance
    # 对齐 Java isFlag=false：测试主管/测试人员不返回付款·开票「数据」；
    # 上传付款/开票/申请付款按钮仍按状态显隐（Java 未用 isFlag 包按钮）。
    if not can_view_finance:
        row["expectPayList"] = []
        row["receiveBills"] = []
        row["onlineReceiveBills"] = []
        row["invoiceBills"] = []
        row["totalPrice"] = None
        row["currencyLabel"] = ""
        row["payWayName"] = ""
        row["payStatusLabel"] = ""
        row["invoiceLabel"] = ""
        row["invoiceType"] = None
        row["inBillTypeName"] = ""
        row["taxes"] = ""
        row["invoiceAmount"] = None
        row["receiveAmount"] = None
        bills = []
        invoice_files = []
        for ch in children:
            ch["costPrice"] = None
        # 测试主管不可做付款审核（销售主管权限）；保留上传入口条件
        row["canAuditPay"] = False
        row["canInvoice"] = False
        row["canReceiveBill"] = False
        row["canConfirmPay"] = False
    if not can_view_share or not role_ctx.get("can_view_share_detail"):
        # 隐藏区或 C 类：不返回分成明细（C 类仍显示空的分成信息标签）
        row["userScaleLabel"] = ""
        row["costScaleLabel"] = ""
        row["userScaleInfo"] = ""
        row["scaleInfo"] = ""
        row["salecbUserScaleInfo"] = ""
    if not role_ctx.get("can_share_ratio"):
        row["canShareRatio"] = False
    _apply_child_edit_permission(row, viewer_user_id, role_ctx=role_ctx)
    _apply_save_finish_permission(row, viewer_user_id)
    # 样品按钮按当前登录人再过滤（仓库管理员只保留到货）
    if ot in ("9", "10"):
        from apps.admin_experiment.repositories import sample_flow as sample_flow_repo

        sample_flow_repo.attach_sample_action_flags(row, viewer_user_id=viewer_user_id)
    # 子单编辑勾选：已挂接 ∪ 父单待处理行（对齐 Java saleChilds）
    edit_selectable: list[dict[str, Any]] = []
    if ot in ("9", "10"):
        try:
            edit_selectable = list_edit_selectable_children(
                order_id, viewer_user_id=viewer_user_id
            )
        except Exception:
            edit_selectable = [
                {**ch, "linkedToThis": True} for ch in (children or [])
            ]
    return {
        **row,
        "children": children,
        "editSelectableChildren": edit_selectable,
        "logs": logs,
        "bills": bills,
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
    uid = str(staff_user_id or "").strip()
    ot = str(row.get("orderType") or "")
    if ot == "9":
        # 对齐 Java：实验室测试主管 / isCzqx
        tm = str(row.get("testManagerId") or "").strip()
        if not uid or (uid != tm and not _is_audit_admin(uid)):
            return False, "无审核权限（需实验室测试主管）"
    else:
        sm = str(row.get("saleManagerId") or "").strip()
        if not uid or (uid != sm and not _is_audit_admin(uid)):
            return False, "无审核权限"
    next_status = 30 if pass_ else 10
    _set_order_status(order_id, next_status)
    _write_order_log(
        order_id,
        ("审核通过" if pass_ else "审核驳回") + (f"：{remark}" if remark else ""),
        user_id=staff_user_id,
    )
    if pass_ and ot == "9":
        # 主单收款可能早于子单审核；审核通过后补触发 type=8 分钱
        try:
            from apps.admin_experiment.services.split_money import (
                try_split_type8_parent_from_child,
            )

            try_split_type8_parent_from_child(order_id)
        except Exception:
            pass
    try:
        from apps.admin_experiment.services.wx_suborder_notify import notify_audit_result

        notify_audit_result(
            order_id=order_id, passed=pass_, staff_user_id=staff_user_id
        )
    except Exception:
        pass
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
    try:
        from apps.admin_experiment.services.wx_suborder_notify import notify_submit_audit

        notify_submit_audit(order_id=order_id)
    except Exception:
        pass
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
        try_finish_main_order(order_id=order_id, staff_user_id=staff_user_id)
        return True, f"已标记成本结清（分钱补分失败：{exc}）"
    try_finish_main_order(order_id=order_id, staff_user_id=staff_user_id)
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


def _viewer_role_context(viewer_user_id: str | int | None) -> dict[str, Any]:
    """详情页角色可见性：分成 / 操作日志 / 付款开票（对齐 Java isFlag + C 类约束）。"""
    ctx = {
        "utoo": "",
        "role": "",
        "can_view_share": True,
        "can_view_share_detail": True,
        "can_share_ratio": True,
        "can_view_logs": True,
        "can_view_all_logs": False,
        # Java ExpSubPurchaseOrder isFlag：仅 type9/10 详情对测试主管/测试人员隐藏付款·开票·总价·币种等
        "can_view_finance": True,
        "is_c_sales": False,
        "is_test_role": False,
    }
    uid = str(viewer_user_id or "").strip()
    if not uid:
        ctx["can_view_all_logs"] = True
        return ctx
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
    role = _resolve_utoo_role_name(utoo)
    ctx["utoo"] = utoo
    ctx["role"] = role
    is_c = role == "C类销售人员" or "C类销售人员" in utoo
    ctx["is_c_sales"] = is_c
    is_test_mgr = "测试主管" in utoo
    is_test_user = ("测试人员" in utoo) and (not is_test_mgr)
    if is_test_mgr or is_test_user:
        ctx["is_test_role"] = True
        ctx["can_view_share"] = False
        ctx["can_view_share_detail"] = False
        ctx["can_share_ratio"] = False
        ctx["can_view_finance"] = False
        # 对齐 Java 详情：测试主管/测试人员可看完整操作记录（非仅本人）
        ctx["can_view_all_logs"] = True
    if role in ("R类人员", "H类用户"):
        ctx["can_view_share"] = False
        ctx["can_view_share_detail"] = False
        ctx["can_share_ratio"] = False
        ctx["can_view_logs"] = False
    if is_c:
        # Java：分成区只显示空的「毛利/成本」；操作记录仅 R 类隐藏，C 类可看完整日志
        ctx["can_view_share"] = True
        ctx["can_view_share_detail"] = False
        ctx["can_share_ratio"] = False
        ctx["can_view_all_logs"] = True
    if role in ("销售主管", "系统管理员") or utoo in ("销售主管", "系统管理员"):
        ctx["can_view_all_logs"] = True
    return ctx


def _viewer_can_see_share(viewer_user_id: str | int | None) -> bool:
    """测试主管/测试人员及 R/H 类不可看分成信息。"""
    return bool(_viewer_role_context(viewer_user_id).get("can_view_share"))


def _filter_order_logs_for_viewer(
    logs: list[dict[str, Any]],
    *,
    viewer_user_id: str | int | None,
    role_ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    if not role_ctx.get("can_view_logs"):
        return []
    if role_ctx.get("can_view_all_logs"):
        return logs
    uid = str(viewer_user_id or "").strip()
    if not uid:
        return logs
    return [lg for lg in logs if str(lg.get("logUserId") or "").strip() == uid]


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
    staff_user_id: str | int | None = None,
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
    _write_order_log(order_id, f"增加关联订单：{related_no}", user_id=staff_user_id)
    _write_order_log(int(other["id"]), f"被关联到订单：{self_no}", user_id=staff_user_id)
    return True, "关联成功"


def del_related_order(
    *,
    of_order_no: str,
    related_order_no: str,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
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
        _write_order_log(int(owner["id"]), f"删除关联订单：{remove_no}", user_id=staff_user_id)

    _strip_one(of_no, rel_no)
    _strip_one(rel_no, of_no)
    return True, "删除成功"


def save_finish_times(
    *, order_id: int, items: list[dict[str, Any]], staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    _apply_save_finish_permission(row, staff_user_id)
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
    *,
    order_id: int,
    money: Any,
    staff_user_id: str = "",
    log_info: str = "录入开票",
    accessory_id: int | str | None = None,
    bill_date: str = "",
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
    try:
        acc_id = int(accessory_id) if accessory_id not in (None, "") else None
    except (TypeError, ValueError):
        acc_id = None
    if acc_id is not None and acc_id <= 0:
        acc_id = None
    bdate = str(bill_date or "").strip()[:19]
    params = {
        "oid": order_id,
        "money": amt,
        "log_info": (log_info or "录入开票")[:500],
        "uid": staff_user_id or None,
        "aid": acc_id,
        "bdate": bdate,
    }
    sql = """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark{acc_col})
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 1, 0, {bdate_sql}, %(log_info)s{acc_val})
        """
    execute(
        sql.format(
            acc_col=", accessory_id" if acc_id else "",
            acc_val=", %(aid)s" if acc_id else "",
            bdate_sql="%(bdate)s" if bdate else "NOW()",
        ),
        params,
    )
    _write_order_log(order_id, f"开票 {amt}", user_id=staff_user_id)
    try_finish_main_order(order_id=order_id, staff_user_id=staff_user_id)
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
    """对齐 Java geranateYydForm：写地址、标记 is_yyd、生成预约单 PDF(type=6)。

    仅线下单可手动生成；线上单由收款后自动生成。预约单只允许生成一次。
    """
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    try:
        is_online = int(row.get("isOnline") or 0)
    except (TypeError, ValueError):
        is_online = 0
    if is_online == 1:
        return False, "线上订单收款后自动生成预约单，不可手动生成"
    if not bool(row.get("canGenerateAppointment")):
        if bool(row.get("isYyd")):
            return False, "预约单已生成，不可重复生成"
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
        try:
            execute(
                "UPDATE experiment_order SET is_yyd = 0 WHERE id = %(id)s",
                {"id": order_id},
            )
        except Exception:
            pass
        return False, f"PDF 生成失败：{pdf_msg}"
    return True, "已生成预约单"


def _resolve_pdf_font() -> str:
    """Windows/Linux 优先系统中文字体，避免 Helvetica 写中文导致 PDF 失败。"""
    import os

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont("UtooCJK", path, subfontIndex=0))
            return "UtooCJK"
        except Exception:
            try:
                pdfmetrics.registerFont(TTFont("UtooCJK", path))
                return "UtooCJK"
            except Exception:
                continue
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        return "Helvetica"


def _build_appointment_pdf(*, order_id: int, test_address_id: int) -> tuple[bool, str]:
    """生成预约单 PDF 并写入 accessory type=6。

    版式对齐 Java 管理端预约单样张：
    - 标题 + 右上二维码 + 创建日期（标题用实验项目名）
    - 主信息：实验项目/订单编号/下单时间/寄方信息/寄送地址（收件人详写）/
      是否回收样品/云视频/线下到场/我要上机
    - 每个样品：EDS主要成分、无法喷金注意事项、样品二维码块
      （二维码内容 childId_{子单pk}；样品编号/名称/数量/实验项目）
    """
    try:
        from datetime import datetime
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Image,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        from apps.orders.repositories import accessory as accessory_repo
        from apps.orders.repositories import print_pdf as print_pdf_repo
        from apps.orders.services.accessory_upload import save_order_attachment
    except Exception as exc:
        return False, f"缺少 PDF 依赖: {exc}"

    def _yn(val: Any) -> str:
        return "是" if _truthy_flag(val) else "否"

    rows = print_pdf_repo.fetch_print_pdf_rows(order_id)
    if not rows:
        order = fetch_one(
            """
            SELECT
                t.id AS eid, t.order_id AS ord_id, t.addTime,
                t.test_address_id, t.reverso_context,
                t.send_address, t.addressee_name, t.addressee_mobile,
                t.is_video, t.is_arrive, t.is_on
            FROM experiment_order t
            WHERE t.id = %(id)s
            LIMIT 1
            """,
            {"id": order_id},
        )
        if not order:
            return False, "订单不存在"
        rows = [order]

    first = dict(rows[0])
    addr_id = test_address_id or first.get("test_address_id") or 0
    try:
        addr_id = int(addr_id or 0)
    except (TypeError, ValueError):
        addr_id = 0
    addr_row = print_pdf_repo.get_test_address(addr_id) or {} if addr_id else {}

    order_no = str(first.get("ord_id") or order_id)
    add_time = str(first.get("addTime") or "")[:19]
    # 寄方信息：仅咨询单/订单寄件人（勿用测试地址收件人冒充；详情页无该字段时常为空）
    sender_name = (
        str(first.get("userName") or "").strip()
        or str(first.get("addressee_name") or "").strip()
    )
    sender_mobile = (
        str(first.get("sc_mobile") or "").strip()
        or str(first.get("addressee_mobile") or "").strip()
    )
    # 样品寄送地址：所选测试地址的收件人/电话/地址（对齐 Java 详写）
    recv_name = str(addr_row.get("trueName") or "").strip()
    recv_mobile = str(addr_row.get("mobile") or "").strip()
    recv_addr = (
        str(addr_row.get("address") or "").strip()
        or str(first.get("sc_send_address") or "").strip()
        or str(first.get("send_address") or "").strip()
    )
    if recv_name or recv_mobile or recv_addr:
        address_text = (
            f"收件人姓名：{recv_name or '-'}\n"
            f"收件人电话：{recv_mobile or '-'}\n"
            f"寄送地址：{recv_addr or '-'}"
        )
    else:
        address_text = ""
    contact_name = sender_name
    contact_mobile = sender_mobile

    rev = first.get("reverso_context")
    if rev in (None, "") and first.get("sc_reverso_context") not in (None, ""):
        rev = first.get("sc_reverso_context")
    recovery_label = "是" if _reverso_is_yes(rev) else "否"
    video_label = _yn(first.get("is_video"))
    arrive_label = _yn(first.get("is_arrive"))
    on_label = _yn(first.get("is_on"))

    child_list: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row in rows:
        r = dict(row)
        cid = r.get("cid")
        if not cid:
            continue
        try:
            cid_i = int(cid)
        except (TypeError, ValueError):
            continue
        if cid_i in seen:
            continue
        seen.add(cid_i)
        child_list.append(
            {
                "cid": cid_i,
                "orderId": str(r.get("ordc_id") or ""),
                "goodsName": str(r.get("goods_name") or ""),
                "goodsNums": r.get("goods_nums"),
                "projectName": str(r.get("experiment_project_name") or ""),
                "className": str(r.get("experiment_class_name") or ""),
                "mainComponent": str(r.get("main_component") or ""),
                "goldDesc": str(r.get("gold_desc") or ""),
            }
        )
    if not child_list:
        for ch in fetch_all(
            """
            SELECT
                c.id AS cid, c.order_id AS orderId, c.goods_name AS goodsName, c.goods_nums AS goodsNums,
                c.experiment_project_name AS projectName, c.experiment_class_name AS className,
                osi.main_component AS mainComponent, osi.gold_desc AS goldDesc
            FROM experiment_order_child c
            LEFT JOIN order_sample_information osi ON c.sample_id = osi.id
            WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
            ORDER BY c.id ASC
            LIMIT 100
            """,
            {"oid": order_id},
        ) or []:
            try:
                cid_i = int(ch.get("cid") or 0)
            except (TypeError, ValueError):
                cid_i = 0
            child_list.append(
                {
                    "cid": cid_i,
                    "orderId": str(ch.get("orderId") or ""),
                    "goodsName": str(ch.get("goodsName") or ""),
                    "goodsNums": ch.get("goodsNums"),
                    "projectName": str(ch.get("projectName") or ""),
                    "className": str(ch.get("className") or ""),
                    "mainComponent": str(ch.get("mainComponent") or ""),
                    "goldDesc": str(ch.get("goldDesc") or ""),
                }
            )

    # 标题/实验项目：用实验项目名，不用测试分类（class）
    project_name = (
        (child_list[0].get("projectName") if child_list else "")
        or str(first.get("experiment_project_name") or "").strip()
        or (child_list[0].get("className") if child_list else "")
        or str(first.get("experiment_class_name") or "").strip()
        or "实验"
    )
    font_name = _resolve_pdf_font()
    create_date = datetime.now().strftime("%Y-%m-%d")

    try:
        buf = BytesIO()
        page_w, _page_h = A4
        left_m = 12 * mm
        right_m = 12 * mm
        usable = page_w - left_m - right_m
        label_w = 42 * mm
        value_w = usable - label_w

        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=left_m,
            rightMargin=right_m,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        title_style = ParagraphStyle(
            "YydTitle",
            fontName=font_name,
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
        )
        body_style = ParagraphStyle(
            "YydBody",
            fontName=font_name,
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
        )
        date_style = ParagraphStyle(
            "YydDate",
            fontName=font_name,
            fontSize=11,
            leading=14,
            alignment=TA_RIGHT,
        )
        sample_text_style = ParagraphStyle(
            "YydSampleText",
            fontName=font_name,
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
        )

        def _cell(text: str, style: ParagraphStyle | None = None) -> Paragraph:
            raw = str(text if text is not None else "")
            safe = (
                raw.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            return Paragraph(safe, style or body_style)

        def _qr_image(payload: str, size_mm: float = 22) -> Any:
            try:
                import qrcode

                qr = qrcode.QRCode(version=2, box_size=4, border=1)
                qr.add_data(payload or " ")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buf = BytesIO()
                qr_img.save(qr_buf, format="PNG")
                qr_buf.seek(0)
                return Image(qr_buf, width=size_mm * mm, height=size_mm * mm)
            except Exception:
                return _cell(" ")

        # 页眉：标题 + 订单二维码；创建日期右对齐
        head_qr = _qr_image(order_no, 22)
        head = Table(
            [
                [_cell(f"{project_name}-预约单", title_style), head_qr],
                [_cell(f"创建日期：{create_date}", date_style), ""],
            ],
            colWidths=[usable - 28 * mm, 28 * mm],
        )
        head.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 1), (1, 1)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        sender_text = (
            f"联系人姓名: {contact_name or '-'}\n联系人电话: {contact_mobile or '-'}"
            if (contact_name or contact_mobile)
            else ""
        )
        data: list[list[Any]] = [
            [_cell("实验项目"), _cell(project_name)],
            [_cell("订单编号"), _cell(order_no)],
            [_cell("下单时间"), _cell(add_time)],
            [_cell("寄方信息"), _cell(sender_text)],
            [_cell("样品寄送地址"), _cell(address_text)],
            [_cell("是否回收样品"), _cell(recovery_label)],
            [_cell("是否云视频"), _cell(video_label)],
            [_cell("是否线下到场"), _cell(arrive_label)],
            [_cell("是否我要上机"), _cell(on_label)],
        ]

        span_rows: list[int] = []
        for ch in child_list:
            oid = str(ch.get("orderId") or "")
            nums = ch.get("goodsNums")
            try:
                nums_s = str(float(nums)).rstrip("0").rstrip(".") if nums not in (None, "") else ""
                if nums not in (None, "") and float(nums) == int(float(nums)):
                    nums_s = str(int(float(nums)))
            except (TypeError, ValueError):
                nums_s = str(nums or "")
            proj = str(ch.get("projectName") or project_name or "")
            data.append([_cell("EDS主要成分"), _cell(str(ch.get("mainComponent") or ""))])
            data.append([_cell("无法喷金注意事项"), _cell(str(ch.get("goldDesc") or ""))])

            # 小程序扫码约定：childId_{子单数字主键}，否则无法回显样品 ID
            try:
                cid_i = int(ch.get("cid") or 0)
            except (TypeError, ValueError):
                cid_i = 0
            qr_payload = f"childId_{cid_i}" if cid_i > 0 else (oid or order_no)
            sample_qr = _qr_image(qr_payload, 28)
            sample_info = _cell(
                f"样品编号：{oid}\n"
                f"样品名称：{ch.get('goodsName') or ''}\n"
                f"样品数量：{nums_s}\n"
                f"实验项目：{proj}",
                sample_text_style,
            )
            sample_box = Table(
                [[sample_qr, sample_info]],
                colWidths=[32 * mm, value_w + label_w - 32 * mm - 4 * mm],
            )
            sample_box.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                    ]
                )
            )
            span_rows.append(len(data))
            data.append([sample_box, ""])

        table = Table(data, colWidths=[label_w, value_w])
        style_cmds: list[Any] = [
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for ri in span_rows:
            style_cmds.append(("SPAN", (0, ri), (1, ri)))
            style_cmds.append(("LEFTPADDING", (0, ri), (1, ri), 0))
            style_cmds.append(("RIGHTPADDING", (0, ri), (1, ri), 0))
            style_cmds.append(("TOPPADDING", (0, ri), (1, ri), 0))
            style_cmds.append(("BOTTOMPADDING", (0, ri), (1, ri), 0))
        table.setStyle(TableStyle(style_cmds))

        story = [head, Spacer(1, 3 * mm), table]
        doc.build(story)
        pdf_bytes = buf.getvalue()
    except Exception as exc:
        return False, f"PDF 绘制失败: {exc}"

    try:
        accessory_repo.soft_delete_yyd_attachments(order_id)
    except Exception:
        pass

    ok_flag, msg, _meta = save_order_attachment(
        data=pdf_bytes,
        orig_name=f"{order_no}预约单.pdf",
        content_type="application/pdf",
        acc_type=6,
        exp_of_id=order_id,
    )
    return (True, "ok") if ok_flag else (False, msg)

def auto_generate_appointment_after_online_pay(
    *, order_id: int, staff_user_id: str | int | None = None
) -> None:
    """对齐 Java BillController.saveBillData → geranateYyd：

    仅线上单(is_online=1)在写入收款单(type=2)后自动生成预约单；
    线下单须手动点「生成预约单」。
    """
    row = fetch_one(
        """
        SELECT id, order_type AS orderType, is_online AS isOnline,
               is_yyd AS isYyd, test_address_id AS testAddressId
        FROM experiment_order
        WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not row:
        return
    if str(row.get("orderType") or "") not in ("6", "8"):
        return
    try:
        is_online = int(row.get("isOnline") or 0)
    except (TypeError, ValueError):
        is_online = 0
    if is_online != 1:
        return
    try:
        is_yyd = int(row.get("isYyd") or 0)
    except (TypeError, ValueError):
        return
    if is_yyd != 0:
        return
    try:
        addr_id = int(row.get("testAddressId") or 0)
    except (TypeError, ValueError):
        addr_id = 0
    try:
        execute(
            "UPDATE experiment_order SET is_yyd = 1 WHERE id = %(id)s",
            {"id": order_id},
        )
    except Exception:
        return
    pdf_ok, pdf_msg = _build_appointment_pdf(order_id=order_id, test_address_id=addr_id)
    _write_order_log(
        order_id,
        "收款完成，自动生成预约单" + ("" if pdf_ok else f"（PDF:{pdf_msg}）"),
        user_id=staff_user_id,
    )


def try_finish_main_order(
    *, order_id: int, staff_user_id: str | int | None = None
) -> None:
    """对齐 Java QdBillServiceImpl.orderFinish：子单/收款/开票/成本结清后主单→49/50。"""
    row = get_order(order_id)
    if not row:
        return
    ot = str(row.get("orderType") or "")
    if ot not in ("6", "8"):
        return
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    if st in (0, 50):
        return

    # 产品行全部已完成(50)
    child_rows = fetch_all(
        """
        SELECT order_status AS orderStatus
        FROM experiment_order_child
        WHERE order_form_id = %(oid)s AND IFNULL(delete_status, 2) <> 1
        """,
        {"oid": order_id},
    ) or []
    if not child_rows:
        return
    for ch in child_rows:
        try:
            if int(ch.get("orderStatus") or 0) != 50:
                return
        except (TypeError, ValueError):
            return

    # 收款次数 = collection_time 槽位数
    coll = str(row.get("collectionTime") or "").strip()
    slots = [p for p in coll.split(",") if p.strip()] if coll else []
    recv_cnt = int(
        scalar(
            "SELECT COUNT(1) FROM qd_bill WHERE exp_of_id = %(oid)s AND type = 2",
            {"oid": order_id},
            0,
        )
        or 0
    )
    if slots and recv_cnt != len(slots):
        return

    # 线下需开票时：开票金额≥总价 或 开票次数≥槽位
    try:
        is_online = int(row.get("isOnline") or 0)
        inv_type = int(row.get("invoiceType") or 0)
        total_p = float(row.get("totalPrice") or 0)
        inv_amt = float(row.get("invoiceAmount") or 0)
        cost_settle = int(row.get("costSettle") or 0)
    except (TypeError, ValueError):
        is_online, inv_type, total_p, inv_amt, cost_settle = 0, 0, 0.0, 0.0, 0
    if is_online == 0 and inv_type == 1:
        if inv_amt < total_p:
            inv_cnt = int(
                scalar(
                    "SELECT COUNT(1) FROM qd_bill WHERE exp_of_id = %(oid)s AND type = 1",
                    {"oid": order_id},
                    0,
                )
                or 0
            )
            if not slots or inv_cnt < len(slots):
                return

    # 关联采购/实验子单须存在且全部已完成（Java：空列表则未完成）
    child_ot = "10" if ot == "6" else "9"
    subs = fetch_all(
        """
        SELECT order_status AS orderStatus
        FROM experiment_order
        WHERE parent_id = %(pid)s
          AND order_type = %(ot)s
          AND IFNULL(deleteStatus, 0) = 0
        """,
        {"pid": order_id, "ot": child_ot},
    ) or []
    if not subs:
        return
    for s in subs:
        try:
            if int(s.get("orderStatus") or 0) != 50:
                return
        except (TypeError, ValueError):
            return

    next_st = 50 if cost_settle == 1 else 49
    try:
        if next_st == 50:
            execute(
                """
                UPDATE experiment_order
                SET order_status = %(st)s, finishTime = NOW()
                WHERE id = %(id)s
                """,
                {"st": next_st, "id": order_id},
            )
        else:
            execute(
                "UPDATE experiment_order SET order_status = %(st)s WHERE id = %(id)s",
                {"st": next_st, "id": order_id},
            )
    except Exception:
        execute(
            "UPDATE experiment_order SET order_status = %(st)s WHERE id = %(id)s",
            {"st": next_st, "id": order_id},
        )
    _write_order_log(
        order_id,
        "订单已完成" if next_st == 50 else "订单待成本结清(49)",
        user_id=staff_user_id,
    )


def _parse_money(val: Any) -> float | None:
    """解析金额：兼容逗号/货币符号；无法解析返回 None。"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "undefined"):
        return None
    # 去掉常见货币符与千分位
    for ch in ("￥", "¥", "$", "元", ",", "，", " "):
        s = s.replace(ch, "")
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def update_order_basic(
    *,
    order_id: int,
    mark: str = "",
    ship_user: Any = None,
    ship_phone: Any = None,
    ship_address: Any = None,
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
    customer_id: Any = None,
    custom_user_id: Any = None,
    class_id: Any = None,
    test_address_id: Any = None,
    company_account_id: Any = None,
    is_video: Any = None,
    user_scale_info: Any = None,
    salecb_user_scale_info: Any = None,
    warehouse_user: Any = None,
    test_manager: Any = None,
    stock_company_id: Any = None,
    in_bill_type_id: Any = None,
    children: list[dict[str, Any]] | None = None,
    deleted_child_ids: list[Any] | None = None,
    check_child_ids: list[Any] | None = None,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """编辑订单主字段；对齐 Java：编辑后按原状态回退以便再次审核，日志追加不清空。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canEdit"):
        return False, "当前不可编辑"
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    ot = str(row.get("orderType") or "")
    # 子单审核通过后抬头字段只读，但仍回退状态以便再次提交审核
    header_locked = ot in ("9", "10") and st >= 30
    sets = []
    params: dict[str, Any] = {"id": order_id}
    if mark is not None:
        sets.append("mark = %(mark)s")
        sets.append("msg = %(mark)s")
        params["mark"] = mark[:1000]
    # ship_* / 回收地址：仅调用方显式传入时才更新（None=不改），避免子单编辑误清空
    if ship_user is not None:
        sets.append("addressee_name = %(ship_user)s")
        params["ship_user"] = str(ship_user)[:100]
    if ship_phone is not None:
        sets.append("addressee_mobile = %(ship_phone)s")
        params["ship_phone"] = str(ship_phone)[:50]
    if ship_address is not None:
        sets.append("send_address = %(ship_address)s")
        params["ship_address"] = str(ship_address)[:500]
    if delivery_time is not None and str(delivery_time).strip():
        sets.append("delivery_time = %(delivery_time)s")
        params["delivery_time"] = str(delivery_time).strip()[:19]
    if order_time is not None and str(order_time).strip():
        sets.append("order_time = %(order_time)s")
        params["order_time"] = str(order_time).strip()[:19]
    if collection_time is not None and str(collection_time).strip():
        sets.append("collection_time = %(collection_time)s")
        params["collection_time"] = str(collection_time).strip()[:200]
    # 订单总价：显式传入时必须写入（含 0）；解析失败直接报错，避免静默跳过
    parsed_total: float | None = None
    total_price_provided = total_price is not None and str(total_price).strip() != ""
    if total_price_provided:
        parsed_total = _parse_money(total_price)
        if parsed_total is None:
            return False, "订单总价格式不正确"
        params["tp"] = round(float(parsed_total), 2)
        sets.append("`totalPrice` = %(tp)s")
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
        sets.append("`invoiceType` = %(invoice_type)s")
    if reverso_context not in (None, ""):
        # 对齐 Java：1=回收 2=不回收（勿再写 ON/OFF 字符串）
        rev = str(reverso_context).strip().upper()
        params["reverso_context"] = 1 if rev in ("1", "ON", "TRUE", "YES") else 2
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
    # 对齐 Java：sale_user / sale_manager 为字符串员工 ID（UUID 或带前导零），禁止 int() 静默丢弃
    if sale_manager not in (None, ""):
        params["sale_manager"] = str(sale_manager).strip()[:64]
        sets.append("sale_manager = %(sale_manager)s")
    if sale_user not in (None, ""):
        params["sale_user"] = str(sale_user).strip()[:64]
        sets.append("sale_user = %(sale_user)s")
    # 客户名称 / 客户账号：前端 clearable 会传空串或 null；显式传入时允许清空（None=不改）
    for key, col in (
        ("customer_id", "customer_name"),
        ("custom_user_id", "custom_user_id"),
    ):
        val = locals().get(key)
        if val is None:
            continue
        if val in ("", 0, "0"):
            params[key] = None
            sets.append(f"{col} = %({key})s")
            continue
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
    if user_scale_info is not None:
        scale = str(user_scale_info or "").strip()[:500]
        params["user_scale_info"] = scale
        sets.append("user_scale_info = %(user_scale_info)s")
        sets.append("scale_info = %(user_scale_info)s")
    if salecb_user_scale_info is not None:
        params["salecb_user_scale_info"] = str(salecb_user_scale_info or "").strip()[:255]
        sets.append("salecb_user_scale_info = %(salecb_user_scale_info)s")
    if warehouse_user not in (None, ""):
        params["warehouse_user"] = str(warehouse_user).strip()[:64]
        sets.append("warehouse_user = %(warehouse_user)s")
    # type=9 分包子单：实验室测试主管（审核权限落在 test_manager）
    if test_manager not in (None, ""):
        params["test_manager"] = str(test_manager).strip()[:64]
        sets.append("test_manager = %(test_manager)s")
    if stock_company_id not in (None, ""):
        try:
            params["stock_company_id"] = int(stock_company_id)
            sets.append("stock_company_name = %(stock_company_id)s")
        except (TypeError, ValueError):
            pass
    if in_bill_type_id not in (None, ""):
        try:
            params["in_bill_type_id"] = int(in_bill_type_id)
            sets.append("in_bill_type_id = %(in_bill_type_id)s")
        except (TypeError, ValueError):
            pass
    # 对齐 Java：type=6 editSave status==10→5 / 66→67 / >=30→20；
    # type=9/10 非草稿编辑一律回退到 5，便于再次提交审核（抬头字段仍可只读）
    next_st = None
    if ot in ("9", "10"):
        if st not in (0, 5):
            next_st = 5
    elif st == 10:
        next_st = 5
    elif st == 66:
        next_st = 67
    elif st >= 30:
        next_st = 20
    if header_locked:
        # 审核通过子单：抬头锁定，仅备注可改；
        # 分包子单(type=9)总价=产品成本合计，产品行可改则总价仍允许回写
        if str(ot).strip() == "9":
            sets = [
                s
                for s in sets
                if s.startswith("mark =")
                or s.startswith("msg =")
                or s.startswith("`totalPrice` =")
            ]
        else:
            sets = [s for s in sets if s.startswith("mark =") or s.startswith("msg =")]
            parsed_total = None
    if next_st is not None:
        sets.append("order_status = %(next_st)s")
        params["next_st"] = next_st
    if not sets and children is None and not deleted_child_ids:
        return False, "无变更"
    # mark/msg 可能重复；去重保留顺序
    if sets:
        uniq: list[str] = []
        for s in sets:
            if s not in uniq:
                uniq.append(s)
        execute(
            f"UPDATE experiment_order SET {', '.join(uniq)} WHERE id = %(id)s",
            params,
        )
    # type=9/10 重新进入审核：子行回到待样品到货(2)，避免沿用旧样品流程按钮
    if ot in ("9", "10") and next_st == 5:
        try:
            execute(
                """
                UPDATE experiment_order_child c
                JOIN exp_qd_purchase_order_child poc ON poc.order_child_id = c.id
                SET c.order_status = 2,
                    c.is_confirm = 0,
                    c.is_meeting = 0,
                    c.meeting_num = NULL
                WHERE poc.purchase_order_id = %(oid)s
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND IFNULL(c.order_status, 0) > 0
                """,
                {"oid": order_id},
            )
        except Exception:
            pass
        try:
            execute(
                """
                UPDATE experiment_order_child
                SET order_status = 2, is_confirm = 0, is_meeting = 0, meeting_num = NULL
                WHERE order_form_id = %(oid)s
                  AND IFNULL(delete_status, 2) <> 1
                  AND IFNULL(order_status, 0) > 0
                """,
                {"oid": order_id},
            )
        except Exception:
            pass
        # 作废旧出库仓位关联，避免详情子行 JOIN 重复、样品按钮错乱
        try:
            execute(
                """
                UPDATE exp_goods_out_treasury_child gotc
                JOIN experiment_order_child c ON gotc.order_child_id = c.id
                LEFT JOIN exp_qd_purchase_order_child poc ON poc.order_child_id = c.id
                SET gotc.store_id = NULL,
                    gotc.store_position_id = NULL,
                    gotc.got_status = 3
                WHERE (c.order_form_id = %(oid)s OR poc.purchase_order_id = %(oid)s)
                  AND IFNULL(gotc.got_status, 0) NOT IN (3, 5)
                """,
                {"oid": order_id},
            )
        except Exception:
            pass
    # 同步产品行（对齐 Java editSave）：更新已有 / 新增 / 软删未提交行
    if children is not None:
        ot = str(row.get("orderType") or "")
        keep_ids: set[int] = set()
        pending_updates: list[dict[str, Any]] = []

        def _as_child_id(ch: dict[str, Any]) -> int | None:
            raw = ch.get("id") or ch.get("childId")
            try:
                return int(raw)
            except (TypeError, ValueError):
                return None

        for ch in children:
            if not isinstance(ch, dict):
                continue
            if ch.get("_deleted") in (True, 1, "1"):
                continue
            cid = ch.get("id") or ch.get("childId")
            # 新增行（无 id）
            if cid in (None, "", 0, "0"):
                if ot not in ("6", "8"):
                    continue
                try:
                    new_cid = _insert_edit_child_line(
                        order_id=order_id, ch=ch, order_no=str(row.get("orderId") or "")
                    )
                    if new_cid:
                        keep_ids.add(int(new_cid))
                except Exception as exc:
                    logger.exception("insert edit child failed order=%s", order_id)
                    return False, f"新增产品行失败：{exc}"
                continue
            try:
                cid_i = int(cid)
            except (TypeError, ValueError):
                continue
            keep_ids.add(cid_i)
            pending_updates.append(ch)

        # 对齐 Java checkChilds：显式勾选列表优先于 children（防止前端回退成全部已挂接行）
        if check_child_ids is not None:
            parsed_check: set[int] = set()
            for x in check_child_ids:
                try:
                    parsed_check.add(int(x))
                except (TypeError, ValueError):
                    continue
            keep_ids = parsed_check
            pending_updates = [
                ch
                for ch in pending_updates
                if _as_child_id(ch) in keep_ids
            ]

        # type9/10：先按勾选同步挂接（对齐 Java checkChilds / updatePurchaseOrder）
        parent_pk = row.get("parentPkId") or row.get("parentId")
        try:
            parent_id = int(parent_pk) if parent_pk not in (None, "", 0, "0") else 0
        except (TypeError, ValueError):
            parent_id = 0
        if str(ot).strip() in ("9", "10"):
            ok_sync, sync_msg = _sync_sub_order_purchase_children(
                order_id=order_id, order_type=ot, keep_ids=keep_ids
            )
            if not ok_sync:
                return False, sync_msg

        for ch in pending_updates:
            cid = ch.get("id") or ch.get("childId")
            try:
                cid_i = int(cid)
            except (TypeError, ValueError):
                continue
            child_sets: list[str] = []
            child_params: dict[str, Any] = {
                "id": cid_i,
                "oid": order_id,
                "pid": parent_id or order_id,
            }
            if ch.get("goodsNums") is not None or ch.get("goods_nums") is not None:
                try:
                    child_params["nums"] = int(
                        ch.get("goodsNums") if ch.get("goodsNums") is not None else ch.get("goods_nums")
                    )
                    child_sets.append("goods_nums = %(nums)s")
                except (TypeError, ValueError):
                    pass
            price_raw = ch.get("goodsPrice") if ch.get("goodsPrice") is not None else ch.get("goods_price")
            if price_raw not in (None, ""):
                try:
                    child_params["price"] = float(price_raw)
                    child_sets.append("goods_price = %(price)s")
                except (TypeError, ValueError):
                    pass
            ref_raw = (
                ch.get("referencePrice")
                if ch.get("referencePrice") is not None
                else ch.get("reference_price")
            )
            if ref_raw not in (None, ""):
                try:
                    child_params["ref"] = float(ref_raw)
                    child_sets.append("reference_price = %(ref)s")
                except (TypeError, ValueError):
                    pass
            spec_raw = ch.get("goodsSpec") if ch.get("goodsSpec") is not None else ch.get("goods_spec")
            if spec_raw is not None:
                child_params["spec"] = str(spec_raw)[:200]
                child_sets.append("goods_spec = %(spec)s")
            cost_raw = ch.get("costPrice") if ch.get("costPrice") is not None else ch.get("cost_price")
            if cost_raw not in (None, ""):
                try:
                    child_params["cost"] = float(cost_raw)
                    child_sets.append("cost_price = %(cost)s")
                except (TypeError, ValueError):
                    pass
            # 实验子单：可改测试人员 / 实验平台 / 预计完成时间（对齐 Java updateExpSubOrder）
            tu = ch.get("testUserId") if "testUserId" in ch else ch.get("test_user_id")
            if tu not in (None,):
                child_params["tu"] = str(tu).strip()[:64] or None
                child_sets.append("test_user_id = %(tu)s")
            lid = ch.get("lineId") if "lineId" in ch else ch.get("line_id")
            if lid not in (None,):
                raw_lid = str(lid).strip()
                if raw_lid in ("", "null", "undefined"):
                    child_params["lid"] = None
                    child_sets.append("line_id = %(lid)s")
                else:
                    try:
                        # 兼容 "123" / 123 / "123.0"
                        child_params["lid"] = int(float(raw_lid))
                        child_sets.append("line_id = %(lid)s")
                    except (TypeError, ValueError):
                        pass
            ft = (
                ch.get("expectFinishTime")
                if "expectFinishTime" in ch
                else None
            )
            if ft is None and "expect_finishtime" in ch:
                ft = ch.get("expect_finishtime")
            if ft is None:
                ft = ch.get("finishTime") or ch.get("_finishTime")
            if ft not in (None, ""):
                # 兼容 ISO：2026-08-14T18:00:00.000Z → 本地展示用的前 19 位
                ft_s = str(ft).strip().replace("T", " ")
                if ft_s.endswith("Z"):
                    ft_s = ft_s[:-1]
                child_params["ft"] = ft_s[:19]
                child_sets.append("expect_finishtime = %(ft)s")
            # 主单编辑可选商品/项目字段回写
            for src, col, key in (
                ("goodsId", "goods_id", "gid"),
                ("goods_id", "goods_id", "gid"),
                ("goodsName", "goods_name", "gn"),
                ("goods_name", "goods_name", "gn"),
                ("goodsBrandId", "goods_brand_id", "gbid"),
                ("goodsBrandName", "goods_brand_name", "gbn"),
                ("projectId", "experiment_project_id", "epid"),
                ("projectName", "experiment_project_name", "epn"),
                ("classId", "experiment_class_id", "ecid"),
                ("className", "experiment_class_name", "ecn"),
            ):
                if src not in ch or ch.get(src) in (None, ""):
                    continue
                val = ch.get(src)
                if col.endswith("_id"):
                    try:
                        child_params[key] = int(val)
                        child_sets.append(f"{col} = %({key})s")
                    except (TypeError, ValueError):
                        child_params[key] = str(val)[:64]
                        child_sets.append(f"{col} = %({key})s")
                else:
                    child_params[key] = str(val)[:200]
                    child_sets.append(f"{col} = %({key})s")
            if child_sets:
                # 子单产品行挂在主单 order_form_id 上；同步挂接后按 id 更新
                affected = execute(
                    f"""
                    UPDATE experiment_order_child
                    SET {', '.join(child_sets)}
                    WHERE id = %(id)s
                      AND IFNULL(delete_status, 2) <> 1
                      AND (
                        order_form_id = %(oid)s
                        OR order_form_id = %(pid)s
                        OR EXISTS (
                          SELECT 1 FROM exp_qd_purchase_order_child poc
                          WHERE poc.order_child_id = %(id)s
                            AND poc.purchase_order_id = %(oid)s
                        )
                      )
                    """,
                    child_params,
                )
                # 个别历史数据 order_form_id / 挂接不一致时，sync 已确认归属则按 id 兜底写入
                if int(affected or 0) <= 0 and str(ot).strip() in ("9", "10") and cid_i in keep_ids:
                    execute(
                        f"""
                        UPDATE experiment_order_child
                        SET {', '.join(child_sets)}
                        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
                        """,
                        child_params,
                    )
        # 主单编辑：软删本次未提交的原产品行（对齐 Java editSaveSaleOrdersExp）
        # 同时查 order_form_id / 采购关联，避免新增行关联方式不一致导致漏删
        if str(ot).strip() in ("6", "8"):
            existing = fetch_all(
                """
                SELECT c.id
                FROM experiment_order_child c
                WHERE IFNULL(c.delete_status, 2) <> 1
                  AND (
                    c.order_form_id = %(oid)s
                    OR EXISTS (
                      SELECT 1 FROM exp_qd_purchase_order_child poc
                      WHERE poc.order_child_id = c.id
                        AND poc.purchase_order_id = %(oid)s
                    )
                  )
                """,
                {"oid": order_id},
            )
            removed = 0
            for er in existing or []:
                try:
                    eid = int(er["id"])
                except (TypeError, ValueError, KeyError):
                    continue
                if eid in keep_ids:
                    continue
                n = execute(
                    """
                    UPDATE experiment_order_child
                    SET delete_status = 1
                    WHERE id = %(id)s
                    """,
                    {"id": eid},
                )
                removed += int(n or 0)
            if removed:
                logger.info(
                    "edit soft-delete children order=%s removed=%s keep=%s",
                    order_id,
                    removed,
                    sorted(keep_ids),
                )
    # 前端显式传入的删除行（兼容 keep_ids 漏删；含新增后未刷新仍带旧 id 的场景）
    # 子单(type9/10)产品行属主单：禁止软删，挂接变更已由 checkChilds 同步完成
    if str(row.get("orderType") or "").strip() not in ("9", "10"):
        for raw_id in deleted_child_ids or []:
            try:
                did = int(raw_id)
            except (TypeError, ValueError):
                continue
            if did <= 0:
                continue
            execute(
                """
                UPDATE experiment_order_child
                SET delete_status = 1
                WHERE id = %(id)s
                  AND (
                    order_form_id = %(oid)s
                    OR EXISTS (
                      SELECT 1 FROM exp_qd_purchase_order_child poc
                      WHERE poc.order_child_id = %(id)s
                        AND poc.purchase_order_id = %(oid)s
                    )
                  )
                """,
                {"id": did, "oid": order_id},
            )
    # 产品行变更后再次回写总价，避免历史逻辑/触发器把总价冲掉
    # 分包子单审核后抬头锁定，但仍需随成本行回写总价
    if parsed_total is not None and (not header_locked or str(ot).strip() == "9"):
        execute(
            """
            UPDATE experiment_order
            SET `totalPrice` = %(tp)s
            WHERE id = %(id)s
            """,
            {"tp": round(float(parsed_total), 2), "id": order_id},
        )
    _write_order_log(order_id, "编辑订单", user_id=staff_user_id)
    return True, "保存成功"


def _insert_edit_child_line(*, order_id: int, ch: dict[str, Any], order_no: str) -> int:
    """主单编辑新增产品行；对齐创建订单 insert，失败抛错由上层返回。"""
    # 含已软删行计数，避免 order_id 子单号与历史行冲突导致插入失败却静默成功
    cnt = int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order_child
            WHERE order_form_id = %(oid)s
            """,
            {"oid": order_id},
            0,
        )
        or 0
    )
    base_no = order_no or str(order_id)
    child_no = f"{base_no}-{cnt + 1}"
    # 若仍冲突则顺延
    for _ in range(20):
        hit = fetch_one(
            """
            SELECT id FROM experiment_order_child
            WHERE order_id = %(cno)s LIMIT 1
            """,
            {"cno": child_no},
        )
        if not hit:
            break
        cnt += 1
        child_no = f"{base_no}-{cnt + 1}"
    goods_id = ch.get("goodsId") or ch.get("goods_id") or ""
    goods_name = str(ch.get("goodsName") or ch.get("goods_name") or "")[:200]
    goods_spec = str(ch.get("goodsSpec") or ch.get("goods_spec") or "")[:200]
    goods_brand_id = ch.get("goodsBrandId") or ch.get("goods_brand_id") or ""
    goods_brand_name = str(
        ch.get("goodsBrandName") or ch.get("goods_brand_name") or ch.get("goodsBrand") or ""
    )[:100]
    try:
        goods_nums = float(ch.get("goodsNums") or ch.get("goods_nums") or 1)
    except (TypeError, ValueError):
        goods_nums = 1.0
    try:
        goods_price = float(ch.get("goodsPrice") or ch.get("goods_price") or 0)
    except (TypeError, ValueError):
        goods_price = 0.0
    try:
        reference_price = float(
            ch.get("referencePrice") or ch.get("reference_price") or goods_price or 0
        )
    except (TypeError, ValueError):
        reference_price = goods_price
    project_id = ch.get("projectId") or ch.get("experiment_project_id") or ""
    project_name = str(ch.get("projectName") or ch.get("experiment_project_name") or "")[:200]
    class_id = ch.get("classId") or ch.get("experiment_class_id") or ""
    class_name = str(ch.get("className") or ch.get("experiment_class_name") or "")[:200]
    try:
        currency_type = int(ch.get("currencyType") or ch.get("currency_type") or 1)
    except (TypeError, ValueError):
        currency_type = 1
    params = {
        "oid": order_id,
        "cno": child_no[:80],
        "gid": int(goods_id) if str(goods_id).isdigit() else None,
        "gn": goods_name,
        "gs": goods_spec,
        "gbid": int(goods_brand_id) if str(goods_brand_id).isdigit() else None,
        "gb": goods_brand_name,
        "nums": goods_nums,
        "price": goods_price,
        "ref": reference_price,
        "epid": int(project_id) if str(project_id).isdigit() else None,
        "epn": project_name,
        "ecid": int(class_id) if str(class_id).isdigit() else None,
        "ecn": class_name,
        "ct": currency_type,
    }
    # 与创建订单一致：order_status=1 / op_status=1 / delete_status=2
    child_pk = 0
    try:
        child_pk = execute_insert(
            """
            INSERT INTO experiment_order_child
                (add_time, delete_status, order_form_id, order_id, order_status, op_status,
                 goods_id, goods_name, goods_spec, goods_brand_id, goods_brand_name,
                 goods_nums, goods_price, reference_price,
                 experiment_project_id, experiment_project_name,
                 experiment_class_id, experiment_class_name,
                 in_status, fcsq, is_meeting, currency_type)
            VALUES
                (NOW(), 2, %(oid)s, %(cno)s, 1, 1,
                 %(gid)s, %(gn)s, %(gs)s, %(gbid)s, %(gb)s,
                 %(nums)s, %(price)s, %(ref)s,
                 %(epid)s, %(epn)s, %(ecid)s, %(ecn)s,
                 0, 0, 0, %(ct)s)
            """,
            params,
        )
    except Exception:
        child_pk = execute_insert(
            """
            INSERT INTO experiment_order_child
                (add_time, delete_status, order_form_id, order_id, order_status, op_status,
                 goods_id, goods_name, goods_spec, goods_brand_name,
                 goods_nums, goods_price, reference_price,
                 experiment_project_id, experiment_project_name,
                 experiment_class_id, experiment_class_name,
                 currency_type)
            VALUES
                (NOW(), 2, %(oid)s, %(cno)s, 1, 1,
                 %(gid)s, %(gn)s, %(gs)s, %(gb)s,
                 %(nums)s, %(price)s, %(ref)s,
                 %(epid)s, %(epn)s, %(ecid)s, %(ecn)s,
                 %(ct)s)
            """,
            params,
        )
    if not child_pk:
        raise RuntimeError("产品明细写入未返回主键")
    return int(child_pk)


def confirm_ordered(
    *, order_id: int, staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    """对齐 Java addOrderData / saveXdData：status 30 → 35 确认已下单。"""
    row = get_order(order_id)
    if not row:
        return False, "订单不存在"
    if not row.get("canConfirmOrdered"):
        return False, "当前不可确认已下单"
    _set_order_status(order_id, 35)
    _write_order_log(order_id, "确认已下单", user_id=staff_user_id)
    return True, "已确认下单"


def update_sub_order_status(
    *,
    order_id: int,
    order_status: int,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
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
        _write_order_log(order_id, "厂家已发货", user_id=staff_user_id)
        return True, "发货成功"
    return False, "不支持的状态变更"


def update_sub_pay(
    *,
    order_id: int,
    pay_type: str | int,
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
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
        _write_order_log(order_id, log_txt, user_id=staff_user_id)
        try:
            from apps.admin_experiment.services.wx_suborder_notify import notify_pay_flow

            notify_pay_flow(
                order_id=order_id, pay_type="1", staff_user_id=staff_user_id
            )
        except Exception:
            pass
        return True, "已提交付款申请"
    if t == "2":
        apply_pay_audit_permission(row, staff_user_id)
        if not row.get("canAuditPay"):
            return False, "无付款审核权限（需本单销售主管）"
        execute(
            "UPDATE experiment_order SET pay_status = 34 WHERE id = %(id)s",
            {"id": order_id},
        )
        _write_order_log(order_id, "申请付款审核通过", user_id=staff_user_id)
        try:
            from apps.admin_experiment.services.wx_suborder_notify import notify_pay_flow

            notify_pay_flow(
                order_id=order_id, pay_type="2", staff_user_id=staff_user_id
            )
        except Exception:
            pass
        return True, "付款申请已通过"
    if t == "3":
        apply_pay_audit_permission(row, staff_user_id)
        if not row.get("canAuditPay"):
            return False, "无付款审核权限（需本单销售主管）"
        execute(
            "UPDATE experiment_order SET pay_status = 33 WHERE id = %(id)s",
            {"id": order_id},
        )
        _write_order_log(order_id, "申请付款驳回", user_id=staff_user_id)
        try:
            from apps.admin_experiment.services.wx_suborder_notify import notify_pay_flow

            notify_pay_flow(
                order_id=order_id, pay_type="3", staff_user_id=staff_user_id
            )
        except Exception:
            pass
        return True, "付款申请已驳回"
    return False, "无法处理此类别"


def upload_sub_pay_bill(
    *,
    order_id: int,
    money: Any,
    staff_user_id: str = "",
    log_info: str = "上传付款信息",
    accessory_id: int | str | None = None,
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
    try:
        acc_id = int(accessory_id) if accessory_id not in (None, "") else None
    except (TypeError, ValueError):
        acc_id = None
    if acc_id is not None and acc_id <= 0:
        acc_id = None
    params = {
        "oid": order_id,
        "money": amt,
        "log_info": (log_info or "上传付款信息")[:500],
        "uid": staff_user_id or None,
        "aid": acc_id,
    }
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark{acc_col})
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 2, 0, NOW(), %(log_info)s{acc_val})
        """.format(
            acc_col=", accessory_id" if acc_id else "",
            acc_val=", %(aid)s" if acc_id else "",
        ),
        params,
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
    _write_order_log(order_id, f"上传付款信息 {amt}", user_id=staff_user_id)
    # 对齐 Java：采购单付完后回写父单利润差；若主单尚未首分也在此补分
    try:
        from apps.admin_experiment.services.split_money import (
            try_split_type8_parent_from_child,
        )

        try_split_type8_parent_from_child(order_id)
    except Exception:
        pass
    return True, "上传付款成功"


def upload_sub_invoice_bill(
    *,
    order_id: int,
    money: Any,
    staff_user_id: str = "",
    log_info: str = "上传发票信息",
    accessory_id: int | str | None = None,
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
    try:
        acc_id = int(accessory_id) if accessory_id not in (None, "") else None
    except (TypeError, ValueError):
        acc_id = None
    if acc_id is not None and acc_id <= 0:
        acc_id = None
    params = {
        "oid": order_id,
        "money": amt,
        "log_info": (log_info or "上传发票信息")[:500],
        "uid": staff_user_id or None,
        "aid": acc_id,
    }
    execute(
        """
        INSERT INTO qd_bill
            (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark{acc_col})
        VALUES
            (NOW(), %(uid)s, %(oid)s, %(money)s, 1, 0, NOW(), %(log_info)s{acc_val})
        """.format(
            acc_col=", accessory_id" if acc_id else "",
            acc_val=", %(aid)s" if acc_id else "",
        ),
        params,
    )
    _write_order_log(order_id, f"上传发票信息 {amt}", user_id=staff_user_id)
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
            SELECT c.id FROM experiment_order_child c
            WHERE c.order_form_id = %(oid)s
              AND IFNULL(c.delete_status, 2) <> 1
              AND IFNULL(c.op_status, 0) = 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM exp_qd_purchase_order_child p
                  INNER JOIN experiment_order o ON o.id = p.purchase_order_id
                  WHERE p.order_child_id = c.id
                    AND IFNULL(o.deleteStatus, 0) = 0
                    AND IFNULL(o.order_status, -1) <> 0
              )
            ORDER BY c.id
            """,
            {"oid": parent_id},
        )
        ids = [int(r["id"]) for r in rows if r.get("id") is not None]
    if not ids:
        return False, "没有可挂接的产品行", None

    # 仅允许主单下待处理且未挂接有效子单的产品行（防重复创建）
    valid_rows = fetch_all(
        """
        SELECT c.id FROM experiment_order_child c
        WHERE c.order_form_id = %(oid)s
          AND IFNULL(c.delete_status, 2) <> 1
          AND IFNULL(c.op_status, 0) = 1
          AND NOT EXISTS (
              SELECT 1
              FROM exp_qd_purchase_order_child p
              INNER JOIN experiment_order o ON o.id = p.purchase_order_id
              WHERE p.order_child_id = c.id
                AND IFNULL(o.deleteStatus, 0) = 0
                AND IFNULL(o.order_status, -1) <> 0
          )
        """,
        {"oid": parent_id},
    )
    valid_ids = {int(r["id"]) for r in (valid_rows or []) if r.get("id") is not None}
    ids = [cid for cid in ids if cid in valid_ids]
    if not ids:
        return False, "所选产品行已创建过子订单或不可用，请刷新后重选", None

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

    # 对齐 Java：实验子单 C + orderIdGeranateSale；分包子单 S + 同规则
    # （历史正确例：HYYPT… → CHYYPT… / SHYYPT…；勿用 parent-Z时分秒）
    id_prefix = "C" if child_ot == "10" else "S"
    order_time = str(
        form.get("orderTime") or form.get("order_time") or parent.get("orderTime") or ""
    ).strip()
    if not order_time:
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_no = _generate_exp_order_no(
        order_time=order_time,
        class_id=parent.get("classId"),
        supplier_id=parent.get("supplierId"),
        id_prefix=id_prefix,
    )
    # 分包/实验子单创建后均为未提交审核（status=5），提交审核走独立入口
    init_status = 5
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
        invoice_type = int(form.get("invoiceType") if form.get("invoiceType") is not None else 2)
    except (TypeError, ValueError):
        invoice_type = 2
    in_bill_type_id = str(form.get("inBillTypeId") or form.get("in_bill_type_id") or "").strip()
    taxes = str(form.get("taxes") or "").strip()
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
                 currency_type, invoiceType, is_confirm, cost_settle, add_user_id, pay_status)
            SELECT
                NOW(), 0, %(ono)s, %(ot)s, %(st)s, id,
                %(tp)s,
                COALESCE(NULLIF(%(sm)s, ''), sale_manager),
                sale_user, customer_name, supplier_name,
                %(ct)s, %(inv)s, 0, 0, NULLIF(%(au)s, ''), 0
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
                 currency_type, invoiceType, is_confirm, cost_settle, pay_status)
            SELECT
                NOW(), 0, %(ono)s, %(ot)s, %(st)s, id,
                %(tp)s,
                COALESCE(NULLIF(%(sm)s, ''), sale_manager),
                sale_user, customer_name, supplier_name,
                %(ct)s, %(inv)s, 0, 0, 0
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
                    msg = NULLIF(%(mk)s, '')
                WHERE id = %(id)s
                """,
                {
                    "id": new_id,
                    "tm": test_manager or None,
                    "scn": stock_company or None,
                    "ibt": int(in_bill_type_id) if in_bill_type_id.isdigit() else None,
                    "otm": order_time[:19] if order_time else "",
                    "dt": delivery_time[:19] if delivery_time else "",
                    "pw": int(pay_way) if pay_way.isdigit() else None,
                    "tx": taxes or None,
                    "ctm": collection_time[:500] if collection_time else None,
                    "mk": msg[:1000] if msg else None,
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
                        msg = NULLIF(%(mk)s, '')
                    WHERE id = %(id)s
                    """,
                    {
                        "id": new_id,
                        "scn": stock_company or None,
                        "otm": order_time[:19] if order_time else "",
                        "dt": delivery_time[:19] if delivery_time else "",
                        "mk": msg[:1000] if msg else None,
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
                    "mk": msg[:1000] if msg else None,
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
                        msg = NULLIF(%(mk)s, '')
                    WHERE id = %(id)s
                    """,
                    {
                        "id": new_id,
                        "sm": sale_manager or "",
                        "su": sale_user or "",
                        "otm": order_time[:19] if order_time else "",
                        "dt": delivery_time[:19] if delivery_time else "",
                        "mk": msg[:1000] if msg else None,
                    },
                )
            except Exception:
                pass
        # 订单资料：创建前上传 / 复制源单的 accessory id 列表
        orderdata = form.get("orderdata") or form.get("orderData") or form.get("fileIds") or ""
        file_ids = _as_str_list(orderdata)
        raw_acc = form.get("accessoryId") or form.get("accessoryIds")
        if isinstance(raw_acc, (list, tuple)):
            file_ids = [str(x) for x in raw_acc] + file_ids
        _attach_accessories_to_order(int(new_id), file_ids)

    # 把产品行挂到新子单（采购关联表；order_type 对齐 Java getChildsByPurchaseId2）
    for i, cid in enumerate(ids):
        _link_exp_purchase_child(
            purchase_order_id=int(new_id),
            order_child_id=int(cid),
            order_type=child_ot,
        )
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
                        pcost_price = COALESCE(NULLIF(%(cp)s, ''), pcost_price),
                        expect_finishtime = COALESCE(NULLIF(%(ft)s, ''), expect_finishtime),
                        line_id = COALESCE(NULLIF(%(lid)s, ''), line_id),
                        op_status = 2,
                        order_status = CASE
                            WHEN IFNULL(order_status, 0) < 2 THEN 2
                            ELSE order_status
                        END
                    WHERE id = %(cid)s
                    """,
                    {
                        "tu": tu,
                        "cp": cp,
                        "ft": ft[:19] if ft else "",
                        "lid": lid if str(lid).isdigit() else "",
                        "cid": cid,
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
                    WHERE id = %(cid)s
                    """,
                    {"cid": cid},
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
                WHERE id = %(cid)s
                """,
                {"cid": cid},
            )
    # 再兜底回填本单关联行 order_type，防止静默插入失败导致 Java 看不到产品
    repair_exp_purchase_child_order_types(int(new_id))
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


def _generate_exp_order_no(
    *, order_time: str, class_id: Any, supplier_id: Any, id_prefix: str = ""
) -> str:
    """对齐 Java orderIdGeranateSale：{C|S?}{company_code}PT{en1}{en2}{en3}{yyyyMM}{5位序号}。

    id_prefix：实验子单 'C'、分包子单 'S'；主单为空。
    """
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
    prefix = f"{id_prefix or ''}{com_code}PT{en1}{en2}{en3}{datestr}"
    latest = fetch_one(
        """
        SELECT order_id FROM experiment_order
        WHERE order_id LIKE %(pfx)s
          AND LOCATE('-', order_id) = 0
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
    创建实验主单（order_type=6）或实验分包主单（order_type=8），
    对齐 Java submitExpOrder / saveExpOrders。
    成功返回 (True, 新订单数字 id 字符串, id)。
    """
    header = header or {}
    children = [c for c in (children or []) if isinstance(c, dict)]
    raw_ot = str(_pick(header, "order_type", "orderType", default="6") or "6").strip()
    order_type = raw_ot if raw_ot in ("6", "8") else "6"
    customer_name = str(
        _pick(header, "customer_name", "customerName", "customerId", default="")
    ).strip()
    custom_user_id = str(
        _pick(header, "custom_user_id", "customUserId", "customerAccount", default="")
    ).strip()
    if not customer_name and not custom_user_id:
        return False, "提交订单失败,客户名称和客户账号不能同时为空!", None
    if not children:
        label = "实验分包订单" if order_type == "8" else "实验订单"
        return False, f"{label}至少选择一个产品才可提交!", None

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
    try:
        is_online = int(_pick(header, "is_online", "isOnline", default=0) or 0)
    except (TypeError, ValueError):
        is_online = 0
    if is_online not in (0, 1):
        is_online = 0
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
    # 预计收款时间：前端多期数组或逗号串（对齐 Java collection_time）
    coll_raw = _pick(header, "collection_time", "collectionTime", default="")
    if isinstance(coll_raw, (list, tuple)):
        collection_time = ",".join(str(x).strip() for x in coll_raw if str(x).strip())
    else:
        collection_time = str(coll_raw or "").strip()
    user_scale_info = str(
        _pick(header, "user_scale_info", "userScaleInfo", default="")
    ).strip()
    salecb_user_scale_info = str(
        _pick(header, "salecb_user_scale_info", "salecbUserScaleInfo", default="")
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
    # 客户公司电话：库列为 contract_phone（勿用 camelCase contractPhone）
    if customer_name and str(customer_name).isdigit():
        try:
            crow = fetch_one(
                "SELECT contract_phone AS contractPhone FROM qd_user_company WHERE id = %(id)s LIMIT 1",
                {"id": int(customer_name)},
            )
            if crow and crow.get("contractPhone"):
                mobile = str(crow["contractPhone"])
        except Exception:
            try:
                crow = fetch_one(
                    "SELECT contractPhone FROM qd_user_company WHERE id = %(id)s LIMIT 1",
                    {"id": int(customer_name)},
                )
                if crow and crow.get("contractPhone"):
                    mobile = str(crow["contractPhone"])
            except Exception:
                pass
    if custom_user_id and str(custom_user_id).isdigit():
        try:
            urow = fetch_one(
                "SELECT mobile FROM exp_user WHERE id = %(id)s LIMIT 1",
                {"id": int(custom_user_id)},
            )
            if not urow or not urow.get("mobile"):
                urow = fetch_one(
                    "SELECT mobile FROM `user` WHERE id = %(id)s LIMIT 1",
                    {"id": int(custom_user_id)},
                )
            if urow and urow.get("mobile"):
                mobile = str(urow["mobile"])
        except Exception:
            pass

    params = {
        "ono": order_no[:80],
        "ot": order_type,
        "st": 5,
        "mobile": mobile[:50] if mobile else None,
        "rev": reverso_context,
        "addr": send_address[:500] if send_address else None,
        "an": addressee_name[:100] if addressee_name else None,
        "am": addressee_mobile[:50] if addressee_mobile else None,
        "inv": invoice_type,
        "msg": msg[:1000] if msg else None,
        "mark": None,
        "otm": order_time[:19],
        "sm": sale_manager or None,
        "su": sale_user or None,
        "cuid": int(custom_user_id) if str(custom_user_id).isdigit() else None,
        "cust": int(customer_name) if str(customer_name).isdigit() else None,
        "sup": supplier_name if str(supplier_name).isdigit() else None,
        "ct": int(currency_type) if str(currency_type).isdigit() else 1,
        "pw": int(pay_way) if str(pay_way).isdigit() else None,
        "ga": goods_amount,
        "delv": delivery_time[:19] if delivery_time else None,
        "tx": taxes if taxes not in (None, "") else None,
        "tp": total_price,
        "class_id": class_id_int,
        "obt": out_bill_type_id if str(out_bill_type_id).isdigit() else None,
        "add_uid": add_uid or None,
        "exp_type": exp_type_id,
        "ctm": collection_time[:500] if collection_time else None,
        "usi": (user_scale_info[:500] if user_scale_info else None),
        "scsi": (salecb_user_scale_info[:255] if salecb_user_scale_info else None),
        "online": is_online,
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
                 add_user_id, exp_type_id, collection_time,
                 user_scale_info, scale_info, salecb_user_scale_info, is_online)
            VALUES
                (NOW(), 0, %(ono)s, %(ot)s, %(st)s,
                 %(mobile)s, %(rev)s, %(addr)s, %(an)s, %(am)s,
                 0, 0, %(inv)s, %(msg)s, %(mark)s,
                 %(otm)s, %(sm)s, %(su)s, %(cuid)s, %(cust)s,
                 %(sup)s, %(ct)s, %(pw)s, %(ga)s,
                 %(delv)s, %(tx)s, %(tp)s, %(class_id)s, %(obt)s,
                 %(add_uid)s, %(exp_type)s, %(ctm)s,
                 %(usi)s, %(usi)s, %(scsi)s, %(online)s)
            """,
            params,
        )
    except Exception:
        try:
            order_pk = execute_insert(
                """
                INSERT INTO experiment_order
                    (addTime, deleteStatus, order_id, order_type, order_status,
                     totalPrice, sale_manager, sale_user, customer_name, supplier_name,
                     currency_type, invoiceType, class_id, msg, mark)
                VALUES
                    (NOW(), 0, %(ono)s, %(ot)s, %(st)s,
                     %(tp)s, %(sm)s, %(su)s, %(cust)s, %(sup)s,
                     %(ct)s, %(inv)s, %(class_id)s, %(msg)s, %(mark)s)
                """,
                params,
            )
        except Exception as exc:
            return False, f"订单提交失败：{exc}", None
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
                        add_user_id=%(add_uid)s, mobile=%(mobile)s,
                        collection_time=%(ctm)s,
                        user_scale_info=%(usi)s, scale_info=%(usi)s,
                        salecb_user_scale_info=%(scsi)s,
                        is_online=%(online)s
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
            "uid": int(add_uid) if str(add_uid).isdigit() else None,
        }
        # experiment_order_child 列名为 snake_case（add_time/delete_status），
        # delete_status：1=删除 2=正常（对齐 Java Mapper）
        child_pk = None
        try:
            child_pk = execute_insert(
                """
                INSERT INTO experiment_order_child
                    (add_time, delete_status, order_form_id, order_id, add_user,
                     goods_id, goods_name, goods_spec, goods_brand_id, goods_brand_name,
                     goods_nums, goods_price, reference_price,
                     experiment_project_id, experiment_project_name,
                     experiment_class_id, experiment_class_name,
                     order_status, in_status, op_status, fcsq, is_meeting, currency_type)
                VALUES
                    (NOW(), 2, %(oid)s, %(cno)s, %(uid)s,
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
                        (add_time, delete_status, order_form_id, order_id,
                         goods_id, goods_name, goods_spec, goods_brand_name, goods_nums,
                         goods_price, reference_price, experiment_project_id, experiment_project_name,
                         experiment_class_id, experiment_class_name,
                         order_status, op_status, currency_type)
                    VALUES
                        (NOW(), 2, %(oid)s, %(cno)s,
                         %(gid)s, %(gn)s, %(gs)s, %(gb)s, %(nums)s,
                         %(price)s, %(ref)s, %(epid)s, %(epn)s,
                         %(ecid)s, %(ecn)s,
                         1, 1, %(ct)s)
                    """,
                    child_params,
                )
            except Exception as exc:
                return False, f"产品明细保存失败：{exc}", None
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
    _attach_accessories_to_order(int(order_pk), aids or [])

    return True, str(order_pk), int(order_pk)


def _accessory_linked_order_id(row: dict[str, Any]) -> int:
    for key in ("exp_of_id", "of_id", "expOfId", "ofId"):
        v = row.get(key)
        if v in (None, "", 0, "0"):
            continue
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return 0


def _attach_accessories_to_order(order_pk: int, accessory_ids: list[Any]) -> None:
    """挂订单资料：未绑定则绑定；已挂其它单则克隆（复制建单不抢走源单附件）。

    同时写 of_id（Java）与 exp_of_id（本仓），避免复制页/详情查不到。
    """
    from datetime import datetime

    from apps.orders.repositories import accessory as accessory_repo

    for aid in accessory_ids or []:
        s = str(aid).strip()
        if not s.isdigit():
            continue
        acc_id = int(s)
        row = fetch_one(
            """
            SELECT * FROM accessory
            WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": acc_id},
        )
        if not row:
            continue
        linked = _accessory_linked_order_id(row)
        if linked == order_pk:
            continue
        if linked and linked != order_pk:
            # 复制建单：克隆附件行，保留源单资料
            try:
                new_id = accessory_repo.insert_accessory(
                    add_time=datetime.now(),
                    name=str(row.get("name") or ""),
                    path=str(row.get("path") or ""),
                    ext=str(row.get("ext") or "")[:64],
                    info=str(row.get("info") or row.get("name") or "upload")[:255],
                    acc_type=int(row.get("type") or 3) or 3,
                    exp_of_id=order_pk,
                )
                if new_id:
                    try:
                        execute(
                            "UPDATE accessory SET of_id = %(oid)s WHERE id = %(id)s",
                            {"oid": order_pk, "id": int(new_id)},
                        )
                    except Exception:
                        pass
            except Exception:
                pass
            continue
        # 新建上传未绑定：挂到本单（兼容 of_id / exp_of_id）
        try:
            execute(
                """
                UPDATE accessory
                SET exp_of_id = %(oid)s,
                    of_id = %(oid)s,
                    type = IFNULL(NULLIF(type, 0), 3)
                WHERE id = %(aid)s AND IFNULL(deleteStatus, 0) = 0
                """,
                {"oid": order_pk, "aid": acc_id},
            )
        except Exception:
            try:
                execute(
                    """
                    UPDATE accessory
                    SET exp_of_id = %(oid)s, type = IFNULL(NULLIF(type, 0), 3)
                    WHERE id = %(aid)s AND IFNULL(deleteStatus, 0) = 0
                    """,
                    {"oid": order_pk, "aid": acc_id},
                )
            except Exception:
                pass


# 对齐 Java excel-config.xml id=experimentOrder 的订单状态 format
# （导出用库内原始 order_status，勿用列表页派生的 41/42）
_EXPORT_ORDER_STATUS_LABEL = {
    0: "已取消",
    5: "待提交审核",
    10: "已驳回",
    20: "待审核",
    30: "已审核",
    40: "已确认",
    49: "已付款",
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


def _fmt_export_money(value: Any) -> str:
    d = _to_decimal(value)
    if d is None:
        return ""
    text = format(d, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def build_experiment_order_export_matrix(
    *,
    limit: int = 5000,
    scope: dict[str, Any] | None = None,
    **filters: Any,
) -> tuple[list[str], list[list]]:
    """对齐 Java UTExperimentOrderController.exportExcel + excel-config experimentOrder。

    - 按子单展开；同一主单后续行清空主单字段（序号/下单时间/订单号/客户/总金额/开票付款/状态）
    - 订单状态用库内原始值 + excel format（含 49:已付款），不用列表页派生状态
    - 下单时间保留 yyyy-MM-dd HH:mm:ss
    """
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
    order_id_set = set(order_ids)

    # 列表接口会改写 orderStatus / 截断 orderTime，导出重新取库内原始字段
    raw_rows = fetch_all(
        f"""
        SELECT
            t.id,
            t.order_id AS orderId,
            t.order_status AS orderStatus,
            t.order_time AS orderTime,
            t.addTime,
            t.totalPrice AS totalPrice,
            q.name AS customerName
        FROM experiment_order t
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        WHERE t.id IN ({placeholders})
        """,
        oid_params,
    )
    raw_by_id: dict[int, dict[str, Any]] = {}
    for r in raw_rows:
        try:
            raw_by_id[int(r["id"])] = r
        except (TypeError, ValueError, KeyError):
            continue

    # 对齐 Java getChildsByOfIdHt：delete_status=2 AND order_status > 0
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

    # 开票/收款：UT 列表用 exp_of_id；Java export 写的是 of_id，两边都收以免漏单
    bill_rows = fetch_all(
        f"""
        SELECT
            exp_of_id AS expOfId,
            of_id AS ofId,
            type AS billType,
            money,
            bill_date AS billDate,
            add_time AS addTime
        FROM qd_bill
        WHERE exp_of_id IN ({placeholders})
           OR of_id IN ({placeholders})
        ORDER BY add_time ASC, id ASC
        """,
        oid_params,
    )
    first_kp: dict[int, str] = {}
    first_sk: dict[int, str] = {}
    kp_sum: dict[int, Any] = {}
    sk_sum: dict[int, Any] = {}
    from decimal import Decimal

    for b in bill_rows:
        mapped: int | None = None
        try:
            exp_id = int(b["expOfId"]) if b.get("expOfId") is not None else None
        except (TypeError, ValueError):
            exp_id = None
        try:
            plain_id = int(b["ofId"]) if b.get("ofId") is not None else None
        except (TypeError, ValueError):
            plain_id = None
        if exp_id in order_id_set:
            mapped = exp_id
        elif plain_id in order_id_set:
            mapped = plain_id
        if mapped is None:
            continue
        try:
            btype = int(b.get("billType"))
        except (TypeError, ValueError):
            continue
        money = _to_decimal(b.get("money")) or Decimal("0")
        dt = _fmt_export_dt(b.get("billDate") or b.get("addTime"), date_only=True)
        if btype == 1:
            kp_sum[mapped] = kp_sum.get(mapped, Decimal("0")) + money
            if mapped not in first_kp:
                first_kp[mapped] = dt
        elif btype == 2:
            sk_sum[mapped] = sk_sum.get(mapped, Decimal("0")) + money
            if mapped not in first_sk:
                first_sk[mapped] = dt

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
        raw = raw_by_id.get(of_id) or {}
        iskp = "已开票" if of_id in kp_sum else "未开票"
        isfk = "已付款" if of_id in sk_sum else "未付款"
        kpje = _fmt_export_money(kp_sum.get(of_id))
        skje = _fmt_export_money(sk_sum.get(of_id))
        order_time = _fmt_export_dt(raw.get("orderTime") or raw.get("addTime") or of.get("addTime"))
        order_id = raw.get("orderId") or of.get("orderId") or ""
        company = raw.get("customerName") or of.get("customerName") or ""
        total_price = _fmt_export_money(raw.get("totalPrice") if raw else of.get("totalPrice"))
        status_label = _export_order_status_label(raw.get("orderStatus"))
        xskprq = first_kp.get(of_id, "")
        xsskrq = first_sk.get(of_id, "")

        for i, ch in enumerate(kids):
            goods_total = ""
            child_price = _to_decimal(ch.get("goodsPrice"))
            child_nums = _to_decimal(ch.get("goodsNums"))
            if child_price is not None and child_nums is not None:
                goods_total = _fmt_export_money(child_price * child_nums)
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
                    total_price,
                    goods_total,
                    iskp,
                    xskprq,
                    kpje,
                    isfk,
                    xsskrq,
                    skje,
                    status_label,
                ]
            else:
                # 对齐 Java：同单后续行清空主单展示字段
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
                    goods_total,
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
            scope=filters.get("scope"),
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


# 对齐 Java excel-config.xml id=expSubPurchaseOrder（实验子订单 export.htm）
SUB_ORDER_EXPORT_HEADERS = [
    "序号",
    "订单编号",
    "来源订单",
    "进货公司名称",
    "订单总价",
    "下单时间",
    "订单状态",
    "确认状态",
    "付款状态",
    "付款时间",
    "付款金额",
    "产品名称",
    "产品型号",
    "服务项目",
    "实验测试分类",
    "测试人员",
    "实验平台",
    "状态",
    "完成操作时间",
    "预估完成时间",
    "实际完成时间",
]

# 对齐 Java excel-config.xml id=bjexperimentSubOrder（实验子订单 bjexport.htm）
SUB_ORDER_FINISHED_EXPORT_HEADERS = [
    "序号",
    "日期",
    "系统订单号",
    "客户名称",
    "客户账号",
    "系统单号",
    "订单状态",
    "确认状态",
    "订单类型",
    "产品名称",
    "产品型号",
    "服务项目",
    "实验测试分类",
    "测试人员",
    "实验平台",
    "状态",
    "完成操作时间",
    "预估完成时间",
    "实际完成时间",
]

_EXPORT_SUB_PAY_STATUS_LABEL = {
    -1: "无",
    0: "未申请",
    32: "付款申请待审核",
    33: "付款申请已驳回",
    34: "付款申请已审核",
    36: "已付款",
    38: "已完成",
}


def _export_sub_pay_status_label(v: Any) -> str:
    if v is None or v == "":
        return _EXPORT_SUB_PAY_STATUS_LABEL[0]
    try:
        return _EXPORT_SUB_PAY_STATUS_LABEL.get(int(v), str(v))
    except (TypeError, ValueError):
        return _EXPORT_SUB_PAY_STATUS_LABEL[0]


def _fmt_export_dt_slash(value: Any, *, date_only: bool = False) -> str:
    text = _fmt_export_dt(value, date_only=date_only)
    if not text:
        return ""
    if date_only:
        return text[:10].replace("-", "/")
    return text.replace("-", "/", 2)


def _child_ygdate(finish_time: Any, time_type: Any) -> str:
    """对齐 Java：time_type==1 → 小时，其余 → 天。"""
    try:
        tt = int(time_type) if time_type is not None else 0
    except (TypeError, ValueError):
        tt = 0
    unit = "小时" if tt == 1 else "天"
    if finish_time in (None, ""):
        return f"0{unit}"
    return f"{finish_time}{unit}"


def _child_sjdate(logs: list[dict[str, Any]], time_type: Any) -> str:
    from datetime import datetime
    from decimal import Decimal, ROUND_HALF_UP

    try:
        tt = int(time_type) if time_type is not None else 0
    except (TypeError, ValueError):
        tt = 0
    if tt == 1:
        unit = "小时"
    elif tt == 3:
        unit = "分钟"
    elif tt == 2:
        unit = "天"
    else:
        unit = ""
    total = Decimal("0")
    for lg in logs:
        st, et = lg.get("startTime"), lg.get("endTime")
        if not st or not et:
            continue
        try:
            def _parse(v: Any):
                if hasattr(v, "timestamp"):
                    return v
                s = str(v).replace("T", " ")[:19]
                return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

            minutes = Decimal(str(max(0, (_parse(et) - _parse(st)).total_seconds() / 60.0)))
        except Exception:
            continue
        if tt == 1:
            minutes = (minutes / Decimal("60")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif tt == 2:
            minutes = (minutes / Decimal("1440")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += minutes
    return f"{total}{unit}"


def _load_sub_order_child_lines(order_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    if not order_ids:
        return {}
    placeholders = ", ".join(f"%(oid{i})s" for i in range(len(order_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    rows = fetch_all(
        f"""
        SELECT
            poc.purchase_order_id AS ofId,
            c.id AS childPkId,
            c.order_id AS childOrderId,
            c.order_status AS childStatus,
            c.goods_name AS goodsName,
            c.goods_spec AS goodsSpec,
            c.experiment_project_name AS projectName,
            c.experiment_class_name AS className,
            c.finish_time AS finishTimeVal,
            c.time_type AS timeType,
            c.test_user_id AS testUserId,
            tu.user_name AS testUserName,
            tu.true_name AS testTrueName,
            ln.line_num AS lineName
        FROM exp_qd_purchase_order_child poc
        JOIN experiment_order_child c ON poc.order_child_id = c.id
        LEFT JOIN sy_users tu ON c.test_user_id = tu.id
        LEFT JOIN experiment_line ln ON c.line_id = ln.id
        WHERE poc.purchase_order_id IN ({placeholders})
          AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY poc.purchase_order_id ASC, c.id ASC
        """,
        params,
    )
    by_of: dict[int, list[dict[str, Any]]] = {}
    child_ids: list[int] = []
    for r in rows:
        try:
            of_id = int(r.get("ofId"))
            cid = int(r.get("childPkId"))
        except (TypeError, ValueError):
            continue
        by_of.setdefault(of_id, []).append(r)
        child_ids.append(cid)

    cz_logs: dict[int, list[dict[str, Any]]] = {}
    if order_ids:
        log_rows = fetch_all(
            f"""
            SELECT of_id AS ofId, log_info AS logInfo, addTime
            FROM experiment_order_log
            WHERE of_id IN ({placeholders})
              AND log_info LIKE %(kw)s
              AND IFNULL(deleteStatus, 0) = 0
            ORDER BY addTime ASC
            """,
            {**params, "kw": "%测试完成%"},
        )
        for lg in log_rows:
            try:
                of_id = int(lg.get("ofId"))
            except (TypeError, ValueError):
                continue
            cz_logs.setdefault(of_id, []).append(lg)

    logs_by_cid: dict[int, list[dict[str, Any]]] = {}
    if child_ids:
        uniq = sorted(set(child_ids))
        cph = ", ".join(f"%(cid{i})s" for i in range(len(uniq)))
        cparams = {f"cid{i}": cid for i, cid in enumerate(uniq)}
        try:
            elogs = fetch_all(
                f"""
                SELECT order_child_id AS childId, start_time AS startTime, end_time AS endTime
                FROM experiment_log
                WHERE order_child_id IN ({cph}) AND IFNULL(deleteStatus, 0) = 0
                ORDER BY addTime DESC
                """,
                cparams,
            )
            for lg in elogs:
                try:
                    cid = int(lg["childId"])
                except (TypeError, ValueError, KeyError):
                    continue
                logs_by_cid.setdefault(cid, []).append(lg)
        except Exception:
            pass

    for of_id, kids in by_of.items():
        logs = cz_logs.get(of_id) or []
        for ch in kids:
            child_oid = str(ch.get("childOrderId") or "")
            cz = None
            for lg in logs:
                info = str(lg.get("logInfo") or "")
                if child_oid and f"{child_oid}测试完成" in info:
                    cz = lg.get("addTime")
                    break
            if cz is None and child_oid and "-" in child_oid:
                num = child_oid.split("-")[-1]
                for lg in logs:
                    info = str(lg.get("logInfo") or "").replace(" ", "")
                    if num and f"{num}测试完成" in info:
                        cz = lg.get("addTime")
                        break
            ch["czdate"] = _fmt_export_dt_slash(cz)
            ch["ygdate"] = _child_ygdate(ch.get("finishTimeVal"), ch.get("timeType"))
            try:
                cid = int(ch.get("childPkId"))
            except (TypeError, ValueError):
                cid = 0
            ch["sjdate"] = _child_sjdate(logs_by_cid.get(cid) or [], ch.get("timeType"))
            ch["testName"] = str(ch.get("testUserName") or ch.get("testTrueName") or "")
            ch["childStatusLabel"] = _child_line_status_label(ch.get("childStatus"))
    return by_of


def _load_pay_bill_summary(order_ids: list[int]) -> dict[int, tuple[str, str]]:
    """收款单 type=2：付款时间/金额，多个以逗号分隔。"""
    if not order_ids:
        return {}
    placeholders = ", ".join(f"%(oid{i})s" for i in range(len(order_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    rows = fetch_all(
        f"""
        SELECT exp_of_id AS ofId, bill_date AS billDate, money, add_time AS addTime
        FROM qd_bill
        WHERE type = 2 AND exp_of_id IN ({placeholders})
        ORDER BY id ASC
        """,
        params,
    )
    out: dict[int, list[tuple[str, str]]] = {}
    for r in rows:
        try:
            of_id = int(r.get("ofId"))
        except (TypeError, ValueError):
            continue
        dt = _fmt_export_dt(r.get("billDate") or r.get("addTime"), date_only=True)
        money = "" if r.get("money") is None else str(r.get("money"))
        out.setdefault(of_id, []).append((dt, money))
    return {
        oid: (
            ",".join(x[0] for x in pairs if x[0]),
            ",".join(x[1] for x in pairs if x[1]),
        )
        for oid, pairs in out.items()
    }


def _load_sub_order_export_customer_meta(order_ids: list[int]) -> dict[int, dict[str, str]]:
    """bjexport 客户名称/客户账号：子单自身 + 父单，账号优先 mobile（对齐 Java customUser）。"""
    if not order_ids:
        return {}
    placeholders = ", ".join(f"%(oid{i})s" for i in range(len(order_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(order_ids)}
    rows = fetch_all(
        f"""
        SELECT
            t.id AS oid,
            COALESCE(NULLIF(q.name, ''), NULLIF(pq.name, '')) AS customerName,
            COALESCE(
                NULLIF(cu.mobile, ''),
                NULLIF(cu2.mobile, ''),
                NULLIF(pcu.mobile, ''),
                NULLIF(pcu2.mobile, ''),
                NULLIF(cu.userName, ''),
                NULLIF(cu2.userName, ''),
                NULLIF(pcu.userName, ''),
                NULLIF(pcu2.userName, '')
            ) AS customMobile
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        LEFT JOIN qd_user_company pq ON p.customer_name = pq.id
        LEFT JOIN exp_user cu ON CAST(t.custom_user_id AS CHAR) = CAST(cu.id AS CHAR)
        LEFT JOIN `user` cu2 ON CAST(t.custom_user_id AS CHAR) = CAST(cu2.id AS CHAR)
        LEFT JOIN exp_user pcu ON CAST(p.custom_user_id AS CHAR) = CAST(pcu.id AS CHAR)
        LEFT JOIN `user` pcu2 ON CAST(p.custom_user_id AS CHAR) = CAST(pcu2.id AS CHAR)
        WHERE t.id IN ({placeholders})
        """,
        params,
    )
    out: dict[int, dict[str, str]] = {}
    for r in rows:
        try:
            oid = int(r.get("oid"))
        except (TypeError, ValueError):
            continue
        name = str(r.get("customerName") or "").strip()
        mobile = str(r.get("customMobile") or "").strip()
        if mobile == "-":
            mobile = ""
        out[oid] = {"customerName": name, "customMobile": mobile}
    return out


def build_sub_order_export_matrix(
    *,
    order_type: str = "10",
    finished_only: bool = False,
    limit: int = 5000,
    **filters: Any,
) -> tuple[list[str], list[list], list[str]]:
    """对齐 Java experimentChildOrder/export.htm 与 bjexport.htm。

    返回 (headers, matrix, merges)；merges 为 Excel A1 引用（含表头行）。
    """
    ot = str(order_type or "10")
    if ot not in ("9", "10"):
        ot = "10"
    headers = SUB_ORDER_FINISHED_EXPORT_HEADERS if finished_only else SUB_ORDER_EXPORT_HEADERS

    # Java 普通导出前端不传完成时间；bjexport 传完成时间且要求有测试完成日志
    finish_start = str(filters.get("finish_start") or "") if finished_only else ""
    finish_end = str(filters.get("finish_end") or "") if finished_only else ""

    list_kwargs: dict[str, Any] = dict(
        order_type=ot,
        order_id=str(filters.get("order_id") or ""),
        parent_order_id=str(filters.get("parent_order_id") or ""),
        customer_name=str(filters.get("customer_name") or ""),
        sale_manager=str(filters.get("sale_manager") or ""),
        sale_user=str(filters.get("sale_user") or ""),
        order_status=str(filters.get("order_status") or ""),
        pay_status=str(filters.get("pay_status") if filters.get("pay_status") is not None else ""),
        test_user_id=str(filters.get("test_user_id") or ""),
        is_confirm=str(filters.get("is_confirm") if filters.get("is_confirm") is not None else ""),
        finish_start=finish_start,
        finish_end=finish_end,
        require_finish_log=bool(finished_only),
        page=1,
        page_size=limit,
        scope=filters.get("scope"),
    )

    orders, _ = list_sub_orders(**list_kwargs)
    if not orders:
        return headers, [], []

    order_ids = [int(o["id"]) for o in orders if o.get("id") is not None]
    children_by_of = _load_sub_order_child_lines(order_ids)
    pay_by_of = {} if finished_only else _load_pay_bill_summary(order_ids)
    cust_meta = _load_sub_order_export_customer_meta(order_ids) if finished_only else {}

    type_name = "实验子订单" if ot == "10" else "实验分包子订单"
    matrix: list[list] = []
    merges: list[str] = []
    nums = 1
    for o in orders:
        try:
            oid = int(o["id"])
        except (TypeError, ValueError, KeyError):
            continue
        kids = children_by_of.get(oid) or []
        if finished_only:
            kids = [
                k
                for k in kids
                if str(k.get("childStatus") if k.get("childStatus") is not None else "") == "50"
                or k.get("childStatus") == 50
            ]
        if not kids:
            continue
        sk_dates, sk_money = pay_by_of.get(oid, ("", ""))
        parent_no = str(o.get("parentOrderId") or "")
        cm = cust_meta.get(oid) or {}
        cust_name = str(cm.get("customerName") or o.get("customerName") or "").strip()
        cust_account = str(cm.get("customMobile") or "").strip()
        if cust_account == "-":
            cust_account = ""
        stock_name = str(o.get("stockCompanyName") or "")
        pay_label = _export_sub_pay_status_label(o.get("payStatus"))
        group_start = len(matrix)  # 0-based matrix index
        for i, ch in enumerate(kids):
            if finished_only:
                if i == 0:
                    row = [
                        str(nums),
                        _fmt_export_dt_slash(o.get("orderTime"), date_only=True),
                        parent_no,
                        cust_name,
                        cust_account,
                        str(o.get("orderId") or ""),
                        str(o.get("orderStatusLabel") or ""),
                        str(o.get("confirmLabel") or ""),
                        type_name,
                        str(ch.get("goodsName") or ""),
                        str(ch.get("goodsSpec") or ""),
                        str(ch.get("projectName") or ""),
                        str(ch.get("className") or ""),
                        str(ch.get("testName") or ""),
                        str(ch.get("lineName") or ""),
                        str(ch.get("childStatusLabel") or ""),
                        str(ch.get("czdate") or ""),
                        str(ch.get("ygdate") or ""),
                        str(ch.get("sjdate") or ""),
                    ]
                else:
                    # 对齐 Java：多测项续行主单列留空，由单元格合并展示
                    row = [
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        str(ch.get("goodsName") or ""),
                        str(ch.get("goodsSpec") or ""),
                        str(ch.get("projectName") or ""),
                        str(ch.get("className") or ""),
                        str(ch.get("testName") or ""),
                        str(ch.get("lineName") or ""),
                        str(ch.get("childStatusLabel") or ""),
                        str(ch.get("czdate") or ""),
                        str(ch.get("ygdate") or ""),
                        str(ch.get("sjdate") or ""),
                    ]
            else:
                if i == 0:
                    row = [
                        str(nums),
                        str(o.get("orderId") or ""),
                        parent_no,
                        stock_name,
                        o.get("totalPrice"),
                        _fmt_export_dt(o.get("orderTime"), date_only=True),
                        str(o.get("orderStatusLabel") or ""),
                        str(o.get("confirmLabel") or ""),
                        pay_label,
                        sk_dates,
                        sk_money,
                        str(ch.get("goodsName") or ""),
                        str(ch.get("goodsSpec") or ""),
                        str(ch.get("projectName") or ""),
                        str(ch.get("className") or ""),
                        str(ch.get("testName") or ""),
                        str(ch.get("lineName") or ""),
                        str(ch.get("childStatusLabel") or ""),
                        str(ch.get("czdate") or ""),
                        str(ch.get("ygdate") or ""),
                        str(ch.get("sjdate") or ""),
                    ]
                else:
                    row = [
                        "",
                        "",
                        "",
                        "",
                        None,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        str(ch.get("goodsName") or ""),
                        str(ch.get("goodsSpec") or ""),
                        str(ch.get("projectName") or ""),
                        str(ch.get("className") or ""),
                        str(ch.get("testName") or ""),
                        str(ch.get("lineName") or ""),
                        str(ch.get("childStatusLabel") or ""),
                        str(ch.get("czdate") or ""),
                        str(ch.get("ygdate") or ""),
                        str(ch.get("sjdate") or ""),
                    ]
            matrix.append(row)
        if finished_only and len(kids) > 1:
            # 表头占第 1 行，数据从第 2 行；合并序号~确认状态（A-H）
            excel_start = group_start + 2
            excel_end = group_start + len(kids) + 1
            for col_idx in range(8):  # A..H
                col = _excel_col_letter(col_idx)
                merges.append(f"{col}{excel_start}:{col}{excel_end}")
        nums += 1
    return headers, matrix, merges


def _excel_col_letter(idx: int) -> str:
    n = idx + 1
    letters: list[str] = []
    while n:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(65 + rem))
    return "".join(reversed(letters))
