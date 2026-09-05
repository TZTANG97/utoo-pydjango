"""UTOO 实验订单审核前置（阶段 A-4：权限校验在 utoo_biz，中台只做状态机）。"""
from __future__ import annotations

from typing import Any

from apps.utoo_experiment.repositories import db


def _staff_id(user: dict[str, Any] | None) -> str:
    return str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()


def _is_audit_admin(user_id: str | int | None) -> bool:
    uid = str(user_id or "").strip()
    if not uid:
        return False
    row = db.fetch_one(
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


def _is_sys_admin_user(user_id: str | int | None) -> bool:
    uid = str(user_id or "").strip()
    if not uid:
        return False
    u = db.fetch_one(
        """
        SELECT user_name AS userName, utoo_type AS utooType
        FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1
        """,
        {"id": uid},
    )
    if not u:
        return False
    name = str(u.get("userName") or "").strip().lower()
    utoo = str(u.get("utooType") or "").strip()
    return name == "admin" or utoo in ("系统管理员",)


def _fetch_order_row(order_id: int) -> dict[str, Any] | None:
    return db.fetch_one(
        """
        SELECT id,
               order_status AS orderStatus,
               order_type AS orderType,
               sale_manager AS saleManagerId,
               test_manager AS testManagerId
        FROM experiment_order
        WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": order_id},
    )


def validate_submit_audit(user: dict[str, Any] | None, order_id: int) -> tuple[bool, str]:
    uid = _staff_id(user)
    if not uid:
        return False, "用户未登录或登录已失效，请重新登录"
    row = _fetch_order_row(order_id)
    if not row:
        return False, "订单不存在"
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        return False, "订单状态异常"
    if st != 5:
        return False, "当前状态不可提交审核"
    return True, ""


def validate_withdraw_audit(user: dict[str, Any] | None, order_id: int) -> tuple[bool, str]:
    uid = _staff_id(user)
    if not uid:
        return False, "用户未登录或登录已失效，请重新登录"
    row = _fetch_order_row(order_id)
    if not row:
        return False, "订单不存在"
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        return False, "订单状态异常"
    if st != 20:
        return False, "当前状态不可取消审核申请"
    return True, ""


def validate_audit(user: dict[str, Any] | None, order_id: int) -> tuple[bool, str]:
    uid = _staff_id(user)
    if not uid:
        return False, "用户未登录或登录已失效，请重新登录"
    row = _fetch_order_row(order_id)
    if not row:
        return False, "订单不存在"
    try:
        st = int(row.get("orderStatus"))
    except (TypeError, ValueError):
        return False, "订单状态异常"
    if st != 20:
        return False, "当前状态不可审核"

    ot = str(row.get("orderType") or "")
    if ot == "9":
        tm = str(row.get("testManagerId") or "").strip()
        if uid != tm and not _is_sys_admin_user(uid):
            return False, "无审核权限（需实验室测试主管）"
    else:
        sm = str(row.get("saleManagerId") or "").strip()
        if uid != sm and not _is_audit_admin(uid):
            return False, "无审核权限"
    return True, ""
