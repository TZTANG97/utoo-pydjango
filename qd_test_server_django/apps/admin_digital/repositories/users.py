from __future__ import annotations

from typing import Any

from apps.admin_digital.helpers import page_clause
from apps.core.db_utils import fetch_all, fetch_one, scalar


def list_depts_flat() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, dept_name AS deptName, super_id AS superId, dept_sort AS deptSort
        FROM sy_dept
        ORDER BY dept_sort ASC, dept_name ASC
        """
    )
    return rows


def list_staff_users(
    *,
    dept_id: str = "",
    user_name: str = "",
    true_name: str = "",
    user_sex: str | int | None = None,
    utoo_types: list[str] | None = None,
    require_pt_type_staff: bool = False,
    include_helpers: bool = False,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """员工列表。

    实验室产出计划（对齐 Java getuserinfoMapSTP）：
    - user_status=1 且 pt_type like '%2%'
    - 管理员不过滤 utoo_type（utoo_types=None）
    - 含协助者 / 间接协助者 / 注册时间 / 性别
    """
    where = "WHERE u.user_status = 1"
    params: dict[str, Any] = {}
    if require_pt_type_staff:
        where += " AND u.pt_type LIKE %(pt_type)s"
        params["pt_type"] = "%2%"
    if dept_id and dept_id not in ("0", ""):
        # Java STP 为精确 dept_id；树选中上级时仍包含下级（便于现网树筛选）
        dept_ids = child_dept_ids(str(dept_id))
        if len(dept_ids) == 1:
            where += " AND u.dept_id = %(dept_id)s"
            params["dept_id"] = dept_ids[0]
        elif dept_ids:
            placeholders = []
            for i, d in enumerate(dept_ids):
                key = f"dept_{i}"
                placeholders.append(f"%({key})s")
                params[key] = d
            where += f" AND u.dept_id IN ({', '.join(placeholders)})"
    if user_name:
        where += " AND u.user_name LIKE %(user_name)s"
        params["user_name"] = f"%{user_name}%"
    if true_name:
        where += " AND u.true_name LIKE %(true_name)s"
        params["true_name"] = f"%{true_name}%"
    if user_sex not in (None, ""):
        where += " AND u.user_sex = %(user_sex)s"
        params["user_sex"] = int(user_sex)
    if utoo_types:
        placeholders = []
        for i, t in enumerate(utoo_types):
            key = f"ut{i}"
            placeholders.append(f"%({key})s")
            params[key] = t
        where += f" AND u.utoo_type IN ({', '.join(placeholders)})"
    total = int(scalar(f"SELECT COUNT(*) FROM sy_users u {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    helper_join = ""
    helper_cols = ""
    if include_helpers:
        helper_join = """
        LEFT JOIN sy_users u1 ON u1.id = u.helper_id
        LEFT JOIN sy_users u2 ON u2.id = u1.helper_id
        """
        helper_cols = """,
            u1.true_name AS helperName,
            u2.true_name AS firstHelperName
        """
    order_by = (
        "ORDER BY u.register_time DESC, u.true_name ASC"
        if include_helpers
        else "ORDER BY u.true_name ASC, u.user_name ASC"
    )
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.user_name AS userName, u.true_name AS trueName,
            u.user_status AS userStatus, u.dept_id AS deptId, u.utoo_type AS utooType,
            u.user_sex AS userSex, u.register_time AS registerTime,
            d.dept_name AS deptName
            {helper_cols}
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        {helper_join}
        {where}
        {order_by}
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        sex = row.get("userSex")
        if sex in (1, "1"):
            row["userSexLabel"] = "男"
        elif sex in (0, "0"):
            row["userSexLabel"] = "女"
        else:
            row["userSexLabel"] = ""
        status = row.get("userStatus")
        row["userStatusLabel"] = "正常" if status in (1, "1") else "禁用"
        rt = row.get("registerTime")
        if rt is not None and hasattr(rt, "strftime"):
            row["registerTime"] = rt.strftime("%Y-%m-%d %H:%M:%S")
        elif rt is not None:
            row["registerTime"] = str(rt)
    return rows, total


def list_staff_users_all(
    *,
    utoo_types: list[str] | None = None,
    dept_ids: list[str] | None = None,
    require_pt_type_staff: bool = False,
) -> list[dict[str, Any]]:
    """对齐 Java UserMapper.queryUsersByDeptId2：启用员工，可选 pt_type/部门/类型。"""
    where = "WHERE u.user_status = 1"
    params: dict[str, Any] = {}
    if require_pt_type_staff:
        where += " AND u.pt_type LIKE %(pt_type)s"
        params["pt_type"] = "%2%"
    if utoo_types:
        placeholders = []
        for i, t in enumerate(utoo_types):
            key = f"ut{i}"
            placeholders.append(f"%({key})s")
            params[key] = t
        where += f" AND u.utoo_type IN ({', '.join(placeholders)})"
    if dept_ids:
        placeholders = []
        for i, d in enumerate(dept_ids):
            key = f"d{i}"
            placeholders.append(f"%({key})s")
            params[key] = d
        where += f" AND u.dept_id IN ({', '.join(placeholders)})"
    return fetch_all(
        f"""
        SELECT
            u.id, u.user_name AS userName, u.true_name AS trueName,
            u.dept_id AS deptId, u.utoo_type AS utooType,
            d.dept_name AS deptName
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        {where}
        ORDER BY u.true_name ASC
        """,
        params,
    )


def get_staff(user_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, user_name AS userName, true_name AS trueName,
               dept_id AS deptId, utoo_type AS utooType
        FROM sy_users WHERE id = %(id)s LIMIT 1
        """,
        {"id": user_id},
    )


def child_dept_ids(root_id: str) -> list[str]:
    """含自身的部门及下级（一层层展开，最多若干层）。"""
    if not root_id or root_id == "0":
        return []
    result = [root_id]
    frontier = [root_id]
    for _ in range(8):
        if not frontier:
            break
        placeholders = []
        params: dict[str, Any] = {}
        for i, d in enumerate(frontier):
            key = f"p{i}"
            placeholders.append(f"%({key})s")
            params[key] = d
        rows = fetch_all(
            f"""
            SELECT id FROM sy_dept
            WHERE super_id IN ({', '.join(placeholders)})
            """,
            params,
        )
        frontier = [str(r["id"]) for r in rows if str(r["id"]) not in result]
        result.extend(frontier)
    return result
