"""UTOO 实验订单列表数据范围（阶段 A-4：产品逻辑在 utoo_biz）。"""
from __future__ import annotations

from typing import Any

from apps.utoo_experiment.repositories import db

_UTOO_TYPE_ROLE = {
    "系统管理员": "系统管理员",
    "公共账号": "公共账号",
    "公司账号": "公司账号",
    "外部合作公司": "外部合作公司",
    "外部公司": "外部公司",
    "销售主管": "销售主管",
    "测试主管": "销售主管",
    "测试人员": "测试人员",
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
    name = str(utoo_type or "").strip()
    if not name:
        return "A类销售人员"
    if name in _UTOO_TYPE_ROLE:
        return _UTOO_TYPE_ROLE[name]
    row = db.fetch_one(
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
    rows = db.fetch_all(
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
    n = db.scalar(
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
    rows = db.fetch_all(
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
    rows = db.fetch_all(
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
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    empty = {"user_id": "", "supplier_ids": [], "sale_user_ids": []}
    if not uid:
        return empty

    urow = db.fetch_one(
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


def build_exp_order_list_scope(
    user: dict[str, Any] | None,
    *,
    order_type: str = "6",
) -> dict[str, Any]:
    uid = str((user or {}).get("user_id") or (user or {}).get("id") or "").strip()
    if not uid:
        return {"filter_list": 2, "user_id": "", "supplier_ids": []}

    urow = db.fetch_one(
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

    supplier_ids: list[str] = []
    is_sale_mgr_or_admin = role in ("系统管理员", "销售主管")
    if not is_sale_mgr_or_admin:
        supplier_ids = list(linked)
        if _has_exp_order_type_perm(uid, order_type):
            for cid in _companies_from_sy_user_company(uid):
                if cid not in supplier_ids:
                    supplier_ids.append(cid)

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


def build_list_scope_for_order_type(
    user: dict[str, Any] | None,
    order_type: str,
) -> dict[str, Any]:
    if order_type in ("9", "10"):
        return build_sub_order_list_scope(user, order_type=order_type)
    return build_exp_order_list_scope(user, order_type=order_type)
