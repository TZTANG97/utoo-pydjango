"""小程序 getOrderCount — 对齐 Java WxController#getOrderCount 核心计数字段。"""
from __future__ import annotations

from typing import Any

from apps.core.db_utils import fetch_one, scalar


def load_sy_user(user_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, user_name, true_name, type, utoo_type
        FROM sy_users
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": str(user_id)},
    )


def is_admin_user(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    utoo = str(row.get("utoo_type") or "").upper()
    typ = str(row.get("type") or "").upper()
    name = str(row.get("true_name") or row.get("user_name") or "")
    if "ADMIN" in utoo or utoo in ("ADMIN", "系统管理员"):
        return True
    if "ADMIN" in typ or typ in ("ADMIN", "系统管理员"):
        return True
    if name in ("admin", "管理员"):
        return True
    return False


def is_sale_or_test_manager(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    blob = f"{row.get('utoo_type') or ''} {row.get('type') or ''}".upper()
    return "SALE_MANAGER" in blob or "TEST_MANAGER" in blob or "销售主管" in blob or "测试主管" in blob


def _staff_scope_sql(uid: str, params: dict[str, Any], *, alias: str = "t") -> str:
    """员工可见范围：销售/主管/制单人命中当前用户。"""
    params["uid"] = uid
    params["uid_like"] = f"%{uid}%"
    return f"""
      AND (
        CAST({alias}.sale_user AS CHAR) = %(uid)s
        OR CAST({alias}.sale_manager AS CHAR) = %(uid)s
        OR CAST({alias}.add_user_id AS CHAR) = %(uid)s
        OR {alias}.sale_user LIKE %(uid_like)s
        OR {alias}.sale_manager LIKE %(uid_like)s
      )
    """


def count_by_type(
    *,
    order_type: str,
    user_id: str = "",
    admin: bool = False,
    child: bool = False,
) -> int:
    params: dict[str, Any] = {"ot": str(order_type)}
    where = """
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND CAST(t.order_type AS CHAR) = %(ot)s
    """
    if child:
        where += " AND t.order_status > 0"
    else:
        where += " AND t.order_status <> 0"
    if not admin and user_id:
        where += _staff_scope_sql(user_id, params)
    n = scalar(
        f"SELECT COUNT(1) FROM experiment_order t {where}",
        params,
        default=0,
    )
    try:
        return int(n or 0)
    except (TypeError, ValueError):
        return 0


def count_manage_by_type(*, order_type: str, user_id: str) -> int:
    """待审核：order_status=20 且 sale_manager 命中。"""
    params: dict[str, Any] = {"ot": str(order_type), "uid": str(user_id), "uid_like": f"%{user_id}%"}
    n = scalar(
        """
        SELECT COUNT(1) FROM experiment_order t
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND CAST(t.order_type AS CHAR) = %(ot)s
          AND t.order_status = 20
          AND (
            CAST(t.sale_manager AS CHAR) = %(uid)s
            OR t.sale_manager LIKE %(uid_like)s
          )
        """,
        params,
        default=0,
    )
    try:
        return int(n or 0)
    except (TypeError, ValueError):
        return 0


def count_exp_sub_child_pay(*, user_id: str) -> int:
    """type=9 且 pay_status=32。"""
    params: dict[str, Any] = {"uid": str(user_id), "uid_like": f"%{user_id}%"}
    n = scalar(
        """
        SELECT COUNT(1) FROM experiment_order t
        WHERE IFNULL(t.deleteStatus, 0) = 0
          AND CAST(t.order_type AS CHAR) = '9'
          AND CAST(t.pay_status AS CHAR) = '32'
          AND (
            CAST(t.sale_manager AS CHAR) = %(uid)s
            OR t.sale_manager LIKE %(uid_like)s
          )
        """,
        params,
        default=0,
    )
    try:
        return int(n or 0)
    except (TypeError, ValueError):
        return 0


def build_order_count_obj(*, user_id: str, user_row: dict[str, Any] | None) -> dict[str, Any]:
    admin = is_admin_user(user_row)
    uid = "" if admin else str(user_id)

    order_count = count_by_type(order_type="6", user_id=uid, admin=admin, child=False)
    suborder_count = count_by_type(order_type="8", user_id=uid, admin=admin, child=False)
    orderchild_count = count_by_type(order_type="10", user_id=uid, admin=admin, child=True)
    suborderchild_count = count_by_type(order_type="9", user_id=uid, admin=admin, child=True)
    order_count_all = order_count + suborder_count + orderchild_count + suborderchild_count

    order_count_m = suborder_count_m = orderchild_count_m = suborderchild_count_m = 0
    exp_sub_pay = 0
    if is_sale_or_test_manager(user_row) or admin:
        mid = str(user_id)
        order_count_m = count_manage_by_type(order_type="6", user_id=mid)
        suborder_count_m = count_manage_by_type(order_type="8", user_id=mid)
        orderchild_count_m = count_manage_by_type(order_type="10", user_id=mid)
        suborderchild_count_m = count_manage_by_type(order_type="9", user_id=mid)
        exp_sub_pay = count_exp_sub_child_pay(user_id=mid)

    order_count_by_manage = (
        order_count_m + suborder_count_m + orderchild_count_m + suborderchild_count_m + exp_sub_pay
    )

    return {
        "orderCount": order_count,
        "suborderCount": suborder_count,
        "orderchildCount": orderchild_count,
        "suborderchildCount": suborderchild_count,
        "orderCountAll": order_count_all,
        "orderCountByManage": order_count_by_manage,
        "orderCountm": order_count_m,
        "suborderCountm": suborder_count_m,
        "orderchildCountm": orderchild_count_m,
        "suborderchildCountm": suborderchild_count_m,
        "expsubChildpayListnum": exp_sub_pay,
    }
