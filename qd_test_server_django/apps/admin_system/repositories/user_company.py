from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _district_name(district_id: Any) -> str:
    if district_id in (None, ""):
        return ""
    row = fetch_one(
        "SELECT dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": str(district_id)},
    )
    return str(row.get("dis_name") or "") if row else ""


def _district_chain(area_id: Any) -> dict[str, Any]:
    """area(县) → city → province，返回 id 与名称。"""
    result = {
        "areaId": str(area_id) if area_id not in (None, "") else "",
        "areaName": "",
        "cityId": "",
        "cityName": "",
        "provinceId": "",
        "provinceName": "",
    }
    if not result["areaId"]:
        return result
    area = fetch_one(
        "SELECT id, super_id, dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": result["areaId"]},
    )
    if not area:
        return result
    result["areaName"] = str(area.get("dis_name") or "")
    city_id = area.get("super_id")
    if city_id in (None, ""):
        return result
    city = fetch_one(
        "SELECT id, super_id, dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": str(city_id)},
    )
    if not city:
        return result
    result["cityId"] = str(city.get("id") or "")
    result["cityName"] = str(city.get("dis_name") or "")
    province_id = city.get("super_id")
    if province_id in (None, ""):
        return result
    province = fetch_one(
        "SELECT id, dis_name FROM sy_district WHERE id = %(id)s LIMIT 1",
        {"id": str(province_id)},
    )
    if not province:
        return result
    result["provinceId"] = str(province.get("id") or "")
    result["provinceName"] = str(province.get("dis_name") or "")
    return result


def list_companies(
    *,
    name: str = "",
    country: str = "",
    province: str = "",
    city: str = "",
    area_id: str = "",
    company_type: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE u.delete_status = 0"
    params: dict[str, Any] = {}
    if name:
        where += " AND u.name LIKE %(name)s"
        params["name"] = f"%{name}%"
    if country:
        where += " AND u.country = %(country)s"
        params["country"] = country
    if province:
        where += " AND c.super_id = %(province)s"
        params["province"] = province
    if city:
        where += " AND c.id = %(city)s"
        params["city"] = city
    if area_id:
        where += " AND u.area_id = %(area_id)s"
        params["area_id"] = area_id
    if company_type not in (None, ""):
        # Java list page type=3 → type in (1,3)
        if str(company_type) == "3":
            where += " AND u.type IN (1, 3)"
        else:
            where += " AND u.type = %(type)s"
            params["type"] = company_type

    join_sql = """
        FROM qd_user_company u
        LEFT JOIN sy_district d ON u.area_id = d.id
        LEFT JOIN sy_district c ON d.super_id = c.id
    """
    total = int(scalar(f"SELECT COUNT(*) {join_sql} {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.name, u.en_name, u.country, u.area_id, u.taxNum, u.bank, u.bankCardNum,
            u.address, u.contract_phone, u.contract_people, u.depts, u.add_time, u.type
        {join_sql}
        {where}
        ORDER BY u.add_time DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_company_list(row) for row in rows], total


def get_company(company_id: int, *, display_names: bool = False) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            u.id, u.name, u.en_name, u.country, u.area_id, u.taxNum, u.bank, u.bankCardNum,
            u.address, u.contract_phone, u.contract_people, u.depts, u.add_time, u.type,
            u.company_prop
        FROM qd_user_company u
        WHERE u.id = %(id)s
        LIMIT 1
        """,
        {"id": company_id},
    )
    if not row:
        return None
    return _normalize_company(row, display_names=display_names)


def name_exists(name: str, exclude_id: int | None = None) -> bool:
    sql = "SELECT COUNT(*) FROM qd_user_company WHERE delete_status = 0 AND name = %(name)s"
    params: dict[str, Any] = {"name": name}
    if exclude_id:
        sql += " AND id <> %(id)s"
        params["id"] = exclude_id
    return int(scalar(sql, params) or 0) > 0


def insert_company(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO qd_user_company
            (name, en_name, country, area_id, taxNum, bank, bankCardNum, address,
             contract_phone, contract_people, depts, company_prop, add_time, delete_status, type)
        VALUES
            (%(name)s, %(en_name)s, %(country)s, %(area_id)s, %(taxNum)s, %(bank)s,
             %(bankCardNum)s, %(address)s, %(contract_phone)s, %(contract_people)s,
             %(depts)s, %(company_prop)s, NOW(), 0, %(type)s)
        """,
        {
            "name": data.get("name") or "",
            "en_name": data.get("enName") or data.get("en_name"),
            "country": data.get("country"),
            "area_id": data.get("areaId") or data.get("area_id"),
            "taxNum": data.get("taxNum"),
            "bank": data.get("bank"),
            "bankCardNum": data.get("bankCardNum"),
            "address": data.get("address"),
            "contract_phone": data.get("contractPhone") or data.get("contract_phone"),
            "contract_people": data.get("contractPeople") or data.get("contract_people"),
            "depts": data.get("depts"),
            "company_prop": data.get("companyProp") or data.get("company_prop"),
            "type": data.get("type") or 3,
        },
    )


def update_company(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE qd_user_company
        SET name = %(name)s,
            en_name = %(en_name)s,
            country = %(country)s,
            area_id = %(area_id)s,
            taxNum = %(taxNum)s,
            bank = %(bank)s,
            bankCardNum = %(bankCardNum)s,
            address = %(address)s,
            contract_phone = %(contract_phone)s,
            contract_people = %(contract_people)s,
            depts = %(depts)s,
            company_prop = %(company_prop)s,
            modify_time = NOW()
        WHERE id = %(id)s
        """,
        {
            "id": data.get("id"),
            "name": data.get("name") or "",
            "en_name": data.get("enName") or data.get("en_name"),
            "country": data.get("country"),
            "area_id": data.get("areaId") or data.get("area_id"),
            "taxNum": data.get("taxNum"),
            "bank": data.get("bank"),
            "bankCardNum": data.get("bankCardNum"),
            "address": data.get("address"),
            "contract_phone": data.get("contractPhone") or data.get("contract_phone"),
            "contract_people": data.get("contractPeople") or data.get("contract_people"),
            "depts": data.get("depts"),
            "company_prop": data.get("companyProp") or data.get("company_prop"),
        },
    )


def soft_delete_company(company_id: int) -> None:
    execute(
        "UPDATE qd_user_company SET delete_status = 1, modify_time = NOW() WHERE id = %(id)s",
        {"id": company_id},
    )


def unbind_company_users(company_id: int) -> None:
    execute(
        """
        UPDATE exp_user
        SET parent_id = NULL, userType = 1, company_name = NULL
        WHERE parent_id = %(id)s AND deleteStatus = 0
        """,
        {"id": company_id},
    )


def _normalize_company_list(row: dict[str, Any]) -> dict[str, Any]:
    """列表接口：与 Java 一致，country/province/city/areaId 填地区名称。"""
    chain = _district_chain(row.get("area_id"))
    country_name = _district_name(row.get("country"))
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "enName": row.get("en_name"),
        "country": country_name or row.get("country"),
        "province": chain["provinceName"],
        "city": chain["cityName"],
        "areaId": chain["areaName"],
        "address": row.get("address"),
        "taxNum": row.get("taxNum"),
        "bank": row.get("bank"),
        "bankCardNum": row.get("bankCardNum"),
        "contractPhone": row.get("contract_phone"),
        "contractPeople": row.get("contract_people"),
        "depts": row.get("depts"),
        "addTime": row.get("add_time"),
        "type": row.get("type"),
    }


def _normalize_company(row: dict[str, Any], *, display_names: bool = False) -> dict[str, Any]:
    chain = _district_chain(row.get("area_id"))
    country_id = row.get("country")
    country_name = _district_name(country_id)
    if display_names:
        return {
            "id": row.get("id"),
            "name": row.get("name"),
            "enName": row.get("en_name"),
            "country": country_name or country_id,
            "province": chain["provinceName"],
            "city": chain["cityName"],
            "areaId": chain["areaName"],
            "address": row.get("address"),
            "taxNum": row.get("taxNum"),
            "bank": row.get("bank"),
            "bankCardNum": row.get("bankCardNum"),
            "contractPhone": row.get("contract_phone"),
            "contractPeople": row.get("contract_people"),
            "depts": row.get("depts"),
            "companyProp": row.get("company_prop"),
            "addTime": row.get("add_time"),
            "type": row.get("type"),
        }
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "enName": row.get("en_name"),
        "country": country_id,
        "countryName": country_name,
        "areaId": row.get("area_id"),
        "areaName": chain["areaName"],
        "cityId": chain["cityId"],
        "city": chain["cityName"],
        "provinceId": chain["provinceId"],
        "province": chain["provinceName"],
        "taxNum": row.get("taxNum"),
        "bank": row.get("bank"),
        "bankCardNum": row.get("bankCardNum"),
        "address": row.get("address"),
        "contractPhone": row.get("contract_phone"),
        "contractPeople": row.get("contract_people"),
        "depts": row.get("depts"),
        "companyProp": row.get("company_prop"),
        "addTime": row.get("add_time"),
        "type": row.get("type"),
    }
