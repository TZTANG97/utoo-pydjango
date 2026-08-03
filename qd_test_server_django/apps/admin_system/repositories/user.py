from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from qd_common.password_java import encrypt_password_for_storage


def backfill_null_register_times() -> None:
    """旧平台列表对 registerTime 调 Date.format，NULL 会 500。"""
    try:
        execute(
            """
            UPDATE sy_users
            SET register_time = NOW()
            WHERE register_time IS NULL
            """
        )
    except Exception:
        pass


def list_users(
    *,
    dept_id: str = "",
    user_name: str = "",
    true_name: str = "",
    user_sex: str = "",
    role_type: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # 用户管理页展示全部状态；启用筛选由前端状态列体现
    # role_type 对齐 Java queryUsers.ajax?type= ：0销售主管+管理员 / 1销售主管 / 2系统管理员 / 3测试主管 / -1全部员工
    where = "WHERE u.pt_type LIKE %(pt_type)s"
    params: dict[str, Any] = {"pt_type": "%2%"}
    rt = str(role_type or "").strip()
    if rt != "":
        # 下拉选人场景：仅启用账号（对齐 Java user_status=1）
        where += " AND u.user_status = 1"
        if rt == "0":
            where += """
              AND u.utoo_type IN (
                SELECT sut.type_name FROM sy_user_type sut
                LEFT JOIN user_type_role utr ON utr.id = sut.role_id
                WHERE utr.name IN ('销售主管', '系统管理员') AND sut.type = 2
              )
            """
        elif rt == "1":
            where += """
              AND u.utoo_type IN (
                SELECT sut.type_name FROM sy_user_type sut
                LEFT JOIN user_type_role utr ON utr.id = sut.role_id
                WHERE utr.name = '销售主管' AND sut.type = 2
              )
            """
        elif rt == "2":
            where += """
              AND u.utoo_type IN (
                SELECT sut.type_name FROM sy_user_type sut
                LEFT JOIN user_type_role utr ON utr.id = sut.role_id
                WHERE utr.name = '系统管理员' AND sut.type = 2
              )
            """
        elif rt == "3":
            where += """
              AND u.utoo_type IN (
                SELECT sut.type_name FROM sy_user_type sut
                LEFT JOIN user_type_role utr ON utr.id = sut.role_id
                WHERE utr.name = '销售主管' AND sut.type_name = '测试主管' AND sut.type = 2
              )
            """
        # type=-1 或其他：仅 pt_type + 启用，不加角色过滤
    if dept_id and dept_id != "0":
        where += " AND u.dept_id = %(dept_id)s"
        params["dept_id"] = dept_id
    if user_name:
        where += " AND u.user_name LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if true_name:
        where += " AND u.true_name LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if user_sex != "":
        where += " AND u.user_sex = %(user_sex)s"
        params["user_sex"] = int(user_sex)
    total = scalar(f"SELECT COUNT(*) FROM sy_users u {where}", params)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT u.id, u.user_name, u.true_name, u.user_status, u.dept_id,
               u.mobile_phone_number, u.email, u.type, u.show_type,
               u.user_sex, u.utoo_type, u.account_type, u.register_time,
               d.dept_name
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        {where}
        ORDER BY u.user_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return [_normalize_user(row) for row in rows], int(total or 0)


def get_user(user_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, user_name, true_name, user_status, dept_id, mobile_phone_number,
               email, type, show_type, user_type_role_id, user_desc, helper_id,
               user_sex, qq_number, utoo_type, user_id AS linked_user_id,
               is_czqx, account_type, is_email, is_rate, store_id, register_time
        FROM sy_users WHERE id = %(id)s
        """,
        {"id": user_id},
    )
    if not row:
        return None
    user = _normalize_user(row)
    user["roleIds"] = get_user_role_ids(user_id)
    user["logs"] = list_user_logs(user_id)
    return user


def find_by_login_name(login_name: str) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, user_name FROM sy_users WHERE user_name = %(name)s LIMIT 1",
        {"name": login_name},
    )


def _account_rates() -> tuple[float, float]:
    row = fetch_one(
        """
        SELECT rmb_rate AS rmbRate, us_rate AS usRate
        FROM account_setting
        WHERE deleteStatus = 0 OR deleteStatus IS NULL
        ORDER BY id ASC
        LIMIT 1
        """
    )
    if not row:
        return 0.0, 0.0
    try:
        return float(row.get("rmbRate") or 0), float(row.get("usRate") or 0)
    except (TypeError, ValueError):
        return 0.0, 0.0


def _ensure_store() -> int | None:
    try:
        return int(
            execute_insert(
                """
                INSERT INTO store (addTime, deleteStatus, store_status)
                VALUES (NOW(), 0, 2)
                """
            )
        )
    except Exception:
        return None


def _ensure_accounts(user_id: str) -> None:
    rmb_rate, us_rate = _account_rates()
    for account_type, rate in ((1, rmb_rate), (2, us_rate)):
        exists = fetch_one(
            """
            SELECT id FROM account
            WHERE user_id = %(user_id)s AND account_type = %(account_type)s
            LIMIT 1
            """,
            {"user_id": user_id, "account_type": account_type},
        )
        if exists:
            continue
        try:
            execute_insert(
                """
                INSERT INTO account
                    (addTime, deleteStatus, account_type, user_id,
                     available_balance, freezing_balance, year_reat, income_total)
                VALUES
                    (NOW(), 0, %(account_type)s, %(user_id)s, 0, 0, %(rate)s, 0)
                """,
                {"account_type": account_type, "user_id": user_id, "rate": rate},
            )
        except Exception:
            pass


def insert_user(data: dict[str, Any]) -> str:
    user_id = new_id()
    store_id = _ensure_store()
    execute_insert(
        """
        INSERT INTO sy_users
            (id, user_name, true_name, user_password, user_status, dept_id,
             mobile_phone_number, email, type, show_type, user_type_role_id,
             user_desc, pt_type, account_type, register_time, error_count,
             last_login_ip, test_num, register_uid,
             user_sex, qq_number, utoo_type, user_id, is_czqx, helper_id,
             is_email, is_rate, store_id)
        VALUES
            (%(id)s, %(user_name)s, %(true_name)s, %(user_password)s, %(user_status)s,
             %(dept_id)s, %(mobile_phone_number)s, %(email)s, %(type)s, %(show_type)s,
             %(user_type_role_id)s, %(user_desc)s, '2', %(account_type)s, NOW(), 0,
             'x.x.x.x', 0, %(register_uid)s,
             %(user_sex)s, %(qq_number)s, %(utoo_type)s, %(linked_user_id)s, %(is_czqx)s,
             %(helper_id)s, %(is_email)s, %(is_rate)s, %(store_id)s)
        """,
        {
            "id": user_id,
            "user_name": data.get("user_name") or "",
            "true_name": data.get("true_name") or "",
            "user_password": encrypt_password_for_storage(data.get("user_password") or "123456"),
            "user_status": int(data.get("user_status") or 1),
            "dept_id": data.get("dept_id") or "0",
            "mobile_phone_number": data.get("mobile_phone_number"),
            "email": data.get("email"),
            "type": data.get("type") or "0",
            "show_type": data.get("show_type"),
            "user_type_role_id": data.get("user_type_role_id"),
            "user_desc": data.get("user_desc"),
            "account_type": int(data.get("account_type") or 0),
            "register_uid": data.get("register_uid") or data.get("operator_id") or None,
            "user_sex": int(data.get("user_sex") if data.get("user_sex") is not None else 1),
            "qq_number": data.get("qq_number"),
            "utoo_type": data.get("utoo_type"),
            "linked_user_id": data.get("linked_user_id") or data.get("user_id") or None,
            "is_czqx": int(data.get("is_czqx") or 0),
            "helper_id": data.get("helper_id") or None,
            "is_email": int(data.get("is_email") if data.get("is_email") is not None else 1),
            "is_rate": int(data.get("is_rate") if data.get("is_rate") is not None else 1),
            "store_id": store_id,
        },
    )
    _ensure_accounts(user_id)
    return user_id


def update_user(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_users
        SET user_name = %(user_name)s,
            true_name = %(true_name)s,
            user_status = %(user_status)s,
            dept_id = %(dept_id)s,
            mobile_phone_number = %(mobile_phone_number)s,
            email = %(email)s,
            type = %(type)s,
            show_type = %(show_type)s,
            user_type_role_id = %(user_type_role_id)s,
            user_desc = %(user_desc)s,
            user_sex = %(user_sex)s,
            qq_number = %(qq_number)s,
            utoo_type = %(utoo_type)s,
            user_id = %(linked_user_id)s,
            is_czqx = %(is_czqx)s,
            helper_id = %(helper_id)s,
            account_type = %(account_type)s,
            is_email = %(is_email)s,
            is_rate = %(is_rate)s
        WHERE id = %(id)s
        """,
        {
            "id": data.get("id"),
            "user_name": data.get("user_name") or "",
            "true_name": data.get("true_name") or "",
            "user_status": int(data.get("user_status") or 1),
            "dept_id": data.get("dept_id") or "0",
            "mobile_phone_number": data.get("mobile_phone_number"),
            "email": data.get("email"),
            "type": data.get("type"),
            "show_type": data.get("show_type"),
            "user_type_role_id": data.get("user_type_role_id"),
            "user_desc": data.get("user_desc"),
            "user_sex": int(data.get("user_sex") if data.get("user_sex") is not None else 1),
            "qq_number": data.get("qq_number"),
            "utoo_type": data.get("utoo_type"),
            "linked_user_id": data.get("linked_user_id") or None,
            "is_czqx": int(data.get("is_czqx") or 0),
            "helper_id": data.get("helper_id") or None,
            "account_type": int(data.get("account_type") or 0),
            "is_email": int(data.get("is_email") if data.get("is_email") is not None else 1),
            "is_rate": int(data.get("is_rate") if data.get("is_rate") is not None else 1),
        },
    )
    # 老用户缺账户时补齐
    if data.get("id"):
        _ensure_accounts(str(data["id"]))
        row = fetch_one("SELECT store_id FROM sy_users WHERE id = %(id)s", {"id": data["id"]})
        if row and not row.get("store_id"):
            store_id = _ensure_store()
            if store_id:
                execute(
                    "UPDATE sy_users SET store_id = %(store_id)s WHERE id = %(id)s",
                    {"store_id": store_id, "id": data["id"]},
                )


def update_password(user_id: str, password: str) -> None:
    execute(
        "UPDATE sy_users SET user_password = %(pwd)s WHERE id = %(id)s",
        {"id": user_id, "pwd": encrypt_password_for_storage(password)},
    )


def set_user_status(user_id: str, status: int) -> None:
    execute(
        "UPDATE sy_users SET user_status = %(status)s WHERE id = %(id)s",
        {"id": user_id, "status": int(status)},
    )


def disable_user(user_id: str) -> None:
    set_user_status(user_id, 0)


def get_user_role_ids(user_id: str) -> list[str]:
    rows = fetch_all(
        "SELECT role_id FROM sy_user_role WHERE user_id = %(user_id)s",
        {"user_id": user_id},
    )
    return [str(r["role_id"]) for r in rows if r.get("role_id")]


def set_user_roles(user_id: str, role_ids: list[str]) -> None:
    execute("DELETE FROM sy_user_role WHERE user_id = %(user_id)s", {"user_id": user_id})
    for role_id in role_ids:
        if role_id:
            execute_insert(
                "INSERT INTO sy_user_role (user_id, role_id) VALUES (%(user_id)s, %(role_id)s)",
                {"user_id": user_id, "role_id": role_id},
            )


def list_user_powers(user_id: str) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT DISTINCT m.id, m.menu_name AS menuName, m.url, m.menu_sort AS menuSort
        FROM sy_user_role ur
        INNER JOIN sy_role_menu rm ON rm.role_id = ur.role_id
        INNER JOIN sy_menu m ON m.id = rm.menu_id
        WHERE ur.user_id = %(user_id)s
        ORDER BY m.menu_sort ASC, m.menu_name ASC
        """,
        {"user_id": user_id},
    )
    return [
        {
            "id": r.get("id"),
            "menuName": r.get("menuName"),
            "url": r.get("url"),
        }
        for r in rows
    ]


def list_user_logs(user_id: str) -> list[dict[str, Any]]:
    try:
        rows = fetch_all(
            """
            SELECT t.id, t.addTime, t.log_info AS logInfo,
                   t.log_user_id AS logUserId, t.user_id AS userId,
                   u.true_name AS userName
            FROM sy_users_log t
            LEFT JOIN sy_users u ON u.id = t.log_user_id
            WHERE t.user_id = %(user_id)s
            ORDER BY t.addTime DESC, t.id DESC
            LIMIT 200
            """,
            {"user_id": user_id},
        )
    except Exception:
        return []
    return [
        {
            "id": r.get("id"),
            "addTime": r.get("addTime"),
            "logInfo": r.get("logInfo"),
            "userName": r.get("userName") or r.get("logUserId") or "-",
        }
        for r in rows
    ]


def insert_user_log(*, user_id: str, log_user_id: str, log_info: str) -> None:
    try:
        execute_insert(
            """
            INSERT INTO sy_users_log (addTime, deleteStatus, log_info, log_user_id, user_id)
            VALUES (NOW(), 0, %(log_info)s, %(log_user_id)s, %(user_id)s)
            """,
            {
                "log_info": (log_info or "")[:255],
                "log_user_id": log_user_id or "",
                "user_id": user_id,
            },
        )
    except Exception:
        pass


def list_role_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, role_name, role_desc
        FROM sy_role
        WHERE type = 2 OR type IS NULL
        ORDER BY role_name ASC
        """
    )
    return [
        {"id": r["id"], "roleName": r.get("role_name"), "roleDesc": r.get("role_desc")}
        for r in rows
    ]


def list_utoo_type_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, type_name AS typeName
        FROM sy_user_type
        WHERE type = 2 OR type IS NULL
        ORDER BY type_sort ASC, id ASC
        """
    )
    return [{"id": r.get("id"), "typeName": r.get("typeName")} for r in rows]


def list_helper_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, user_name AS userName, true_name AS trueName
        FROM sy_users
        WHERE user_status = 1 AND pt_type LIKE %(pt_type)s
        ORDER BY true_name ASC, user_name ASC
        """,
        {"pt_type": "%2%"},
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


def list_member_options() -> list[dict[str, Any]]:
    """关联账号：对齐 Java queryAllMembers（userType=5 且绑定公司）。"""
    try:
        rows = fetch_all(
            """
            SELECT u.id, u.userName AS userName, u.trueName AS trueName
            FROM `user` u
            INNER JOIN qd_user_company c ON u.company_name = c.id
            WHERE u.userType = 5
              AND (u.deleteStatus = 0 OR u.deleteStatus IS NULL)
            ORDER BY u.userName ASC
            LIMIT 2000
            """
        )
    except Exception:
        try:
            rows = fetch_all(
                """
                SELECT id, userName AS userName, trueName AS trueName
                FROM `user`
                WHERE userType = 5
                  AND (deleteStatus = 0 OR deleteStatus IS NULL)
                ORDER BY userName ASC
                LIMIT 2000
                """
            )
        except Exception:
            rows = []
    return [
        {
            "id": r.get("id"),
            "userName": r.get("userName"),
            "trueName": r.get("trueName"),
            "label": str(r.get("userName") or r.get("id") or ""),
        }
        for r in rows
    ]


def _users_by_utoo_type(utoo_type: str) -> list[dict[str, Any]]:
    """对齐 Java queryUsersByType0419：pt_type 含 2、启用、指定 utoo_type。"""
    rows = fetch_all(
        """
        SELECT u.id, u.user_name, u.true_name, u.user_status, u.dept_id,
               u.mobile_phone_number, u.email, u.type, u.show_type,
               u.user_sex, u.utoo_type, u.account_type, u.register_time,
               d.dept_name
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        WHERE u.pt_type LIKE %(pt_type)s
          AND u.user_status = 1
          AND u.utoo_type = %(utoo_type)s
        ORDER BY u.user_name ASC
        """,
        {"pt_type": "%2%", "utoo_type": utoo_type},
    )
    return [_normalize_user(r) for r in rows or []]


def _users_by_exp_class(class_id: int | str) -> list[dict[str, Any]]:
    """sy_user_expmanage 关联实验分类的用户。"""
    try:
        cid = int(class_id)
    except (TypeError, ValueError):
        return []
    if cid <= 0:
        return []
    rows = fetch_all(
        """
        SELECT u.id, u.user_name, u.true_name, u.user_status, u.dept_id,
               u.mobile_phone_number, u.email, u.type, u.show_type,
               u.user_sex, u.utoo_type, u.account_type, u.register_time,
               d.dept_name
        FROM sy_user_expmanage sue
        INNER JOIN sy_users u ON u.id = sue.user_id
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        WHERE sue.exp_manage_id = %(cid)s
          AND u.pt_type LIKE %(pt_type)s
          AND u.user_status = 1
        ORDER BY u.user_name ASC
        """,
        {"cid": cid, "pt_type": "%2%"},
    )
    return [_normalize_user(r) for r in rows or []]


def list_test_users(*, class_id: str = "", with_admin: bool = True) -> list[dict[str, Any]]:
    """
    对齐 Java queryTestUsers / queryTestUsers1：
    - 测试人员 + 测试主管
    - with_admin 时含系统管理员
    - class_id 有值时合并 sy_user_expmanage 绑定用户
    """
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    def _add(rows: list[dict[str, Any]]) -> None:
        for r in rows:
            uid = str(r.get("id") or "")
            if not uid or uid in seen:
                continue
            seen.add(uid)
            out.append(r)

    if with_admin:
        _add(_users_by_utoo_type("系统管理员"))
    _add(_users_by_utoo_type("测试人员"))
    _add(_users_by_utoo_type("测试主管"))
    if str(class_id or "").strip():
        _add(_users_by_exp_class(class_id))
    return out


def _normalize_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "userName": row.get("user_name"),
        "trueName": row.get("true_name"),
        "userStatus": row.get("user_status"),
        "deptId": row.get("dept_id"),
        "deptName": row.get("dept_name"),
        "mobilePhoneNumber": row.get("mobile_phone_number"),
        "email": row.get("email"),
        "type": row.get("type"),
        "showType": row.get("show_type"),
        "userTypeRoleId": row.get("user_type_role_id"),
        "userDesc": row.get("user_desc"),
        "helperId": row.get("helper_id"),
        "userSex": row.get("user_sex"),
        "qqNumber": row.get("qq_number"),
        "utooType": row.get("utoo_type"),
        "userId": row.get("linked_user_id") or row.get("user_id"),
        "isCzqx": row.get("is_czqx"),
        "accountType": row.get("account_type"),
        "isEmail": row.get("is_email"),
        "isRate": row.get("is_rate"),
        "storeId": row.get("store_id"),
        "registerTime": row.get("register_time"),
    }
