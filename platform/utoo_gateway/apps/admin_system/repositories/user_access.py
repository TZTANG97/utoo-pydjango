from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one


def list_access_companies() -> list[dict[str, Any]]:
    """对齐 Java getAllCompanyAndUserType(公司账号)。"""
    sql_full = """
        SELECT t.id, t.company_name AS companyName, t.userName, t.trueName
        FROM `user` t
        INNER JOIN sy_users u ON t.syuser_id = u.id
        WHERE t.userType = '6'
          AND (t.deleteStatus = 0 OR t.deleteStatus IS NULL)
          AND (
            u.type = '公司账号'
            OR u.utoo_type = '公司账号'
            OR u.amk_type = '公司账号'
          )
        ORDER BY t.company_name ASC, t.id ASC
    """
    sql_fallback = """
        SELECT t.id, t.company_name AS companyName, t.userName, t.trueName
        FROM `user` t
        INNER JOIN sy_users u ON t.syuser_id = u.id
        WHERE t.userType = '6'
          AND (t.deleteStatus = 0 OR t.deleteStatus IS NULL)
          AND (u.type = '公司账号' OR u.utoo_type = '公司账号')
        ORDER BY t.company_name ASC, t.id ASC
    """
    try:
        rows = fetch_all(sql_full)
    except Exception:
        try:
            rows = fetch_all(sql_fallback)
        except Exception:
            rows = []
    return [
        {
            "id": r.get("id"),
            "companyName": r.get("companyName") or r.get("userName") or r.get("trueName") or str(r.get("id")),
        }
        for r in rows
    ]


def list_access_order_types() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, type_name AS typeName, type_desc AS typeDesc
        FROM order_type
        WHERE deleteStatus = 0 AND pt_type LIKE %(pt)s
        ORDER BY type_sort ASC, id ASC
        """,
        {"pt": "%2%"},
    )
    return [{"id": r.get("id"), "typeName": r.get("typeName") or str(r.get("id"))} for r in rows]


def list_access_sale_users() -> list[dict[str, Any]]:
    """对齐 Java queryUsersAccess。"""
    rows = fetch_all(
        """
        SELECT t.id, t.user_name AS userName, t.true_name AS trueName, t.utoo_type AS utooType
        FROM sy_users t
        WHERE t.pt_type LIKE %(pt)s
          AND t.utoo_type IN (
            SELECT sut.type_name
            FROM sy_user_type sut
            LEFT JOIN user_type_role utr ON utr.id = sut.role_id
            WHERE utr.name IN ('销售主管', 'A类销售人员', 'C类销售人员', 'H类用户')
          )
        ORDER BY t.true_name ASC, t.user_name ASC
        """,
        {"pt": "%2%"},
    )
    return [
        {
            "id": r.get("id"),
            "userName": r.get("userName"),
            "trueName": r.get("trueName"),
            "label": f"{r.get('trueName') or ''}（{r.get('userName') or ''}）".strip("（）"),
        }
        for r in rows
    ]


def find_company_ids(user_id: str) -> list[str]:
    rows = fetch_all(
        """
        SELECT company_id
        FROM sy_user_company
        WHERE deleteStatus = 0 AND pt_type = '2' AND user_id = %(user_id)s
        """,
        {"user_id": user_id},
    )
    return [str(r["company_id"]) for r in rows if r.get("company_id") is not None]


def find_order_type_ids(user_id: str) -> list[str]:
    rows = fetch_all(
        """
        SELECT type_id
        FROM sy_user_ordertype
        WHERE deleteStatus = 0 AND pt_type = '2' AND user_id = %(user_id)s
        """,
        {"user_id": user_id},
    )
    return [str(r["type_id"]) for r in rows if r.get("type_id") is not None]


def find_sale_user_ids(user_id: str) -> list[str]:
    rows = fetch_all(
        """
        SELECT saleuser_id
        FROM sy_user_saleuser
        WHERE deleteStatus = 0 AND pt_type = '2' AND user_id = %(user_id)s
        """,
        {"user_id": user_id},
    )
    return [str(r["saleuser_id"]) for r in rows if r.get("saleuser_id")]


def get_access_rights(user_id: str) -> dict[str, Any]:
    return {
        "companys": list_access_companies(),
        "hasCompanys": find_company_ids(user_id),
        "types": list_access_order_types(),
        "hasTypes": find_order_type_ids(user_id),
        "saleUsers": list_access_sale_users(),
        "userInfo": find_sale_user_ids(user_id),
    }


def _ids(raw: list[str] | None) -> list[str]:
    out: list[str] = []
    for item in raw or []:
        s = str(item).strip()
        if s and s not in out:
            out.append(s)
    return out


def update_user_companies(user_id: str, company_ids: list[str]) -> None:
    wanted = set(_ids(company_ids))
    current = set(find_company_ids(user_id))
    for cid in wanted - current:
        execute_insert(
            """
            INSERT INTO sy_user_company (addTime, deleteStatus, company_id, user_id, pt_type)
            VALUES (NOW(), 0, %(company_id)s, %(user_id)s, '2')
            """,
            {"company_id": cid, "user_id": user_id},
        )
    for cid in current - wanted:
        execute(
            """
            DELETE FROM sy_user_company
            WHERE user_id = %(user_id)s AND company_id = %(company_id)s AND pt_type = '2'
            """,
            {"user_id": user_id, "company_id": cid},
        )


def update_user_order_types(user_id: str, type_ids: list[str]) -> None:
    wanted = set(_ids(type_ids))
    current = set(find_order_type_ids(user_id))
    for tid in wanted - current:
        execute_insert(
            """
            INSERT INTO sy_user_ordertype (addTime, deleteStatus, type_id, user_id, pt_type)
            VALUES (NOW(), 0, %(type_id)s, %(user_id)s, '2')
            """,
            {"type_id": tid, "user_id": user_id},
        )
    for tid in current - wanted:
        execute(
            """
            DELETE FROM sy_user_ordertype
            WHERE user_id = %(user_id)s AND type_id = %(type_id)s AND pt_type = '2'
            """,
            {"user_id": user_id, "type_id": tid},
        )


def update_user_sale_users(user_id: str, sale_user_ids: list[str]) -> None:
    wanted = set(_ids(sale_user_ids))
    current = set(find_sale_user_ids(user_id))
    for sid in wanted - current:
        execute_insert(
            """
            INSERT INTO sy_user_saleuser (addTime, deleteStatus, saleuser_id, user_id, pt_type)
            VALUES (NOW(), 0, %(saleuser_id)s, %(user_id)s, '2')
            """,
            {"saleuser_id": sid, "user_id": user_id},
        )
    for sid in current - wanted:
        execute(
            """
            DELETE FROM sy_user_saleuser
            WHERE user_id = %(user_id)s AND saleuser_id = %(saleuser_id)s AND pt_type = '2'
            """,
            {"user_id": user_id, "saleuser_id": sid},
        )


def update_access_rights(
    user_id: str,
    *,
    company_ids: list[str],
    order_type_ids: list[str],
    sale_user_ids: list[str],
) -> None:
    update_user_companies(user_id, company_ids)
    update_user_order_types(user_id, order_type_ids)
    update_user_sale_users(user_id, sale_user_ids)


def list_available_exp_projects(user_id: str) -> list[dict[str, Any]]:
    """未关联的 type=3 项目，对齐 selExpProject。"""
    rows = fetch_all(
        """
        SELECT t.id, t.name
        FROM experiment_manage t
        WHERE t.type = 3
          AND (t.deleteStatus = 0 OR t.deleteStatus IS NULL)
          AND t.id NOT IN (
            SELECT m.exp_manage_id FROM sy_user_expmanage m
            WHERE m.user_id = %(user_id)s AND m.exp_manage_id IS NOT NULL
          )
        ORDER BY t.name ASC, t.id ASC
        """,
        {"user_id": user_id},
    )
    return [{"id": r.get("id"), "name": r.get("name") or str(r.get("id"))} for r in rows]


def list_user_exp_projects(user_id: str) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT t.id, t.exp_manage_id AS expManageId, m.name AS emname
        FROM sy_user_expmanage t
        LEFT JOIN experiment_manage m ON t.exp_manage_id = m.id
        WHERE t.user_id = %(user_id)s
        ORDER BY t.id DESC
        """,
        {"user_id": user_id},
    )
    return [
        {
            "id": r.get("id"),
            "expManageId": r.get("expManageId"),
            "emname": r.get("emname") or "",
        }
        for r in rows
    ]


def add_user_exp_manage(user_id: str, exp_manage_id: int | str) -> dict[str, Any] | None:
    exists = fetch_one(
        """
        SELECT id FROM sy_user_expmanage
        WHERE user_id = %(user_id)s AND exp_manage_id = %(exp_manage_id)s
        LIMIT 1
        """,
        {"user_id": user_id, "exp_manage_id": exp_manage_id},
    )
    if exists:
        em = fetch_one(
            "SELECT name FROM experiment_manage WHERE id = %(id)s",
            {"id": exp_manage_id},
        )
        return {
            "emid": exists.get("id"),
            "emname": (em or {}).get("name") or "",
        }
    row_id = execute_insert(
        """
        INSERT INTO sy_user_expmanage (addTime, deleteStatus, exp_manage_id, user_id)
        VALUES (NOW(), 0, %(exp_manage_id)s, %(user_id)s)
        """,
        {"exp_manage_id": exp_manage_id, "user_id": user_id},
    )
    em = fetch_one(
        "SELECT name FROM experiment_manage WHERE id = %(id)s",
        {"id": exp_manage_id},
    )
    return {"emid": row_id, "emname": (em or {}).get("name") or ""}


def delete_user_exp_manage(row_id: int | str) -> None:
    execute("DELETE FROM sy_user_expmanage WHERE id = %(id)s", {"id": row_id})
