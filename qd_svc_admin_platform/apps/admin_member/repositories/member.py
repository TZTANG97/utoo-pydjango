from __future__ import annotations

from typing import Any

from apps.admin_member.helpers import page_clause
from apps.admin_system.repositories.user_company import _district_chain
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_members(
    *,
    true_name: str = "",
    company_name: str = "",
    mobile: str = "",
    province: str = "",
    city: str = "",
    area_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE u.deleteStatus = 0"
    params: dict[str, Any] = {}
    if true_name:
        where += " AND u.trueName LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if company_name:
        where += " AND u.company_name LIKE %(company_name)s"
        params["company_name"] = f"%{company_name}%"
    if mobile:
        where += " AND u.mobile LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    if province:
        where += " AND c.super_id = %(province)s"
        params["province"] = province
    if city:
        where += " AND c.id = %(city)s"
        params["city"] = city
    if area_id:
        where += " AND u.area_id = %(area_id)s"
        params["area_id"] = area_id

    join_sql = """
        FROM exp_user u
        LEFT JOIN sy_district d ON u.area_id = d.id
        LEFT JOIN sy_district c ON d.super_id = c.id
        LEFT JOIN user_account ua ON ua.user_id = u.id AND ua.delete_status = 0
    """
    total = int(scalar(f"SELECT COUNT(*) {join_sql} {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.addTime, u.userName, u.trueName, u.mobile, u.email, u.idcard,
            u.company_name, u.company_name AS companyName, u.userType,
            u.parent_id AS parentId, u.area_id AS areaId, u.address_info AS addreddInfo,
            u.is_accept_message AS isAcceptMessage, ua.amount
        {join_sql}
        {where}
        ORDER BY u.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_list_row(row) for row in rows], total


def get_member(user_id: int, *, display_names: bool = False) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            u.id, u.addTime, u.userName, u.trueName, u.mobile, u.email, u.idcard,
            u.company_name, u.company_name AS companyName, u.userType,
            u.parent_id AS parentId, u.area_id AS areaId, u.address_info AS addreddInfo,
            u.is_accept_message AS isAcceptMessage,
            u.dept, u.job, u.telephone, u.extension, u.zipCode,
            ua.amount, ua.arrear_amount AS arrearAmount
        FROM exp_user u
        LEFT JOIN user_account ua ON ua.user_id = u.id AND ua.delete_status = 0
        WHERE u.id = %(id)s
        LIMIT 1
        """,
        {"id": user_id},
    )
    if not row:
        return None
    return _normalize_detail_row(row, display_names=display_names)


def companies_by_phone(mobile: str) -> list[dict[str, Any]]:
    if not mobile:
        return []
    return fetch_all(
        """
        SELECT id, name, contract_phone AS contractPhone
        FROM qd_user_company
        WHERE delete_status = 0 AND contract_phone = %(mobile)s
        ORDER BY id DESC
        """,
        {"mobile": mobile},
    )


def mobile_exists(mobile: str, exclude_id: int | None = None) -> bool:
    sql = "SELECT COUNT(*) FROM exp_user WHERE deleteStatus = 0 AND mobile = %(mobile)s"
    params: dict[str, Any] = {"mobile": mobile}
    if exclude_id:
        sql += " AND id <> %(id)s"
        params["id"] = exclude_id
    return int(scalar(sql, params) or 0) > 0


def username_exists(user_name: str, exclude_id: int | None = None) -> bool:
    sql = "SELECT COUNT(*) FROM exp_user WHERE deleteStatus = 0 AND userName = %(user_name)s"
    params: dict[str, Any] = {"user_name": user_name}
    if exclude_id:
        sql += " AND id <> %(id)s"
        params["id"] = exclude_id
    return int(scalar(sql, params) or 0) > 0


def insert_member(fields: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO exp_user
            (addTime, deleteStatus, userName, password, trueName, mobile, email, idcard,
             company_name, userType, parent_id, area_id, address_info, is_accept_message,
             dept, job, telephone, extension, zipCode)
        VALUES
            (NOW(), 0, %(userName)s, %(password)s, %(trueName)s, %(mobile)s, %(email)s, %(idcard)s,
             %(company_name)s, %(userType)s, %(parent_id)s, %(area_id)s, %(addreddInfo)s, %(is_accept_message)s,
             %(dept)s, %(job)s, %(telephone)s, %(extension)s, %(zipCode)s)
        """,
        {
            "userName": fields.get("userName"),
            "password": fields.get("password"),
            "trueName": fields.get("trueName"),
            "mobile": fields.get("mobile"),
            "email": fields.get("email"),
            "idcard": fields.get("idcard"),
            "company_name": fields.get("company_name"),
            "userType": fields.get("userType"),
            "parent_id": fields.get("parent_id"),
            "area_id": fields.get("area_id"),
            "addreddInfo": fields.get("addreddInfo"),
            "is_accept_message": fields.get("is_accept_message") or 0,
            "dept": fields.get("dept"),
            "job": fields.get("job"),
            "telephone": fields.get("telephone"),
            "extension": fields.get("extension"),
            "zipCode": fields.get("zipCode"),
        },
    )


def update_member(user_id: int, fields: dict[str, Any]) -> None:
    execute(
        """
        UPDATE exp_user
        SET trueName = %(trueName)s,
            mobile = %(mobile)s,
            email = %(email)s,
            idcard = %(idcard)s,
            company_name = %(company_name)s,
            area_id = %(area_id)s,
            address_info = %(addreddInfo)s,
            is_accept_message = %(is_accept_message)s,
            dept = %(dept)s,
            job = %(job)s,
            telephone = %(telephone)s,
            extension = %(extension)s,
            zipCode = %(zipCode)s,
            parent_id = COALESCE(%(parent_id)s, parent_id),
            userType = COALESCE(%(userType)s, userType)
        WHERE id = %(id)s
        """,
        {
            "id": user_id,
            "trueName": fields.get("trueName"),
            "mobile": fields.get("mobile"),
            "email": fields.get("email"),
            "idcard": fields.get("idcard"),
            "company_name": fields.get("company_name"),
            "area_id": fields.get("area_id"),
            "addreddInfo": fields.get("addreddInfo"),
            "is_accept_message": fields.get("is_accept_message") or 0,
            "dept": fields.get("dept"),
            "job": fields.get("job"),
            "telephone": fields.get("telephone"),
            "extension": fields.get("extension"),
            "zipCode": fields.get("zipCode"),
            "parent_id": fields.get("parent_id"),
            "userType": fields.get("userType"),
        },
    )


def unbind_member(user_id: int) -> None:
    execute(
        """
        UPDATE exp_user
        SET parent_id = NULL, userType = 1, company_name = NULL
        WHERE id = %(id)s
        """,
        {"id": user_id},
    )


def bind_member(*, user_id: int, parent_id: int, company_name: str) -> None:
    execute(
        """
        UPDATE exp_user
        SET parent_id = %(parent_id)s, userType = 2, company_name = %(company_name)s
        WHERE id = %(id)s
        """,
        {"id": user_id, "parent_id": parent_id, "company_name": company_name},
    )


def list_picker(*, mobile: str = "", page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE u.deleteStatus = 0"
    params: dict[str, Any] = {}
    if mobile:
        where += " AND u.mobile LIKE %(mobile)s"
        params["mobile"] = f"%{mobile}%"
    total = int(scalar(f"SELECT COUNT(*) FROM exp_user u {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.userName, u.trueName, u.mobile,
            u.company_name AS companyName,
            u.company_name,
            IFNULL(a.amount, 0) AS ye
        FROM exp_user u
        LEFT JOIN user_account a ON u.id = a.user_id AND IFNULL(a.delete_status, 0) = 0
        {where}
        ORDER BY u.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def _normalize_list_row(row: dict[str, Any]) -> dict[str, Any]:
    chain = _district_chain(row.get("areaId"))
    return {
        "id": row.get("id"),
        "addTime": row.get("addTime"),
        "userName": row.get("userName"),
        "trueName": row.get("trueName"),
        "mobile": row.get("mobile"),
        "email": row.get("email"),
        "idcard": row.get("idcard"),
        "company_name": row.get("company_name"),
        "companyName": row.get("companyName") or row.get("company_name"),
        "userType": row.get("userType"),
        "parentId": row.get("parentId"),
        "areaId": row.get("areaId"),
        "areaInfo": chain["areaName"],
        "province": chain["provinceName"],
        "city": chain["cityName"],
        "addreddInfo": row.get("addreddInfo"),
        "isAcceptMessage": row.get("isAcceptMessage"),
        "amount": row.get("amount"),
    }


def _normalize_detail_row(row: dict[str, Any], *, display_names: bool = False) -> dict[str, Any]:
    chain = _district_chain(row.get("areaId"))
    base = {
        "id": row.get("id"),
        "addTime": row.get("addTime"),
        "userName": row.get("userName"),
        "trueName": row.get("trueName"),
        "mobile": row.get("mobile"),
        "email": row.get("email"),
        "idcard": row.get("idcard"),
        "company_name": row.get("company_name"),
        "companyName": row.get("companyName") or row.get("company_name"),
        "userType": row.get("userType"),
        "parentId": row.get("parentId"),
        "addreddInfo": row.get("addreddInfo"),
        "is_accept_message": row.get("isAcceptMessage"),
        "isAcceptMessage": row.get("isAcceptMessage"),
        "dept": row.get("dept"),
        "job": row.get("job"),
        "telephone": row.get("telephone"),
        "extension": row.get("extension"),
        "zipCode": row.get("zipCode"),
        "amount": row.get("amount"),
        "arrearAmount": row.get("arrearAmount"),
    }
    if display_names:
        base.update(
            {
                "areaId": row.get("areaId"),
                "areaInfo": chain["areaName"],
                "province": chain["provinceName"],
                "city": chain["cityName"],
                "provinceId": chain["provinceId"],
                "cityId": chain["cityId"],
            }
        )
    else:
        base.update(
            {
                "areaId": row.get("areaId"),
                "areaInfo": chain["areaName"],
                "province": chain["provinceName"],
                "city": chain["cityName"],
                "provinceId": chain["provinceId"],
                "cityId": chain["cityId"],
            }
        )
    return base
