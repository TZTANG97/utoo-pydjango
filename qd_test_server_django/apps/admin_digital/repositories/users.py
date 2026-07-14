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
    utoo_types: list[str] | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE u.user_status = 1"
    params: dict[str, Any] = {}
    if dept_id and dept_id not in ("0", ""):
        # 选中上级部门时，包含其下级各部门人员（对齐 Java 部门树筛选语义）
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
    if utoo_types:
        placeholders = []
        for i, t in enumerate(utoo_types):
            key = f"ut{i}"
            placeholders.append(f"%({key})s")
            params[key] = t
        where += f" AND u.utoo_type IN ({', '.join(placeholders)})"
    total = int(scalar(f"SELECT COUNT(*) FROM sy_users u {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            u.id, u.user_name AS userName, u.true_name AS trueName,
            u.user_status AS userStatus, u.dept_id AS deptId, u.utoo_type AS utooType,
            d.dept_name AS deptName
        FROM sy_users u
        LEFT JOIN sy_dept d ON d.id = u.dept_id
        {where}
        ORDER BY u.true_name ASC, u.user_name ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def list_staff_users_all(
    *,
    utoo_types: list[str] | None = None,
    dept_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    where = "WHERE u.user_status = 1"
    params: dict[str, Any] = {}
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
