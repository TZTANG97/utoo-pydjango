from __future__ import annotations

from typing import Any

from apps.admin_system.helpers import build_tree, new_id, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_all_depts() -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, dept_sort, dept_name, dept_phone, dept_fax, dept_address,
               super_id, lead_uid, dept_desc, lab_ids
        FROM sy_dept
        ORDER BY dept_sort ASC, dept_name ASC
        """
    )
    normalized = [_normalize_dept(row) for row in rows]
    return build_tree(normalized, parent_key="superId")


def get_dept(dept_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT id, dept_sort, dept_name, dept_phone, dept_fax, dept_address,
               super_id, lead_uid, dept_desc, lab_ids
        FROM sy_dept WHERE id = %(id)s
        """,
        {"id": dept_id},
    )
    return _normalize_dept(row) if row else None


def insert_dept(data: dict[str, Any]) -> str:
    dept_id = new_id()
    execute_insert(
        """
        INSERT INTO sy_dept
            (id, dept_sort, dept_name, dept_phone, dept_fax, dept_address,
             super_id, lead_uid, dept_desc, lab_ids)
        VALUES
            (%(id)s, %(dept_sort)s, %(dept_name)s, %(dept_phone)s, %(dept_fax)s,
             %(dept_address)s, %(super_id)s, %(lead_uid)s, %(dept_desc)s, %(lab_ids)s)
        """,
        {
            "id": dept_id,
            "dept_sort": data.get("dept_sort") or 0,
            "dept_name": data.get("dept_name") or "",
            "dept_phone": data.get("dept_phone"),
            "dept_fax": data.get("dept_fax"),
            "dept_address": data.get("dept_address"),
            "super_id": data.get("super_id") or "0",
            "lead_uid": data.get("lead_uid"),
            "dept_desc": data.get("dept_desc"),
            "lab_ids": data.get("lab_ids"),
        },
    )
    return dept_id


def update_dept(data: dict[str, Any]) -> None:
    execute(
        """
        UPDATE sy_dept
        SET dept_sort = %(dept_sort)s,
            dept_name = %(dept_name)s,
            dept_phone = %(dept_phone)s,
            dept_fax = %(dept_fax)s,
            dept_address = %(dept_address)s,
            super_id = %(super_id)s,
            lead_uid = %(lead_uid)s,
            dept_desc = %(dept_desc)s,
            lab_ids = %(lab_ids)s
        WHERE id = %(id)s
        """,
        data,
    )


def delete_dept(dept_id: str) -> None:
    execute("DELETE FROM sy_dept WHERE id = %(id)s", {"id": dept_id})


def list_dept_options() -> list[dict[str, Any]]:
    rows = fetch_all(
        "SELECT id, dept_name, super_id FROM sy_dept ORDER BY dept_sort ASC"
    )
    return [{"id": r["id"], "deptName": r.get("dept_name"), "superId": r.get("super_id")} for r in rows]


def list_dept_ids_with_children(root_dept_id: str) -> list[str]:
    """本部门及下级部门 id（对齐 Java DeptAction.loadAllYhgl / childDept）。"""
    root = str(root_dept_id or "").strip()
    if not root or root == "0":
        return []
    rows = fetch_all("SELECT id, super_id FROM sy_dept")
    children_map: dict[str, list[str]] = {}
    for row in rows:
        pid = str(row.get("super_id") or "0")
        children_map.setdefault(pid, []).append(str(row.get("id") or ""))
    out: list[str] = []
    stack = [root]
    seen: set[str] = set()
    while stack:
        cur = stack.pop()
        if not cur or cur in seen:
            continue
        seen.add(cur)
        out.append(cur)
        stack.extend(children_map.get(cur, []))
    return out


def list_dept_options_for_yhgl(*, is_admin: bool, dept_id: str = "") -> list[dict[str, Any]]:
    all_opts = list_dept_options()
    if is_admin:
        return all_opts
    allowed = set(list_dept_ids_with_children(dept_id))
    if not allowed:
        return []
    return [o for o in all_opts if str(o.get("id") or "") in allowed]


def _normalize_dept(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "deptSort": row.get("dept_sort"),
        "deptName": row.get("dept_name"),
        "deptPhone": row.get("dept_phone"),
        "deptFax": row.get("dept_fax"),
        "deptAddress": row.get("dept_address"),
        "superId": row.get("super_id"),
        "leadUid": row.get("lead_uid"),
        "deptDesc": row.get("dept_desc"),
        "labIds": row.get("lab_ids"),
    }
