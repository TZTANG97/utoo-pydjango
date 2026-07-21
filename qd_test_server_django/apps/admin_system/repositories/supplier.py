from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from qd_common.password_java import encrypt_password_for_storage

SUPPLIER_USER_TYPE = 6

# 编辑/列表共用字段，避免宽 SELECT 因列缺失导致 DatabaseError
_SUPPLIER_SELECT = """
    id, userName, company_name, trueName, mobile, address, area_info,
    company_code, addTime, deleteStatus, email, area_id, city, province, address_info
"""


def list_suppliers(
    *,
    user_name: str = "",
    company_name: str = "",
    true_name: str = "",
    mobile: str = "",
    area_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE userType = %(user_type)s AND (deleteStatus = 0 OR deleteStatus IS NULL)"
    params: dict[str, Any] = {"user_type": SUPPLIER_USER_TYPE}
    if user_name:
        where += " AND userName LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if company_name:
        where += " AND company_name LIKE %(company_name)s"
        params["company_name"] = f"%{company_name}%"
    if true_name:
        where += " AND trueName LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if mobile:
        where += " AND mobile LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    if area_id:
        where += " AND area_info = %(area_id)s"
        params["area_id"] = area_id
    total = scalar(f"SELECT COUNT(*) FROM `user` {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT {_SUPPLIER_SELECT}
        FROM `user`
        {where}
        ORDER BY addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_supplier(row) for row in rows], int(total)


def get_supplier(supplier_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        f"""
        SELECT {_SUPPLIER_SELECT}
        FROM `user`
        WHERE id = %(id)s AND userType = %(user_type)s
        """,
        {"id": supplier_id, "user_type": SUPPLIER_USER_TYPE},
    )
    return _normalize_supplier(row) if row else None


def find_by_user_name(user_name: str, exclude_id: int | None = None) -> dict[str, Any] | None:
    params: dict[str, Any] = {"user_name": user_name, "user_type": SUPPLIER_USER_TYPE}
    sql = """
        SELECT id FROM `user`
        WHERE userName = %(user_name)s AND userType = %(user_type)s
    """
    if exclude_id:
        sql += " AND id != %(exclude_id)s"
        params["exclude_id"] = exclude_id
    return fetch_one(sql + " LIMIT 1", params)


def find_by_company_name(company_name: str, exclude_id: int | None = None) -> dict[str, Any] | None:
    params: dict[str, Any] = {"company_name": company_name, "user_type": SUPPLIER_USER_TYPE}
    sql = """
        SELECT id FROM `user`
        WHERE company_name = %(company_name)s AND userType = %(user_type)s
    """
    if exclude_id:
        sql += " AND id != %(exclude_id)s"
        params["exclude_id"] = exclude_id
    return fetch_one(sql + " LIMIT 1", params)


def insert_supplier(data: dict[str, Any]) -> int:
    password = data.get("password") or "123456"
    return execute_insert(
        """
        INSERT INTO `user`
            (userName, company_name, trueName, mobile, address, area_info, company_code,
             email, area_id, city, province, address_info, userType, password,
             deleteStatus, addTime, status)
        VALUES
            (%(userName)s, %(company_name)s, %(trueName)s, %(mobile)s, %(address)s,
             %(area_info)s, %(company_code)s, %(email)s, %(area_id)s, %(city)s,
             %(province)s, %(address_info)s, %(user_type)s, %(password)s, 0, NOW(), 1)
        """,
        {
            "userName": data.get("userName") or "",
            "company_name": data.get("company_name") or "",
            "trueName": data.get("trueName") or "",
            "mobile": data.get("mobile") or "",
            "address": data.get("address") or "",
            "area_info": data.get("area_info") or data.get("areaInfo"),
            "company_code": data.get("company_code") or data.get("companyCode"),
            "email": data.get("email"),
            "area_id": data.get("area_id") or data.get("areaId"),
            "city": data.get("city"),
            "province": data.get("province"),
            "address_info": data.get("address_info") or data.get("addreddInfo"),
            "user_type": SUPPLIER_USER_TYPE,
            "password": encrypt_password_for_storage(password),
        },
    )


def update_supplier(supplier_id: int, data: dict[str, Any]) -> None:
    # address：有传则更新；未传则保留原值，避免编辑弹窗清空区划 ID
    existing = fetch_one(
        "SELECT address, city, province FROM `user` WHERE id = %(id)s AND userType = %(user_type)s",
        {"id": supplier_id, "user_type": SUPPLIER_USER_TYPE},
    ) or {}
    address = data.get("address")
    if address in (None, ""):
        address = existing.get("address") or ""
    city = data.get("city")
    if city in (None, ""):
        city = existing.get("city")
    province = data.get("province")
    if province in (None, ""):
        province = existing.get("province")
    execute(
        """
        UPDATE `user`
        SET userName = %(userName)s,
            company_name = %(company_name)s,
            trueName = %(trueName)s,
            mobile = %(mobile)s,
            address = %(address)s,
            area_info = %(area_info)s,
            company_code = %(company_code)s,
            email = %(email)s,
            area_id = %(area_id)s,
            city = %(city)s,
            province = %(province)s,
            address_info = %(address_info)s
        WHERE id = %(id)s AND userType = %(user_type)s
        """,
        {
            "id": supplier_id,
            "userName": data.get("userName") or "",
            "company_name": data.get("company_name") or "",
            "trueName": data.get("trueName") or "",
            "mobile": data.get("mobile") or "",
            "address": address,
            "area_info": data.get("area_info") or data.get("areaInfo"),
            "company_code": data.get("company_code") or data.get("companyCode"),
            "email": data.get("email"),
            "area_id": data.get("area_id") or data.get("areaId"),
            "city": city,
            "province": province,
            "address_info": data.get("address_info") or data.get("addreddInfo"),
            "user_type": SUPPLIER_USER_TYPE,
        },
    )


def toggle_supplier_status(supplier_id: int) -> None:
    row = fetch_one(
        "SELECT deleteStatus FROM `user` WHERE id = %(id)s AND userType = %(user_type)s",
        {"id": supplier_id, "user_type": SUPPLIER_USER_TYPE},
    )
    if not row:
        return
    current = bool(row.get("deleteStatus"))
    execute(
        "UPDATE `user` SET deleteStatus = %(status)s WHERE id = %(id)s",
        {"id": supplier_id, "status": 0 if current else 1},
    )


def _district_label(address: Any) -> Any:
    """address 存区划 ID（可为非纯数字），解析为可读地名。"""
    if address in (None, ""):
        return address
    aid = str(address).strip()
    dist = fetch_one(
        "SELECT id, dis_name, superId FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": aid},
    )
    if not dist:
        return address
    name = dist.get("dis_name") or ""
    super_id = dist.get("superId")
    if super_id:
        parent = fetch_one(
            "SELECT dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
            {"id": str(super_id)},
        )
        parent_name = (parent or {}).get("dis_name") or ""
        if parent_name and name:
            return f"{parent_name}/{name}"
        if parent_name:
            return parent_name
    return name or address


def _normalize_supplier(row: dict[str, Any]) -> dict[str, Any]:
    area_info = row.get("area_info")
    area_name = ""
    if area_info:
        area_row = fetch_one(
            "SELECT areaName FROM trans_area WHERE id = %(id)s LIMIT 1",
            {"id": area_info},
        )
        area_name = area_row.get("areaName") if area_row else ""
    address = row.get("address")
    address_label = _district_label(address)
    detail = row.get("address_info")
    if detail and address_label and str(address_label) != str(address):
        # 有区划名时，列表可附带详细地址（若存在）
        pass
    return {
        "id": row.get("id"),
        "userName": row.get("userName"),
        "companyName": row.get("company_name"),
        "company_name": row.get("company_name"),
        "trueName": row.get("trueName"),
        "mobile": row.get("mobile"),
        "address": address,
        "addressLabel": address_label if address_label not in (None, "") else (detail or address),
        "areaInfo": area_info,
        "areaName": area_name,
        "companyCode": row.get("company_code"),
        "company_code": row.get("company_code"),
        "addTime": row.get("addTime"),
        "deleteStatus": bool(row.get("deleteStatus")),
        "email": row.get("email"),
        "areaId": row.get("area_id"),
        "city": row.get("city"),
        "province": row.get("province"),
        "addressInfo": detail,
    }
