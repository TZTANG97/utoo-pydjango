from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def _user_names(lab_userid: str) -> str:
    ids = [x.strip() for x in str(lab_userid or "").split(",") if x.strip()]
    if not ids:
        return ""
    placeholders = []
    params: dict[str, Any] = {}
    for i, uid in enumerate(ids):
        key = f"u{i}"
        placeholders.append(f"%({key})s")
        params[key] = uid
    rows = fetch_all(
        f"""
        SELECT id, user_name AS userName, true_name AS trueName
        FROM sy_users
        WHERE id IN ({', '.join(placeholders)})
        """,
        params,
    )
    by_id = {str(r["id"]): r for r in rows}
    names = []
    for uid in ids:
        u = by_id.get(uid)
        if not u:
            continue
        uname = str(u.get("userName") or "")
        tname = str(u.get("trueName") or "")
        names.append(f"{uname} {tname}".strip() if tname else uname)
    return "，".join(names)


def list_labs(
    *,
    lab_name: str = "",
    lab_num: str = "",
    lab_userid: str = "",
    country: str = "",
    province: str = "",
    city: str = "",
    area_id: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0"
    params: dict[str, Any] = {}
    if lab_name:
        where += " AND t.lab_name LIKE %(lab_name)s"
        params["lab_name"] = f"%{lab_name}%"
    if lab_num:
        where += " AND t.lab_num LIKE %(lab_num)s"
        params["lab_num"] = f"%{lab_num}%"
    if lab_userid:
        where += " AND FIND_IN_SET(%(lab_userid)s, REPLACE(IFNULL(t.lab_userid,''), ' ', '')) > 0"
        params["lab_userid"] = lab_userid
    if country:
        where += " AND t.country = %(country)s"
        params["country"] = country
    if area_id:
        where += " AND t.area_id = %(area_id)s"
        params["area_id"] = area_id
    elif city:
        # 选中市：包含该市下所有县/区
        where += """
          AND t.area_id IN (
            SELECT id FROM sy_district WHERE super_id = %(city)s
          )
        """
        params["city"] = city
    elif province:
        where += """
          AND t.area_id IN (
            SELECT c.id
            FROM sy_district c
            INNER JOIN sy_district city ON c.super_id = city.id
            WHERE city.super_id = %(province)s
          )
        """
        params["province"] = province

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_lab t
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
            t.id, t.addTime, t.lab_num AS labNum, t.lab_name AS labName,
            t.lab_userid AS labUserid, t.country, t.area_id AS areaId,
            t.address, t.status, t.syuser_id AS syuserId,
            county.dis_name AS areaName,
            city.dis_name AS cityName,
            province.dis_name AS provinceName,
            country_d.dis_name AS countryName
        FROM experiment_lab t
        LEFT JOIN sy_district county ON t.area_id = county.id
        LEFT JOIN sy_district city ON county.super_id = city.id
        LEFT JOIN sy_district province ON city.super_id = province.id
        LEFT JOIN sy_district country_d ON t.country = country_d.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        row["userName"] = _user_names(str(row.get("labUserid") or ""))
        row["trueName"] = row["userName"]
        # Java：status 1启用 2禁用
        st = int(row.get("status") or 0)
        row["statusLabel"] = "启用" if st == 1 else "禁用"
    return rows, total


def get_lab(lab_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.lab_num AS labNum, t.lab_name AS labName,
            t.lab_userid AS labUserid, t.country, t.area_id AS areaId,
            t.address, t.status, t.syuser_id AS syuserId,
            county.dis_name AS areaName,
            city.id AS cityId, city.dis_name AS cityName,
            province.id AS provinceId, province.dis_name AS provinceName,
            country_d.dis_name AS countryName
        FROM experiment_lab t
        LEFT JOIN sy_district county ON t.area_id = county.id
        LEFT JOIN sy_district city ON county.super_id = city.id
        LEFT JOIN sy_district province ON city.super_id = province.id
        LEFT JOIN sy_district country_d ON t.country = country_d.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": lab_id},
    )
    if row:
        row["userName"] = _user_names(str(row.get("labUserid") or ""))
        sy_id = str(row.get("syuserId") or "").strip()
        if sy_id:
            su = fetch_one(
                "SELECT user_name AS userName FROM sy_users WHERE id = %(id)s LIMIT 1",
                {"id": sy_id},
            )
            row["syUserName"] = str((su or {}).get("userName") or "")
        else:
            row["syUserName"] = ""
    return row


def insert_lab(data: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO experiment_lab
            (addTime, deleteStatus, lab_num, lab_name, lab_userid, country, area_id, address, status, syuser_id)
        VALUES
            (NOW(), 0, %(lab_num)s, %(lab_name)s, %(lab_userid)s, %(country)s, %(area_id)s, %(address)s, %(status)s, %(syuser_id)s)
        """,
        data,
    )


def update_lab(lab_id: int, data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE experiment_lab
        SET lab_num = %(lab_num)s,
            lab_name = %(lab_name)s,
            lab_userid = %(lab_userid)s,
            country = %(country)s,
            area_id = %(area_id)s,
            address = %(address)s,
            status = %(status)s,
            syuser_id = %(syuser_id)s
        WHERE id = %(id)s
        """,
        {**data, "id": lab_id},
    )


def set_lab_status(lab_id: int, status: int) -> None:
    execute(
        "UPDATE experiment_lab SET status = %(status)s WHERE id = %(id)s",
        {"id": lab_id, "status": status},
    )


def soft_delete_lab(lab_id: int) -> None:
    execute(
        "UPDATE experiment_lab SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": lab_id},
    )


def list_lab_filter_options() -> dict[str, Any]:
    """筛选下拉：实验室编号/名称、负责人、国家。"""
    nums = fetch_all(
        """
        SELECT DISTINCT lab_num AS value, lab_num AS label
        FROM experiment_lab
        WHERE IFNULL(deleteStatus, 0) = 0 AND IFNULL(lab_num, '') != ''
        ORDER BY lab_num ASC
        LIMIT 500
        """
    )
    names = fetch_all(
        """
        SELECT DISTINCT lab_name AS value, lab_name AS label
        FROM experiment_lab
        WHERE IFNULL(deleteStatus, 0) = 0 AND IFNULL(lab_name, '') != ''
        ORDER BY lab_name ASC
        LIMIT 500
        """
    )
    users = fetch_all(
        """
        SELECT DISTINCT u.id AS value,
               CONCAT(IFNULL(u.user_name,''), IF(IFNULL(u.true_name,'')='','', CONCAT(' ', u.true_name))) AS label
        FROM experiment_lab t
        INNER JOIN sy_users u ON FIND_IN_SET(u.id, REPLACE(IFNULL(t.lab_userid,''), ' ', '')) > 0
        WHERE IFNULL(t.deleteStatus, 0) = 0
        ORDER BY u.user_name ASC
        LIMIT 500
        """
    )
    countries = fetch_all(
        """
        SELECT d.id AS value, d.dis_name AS label
        FROM sy_district d
        WHERE d.id IN (
            SELECT DISTINCT country FROM experiment_lab
            WHERE IFNULL(deleteStatus, 0) = 0 AND IFNULL(country, '') != ''
        )
        ORDER BY d.dis_name ASC
        """
    )
    return {
        "labNums": nums,
        "labNames": names,
        "users": users,
        "countries": countries,
    }
