"""UTOO 用户类型枚举（小程序/前端 userRoles）— 产品参考数据，非 identity 主数据。"""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# 对齐 Java com.qdmall.sys.enums.UserTypes（key=枚举名, name=类型中文, roleName=权限角色）
USER_TYPES_DEFAULT: dict[str, dict[str, str]] = {
    "ADMIN": {"name": "系统管理员", "roleName": "系统管理员"},
    "PUBLIC": {"name": "公共账号", "roleName": "公共账号"},
    "COMPANY": {"name": "公司账号", "roleName": "公司账号"},
    "OUT_COOPERATE_COMPANY": {"name": "外部合作公司", "roleName": "外部合作公司"},
    "OUT_COMPANY": {"name": "外部公司", "roleName": "外部公司"},
    "SALE_MANAGER": {"name": "销售主管", "roleName": "销售主管"},
    "C_SALE_USER": {"name": "C类销售人员", "roleName": "C类销售人员"},
    "R_SALE_USER": {"name": "R类人员", "roleName": "R类人员"},
    "H_USER": {"name": "H类用户", "roleName": "H类用户"},
    "A_SALE_USER": {"name": "A类销售人员", "roleName": "A类销售人员"},
    "A_ORDER_ADDER": {"name": "制单员", "roleName": "A类销售人员"},
    "A_SALESPERSON": {"name": "销售人员", "roleName": "A类销售人员"},
    "A_INTERNAL_MANAGER": {"name": "内勤主管", "roleName": "A类销售人员"},
    "A_STORE_MANAGER": {"name": "仓库管理", "roleName": "A类销售人员"},
    "A_COMPANY_FUND": {"name": "公司基金", "roleName": "A类销售人员"},
    "A_ORIGIN_SALE_USER": {"name": "原厂销售人员", "roleName": "A类销售人员"},
    "A_OUT_INVEST": {"name": "外部投资", "roleName": "A类销售人员"},
    "TEST_USER": {"name": "测试人员", "roleName": "测试人员"},
    "TEST_MANAGER": {"name": "测试主管", "roleName": "销售主管"},
}

_NAME_TO_KEY = {v["name"]: k for k, v in USER_TYPES_DEFAULT.items()}


def build_user_roles(
    *,
    fetch_rows: Callable[[], list[dict[str, Any]]] | None = None,
) -> dict[str, dict[str, str]]:
    """静态枚举 + 可选库表覆盖（sy_user_type / user_type_role）。"""
    result = {k: dict(v) for k, v in USER_TYPES_DEFAULT.items()}
    if fetch_rows is None:
        return result
    try:
        rows = fetch_rows() or []
    except Exception as exc:
        logger.warning("userRoles db query failed, use enum defaults: %s", exc)
        return result

    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        key = _NAME_TO_KEY.get(name)
        if not key:
            continue
        role_name = (row.get("roleName") or "").strip() or result[key]["roleName"]
        result[key] = {"name": name, "roleName": role_name}
    return result
