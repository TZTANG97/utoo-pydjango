"""青岛会员账号（user.userType=5），对齐 Java MemberController + UserMapper.listPageAdmin。"""

from __future__ import annotations

from typing import Any

from apps.admin_member.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar

MEMBER_USER_TYPE = 5
OSS_BASE = "https://qgongye.oss-cn-shanghai.aliyuncs.com/"


def _truthy(value: Any) -> bool:
    return value not in (None, "", 0, "0", False, "false", "False")


def _photo_url(path: Any, name: Any) -> str:
    p = str(path or "").strip().rstrip("/")
    n = str(name or "").strip().lstrip("/")
    if not p or not n:
        return ""
    if p.startswith("http://") or p.startswith("https://"):
        return p if p.endswith(n) else f"{p}/{n}"
    return f"{OSS_BASE}{p}/{n}"


def list_accounts(
    *,
    user_name: str = "",
    company_name: str = "",
    true_name: str = "",
    mobile: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # 对齐 Java listPageAdmin：不按 deleteStatus 过滤，禁用账号仍出现在列表
    where = "WHERE u.userType = %(user_type)s"
    params: dict[str, Any] = {"user_type": MEMBER_USER_TYPE}
    if user_name:
        where += " AND u.userName LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if company_name:
        where += " AND c.name LIKE %(company_name)s"
        params["company_name"] = f"%{company_name}%"
    if true_name:
        where += " AND u.trueName LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if mobile:
        where += " AND (u.mobile LIKE %(mobile)s OR u.telephone LIKE %(mobile)s)"
        params["mobile"] = f"%{mobile}%"

    join_sql = """
        FROM `user` u
        INNER JOIN qd_user_company c ON u.company_name = c.id
    """
    total = int(scalar(f"SELECT COUNT(*) {join_sql} {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.userName, u.trueName, u.mobile, u.email, u.telephone,
            u.status, u.deleteStatus, u.is_app_login, u.addTime,
            u.company_name AS companyId, u.cg_company_name AS cgCompanyId,
            c.name AS companyName, c.name AS parentName
        {join_sql}
        {where}
        ORDER BY u.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    result = []
    for row in rows:
        is_app_login = _truthy(row.get("is_app_login"))
        delete_status = _truthy(row.get("deleteStatus"))
        result.append(
            {
                "id": row.get("id"),
                "userName": row.get("userName"),
                "trueName": row.get("trueName"),
                "mobile": row.get("mobile") or row.get("telephone"),
                "telephone": row.get("telephone") or row.get("mobile"),
                "email": row.get("email"),
                "status": row.get("status"),
                "deleteStatus": 1 if delete_status else 0,
                "is_app_login": 1 if is_app_login else 0,
                "addTime": str(row.get("addTime") or "")[:19],
                "companyId": row.get("companyId"),
                "cgCompanyId": row.get("cgCompanyId"),
                "companyName": row.get("companyName"),
                "company_name": row.get("companyName"),
                "parent": {"id": row.get("companyId"), "name": row.get("companyName")},
                # 列表「是否可操作」对齐 Java is_app_login
                "operable": "是" if is_app_login else "否",
            }
        )
    return result, total


def get_account(account_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            u.id, u.userName, u.trueName, u.mobile, u.email, u.telephone,
            u.status, u.deleteStatus, u.is_app_login, u.addTime, u.password,
            u.company_name AS companyId, u.cg_company_name AS cgCompanyId,
            u.photo_id AS photoId,
            c.name AS companyName, cg.name AS cgCompanyName,
            a.path AS photoPath, a.name AS photoName
        FROM `user` u
        LEFT JOIN qd_user_company c ON u.company_name = c.id
        LEFT JOIN qd_user_company cg ON u.cg_company_name = cg.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE u.id = %(id)s AND u.userType = %(user_type)s
        LIMIT 1
        """,
        {"id": account_id, "user_type": MEMBER_USER_TYPE},
    )
    if not row:
        return None
    is_app_login = _truthy(row.get("is_app_login"))
    photo_url = _photo_url(row.get("photoPath"), row.get("photoName"))
    return {
        "id": row.get("id"),
        "userName": row.get("userName"),
        "trueName": row.get("trueName"),
        "mobile": row.get("mobile"),
        "telephone": row.get("telephone") or row.get("mobile"),
        "email": row.get("email"),
        "status": row.get("status"),
        "deleteStatus": 1 if _truthy(row.get("deleteStatus")) else 0,
        "is_app_login": 1 if is_app_login else 0,
        "addTime": str(row.get("addTime") or "")[:19],
        "companyId": row.get("companyId"),
        "company_name": row.get("companyId"),
        "companyName": row.get("companyName"),
        "cgCompanyId": row.get("cgCompanyId"),
        "cg_company_name": row.get("cgCompanyId"),
        "cgCompanyName": row.get("cgCompanyName"),
        "photoId": row.get("photoId"),
        "photo_id": row.get("photoId"),
        "photoUrl": photo_url,
        "parent": {"id": row.get("companyId"), "name": row.get("companyName")},
    }


def username_exists(user_name: str, *, exclude_id: int | None = None) -> bool:
    sql = """
        SELECT COUNT(*) FROM `user`
        WHERE userName = %(user_name)s AND IFNULL(deleteStatus, 0) = 0
    """
    params: dict[str, Any] = {"user_name": user_name}
    if exclude_id:
        sql += " AND id <> %(exclude_id)s"
        params["exclude_id"] = exclude_id
    return int(scalar(sql, params) or 0) > 0


def insert_account(data: dict[str, Any]) -> int:
    return int(
        execute_insert(
            """
            INSERT INTO `user`
                (addTime, deleteStatus, userName, password, trueName, mobile, telephone,
                 email, company_name, cg_company_name, userType, status, is_app_login, photo_id)
            VALUES
                (NOW(), 0, %(userName)s, %(password)s, %(trueName)s, %(mobile)s, %(telephone)s,
                 %(email)s, %(company_name)s, %(cg_company_name)s, %(user_type)s, 1,
                 %(is_app_login)s, %(photo_id)s)
            """,
            {
                "userName": data["userName"],
                "password": data["password"],
                "trueName": data.get("trueName") or "",
                "mobile": data.get("mobile") or "",
                "telephone": data.get("telephone") or data.get("mobile") or "",
                "email": data.get("email") or "",
                "company_name": data.get("company_name") or data.get("companyId"),
                "cg_company_name": data.get("cg_company_name") or data.get("cgCompanyId") or None,
                "user_type": MEMBER_USER_TYPE,
                "is_app_login": 1 if _truthy(data.get("is_app_login")) else 0,
                "photo_id": data.get("photo_id") or data.get("photoId") or None,
            },
        )
        or 0
    )


def update_account(account_id: int, data: dict[str, Any]) -> None:
    sets = [
        "trueName = %(trueName)s",
        "mobile = %(mobile)s",
        "telephone = %(telephone)s",
        "email = %(email)s",
        "company_name = %(company_name)s",
        "cg_company_name = %(cg_company_name)s",
        "is_app_login = %(is_app_login)s",
    ]
    params: dict[str, Any] = {
        "id": account_id,
        "trueName": data.get("trueName") or "",
        "mobile": data.get("mobile") or "",
        "telephone": data.get("telephone") or data.get("mobile") or "",
        "email": data.get("email") or "",
        "company_name": data.get("company_name") or data.get("companyId"),
        "cg_company_name": data.get("cg_company_name") or data.get("cgCompanyId") or None,
        "is_app_login": 1 if _truthy(data.get("is_app_login")) else 0,
        "user_type": MEMBER_USER_TYPE,
    }
    if data.get("password"):
        sets.append("password = %(password)s")
        params["password"] = data["password"]
    if "userName" in data and data.get("userName"):
        sets.append("userName = %(userName)s")
        params["userName"] = data["userName"]
    photo_id = data.get("photo_id") if "photo_id" in data else data.get("photoId")
    if photo_id not in (None, ""):
        sets.append("photo_id = %(photo_id)s")
        params["photo_id"] = photo_id
    execute(
        f"""
        UPDATE `user`
        SET {', '.join(sets)}
        WHERE id = %(id)s AND userType = %(user_type)s
        """,
        params,
    )


def update_status(account_id: int, status: int | None = None) -> None:
    """对齐 Java MemberController.updateStatus：status=2 禁用(deleteStatus=1)，status=1 开启(deleteStatus=0)。"""
    if status is None:
        row = fetch_one(
            "SELECT deleteStatus FROM `user` WHERE id = %(id)s AND userType = %(user_type)s LIMIT 1",
            {"id": account_id, "user_type": MEMBER_USER_TYPE},
        )
        if not row:
            return
        delete_status = 0 if _truthy(row.get("deleteStatus")) else 1
    elif int(status) == 2:
        delete_status = 1
    elif int(status) == 1:
        delete_status = 0
    else:
        delete_status = 0 if int(status) else 1
    execute(
        "UPDATE `user` SET deleteStatus = %(delete_status)s WHERE id = %(id)s AND userType = %(user_type)s",
        {"id": account_id, "delete_status": delete_status, "user_type": MEMBER_USER_TYPE},
    )
