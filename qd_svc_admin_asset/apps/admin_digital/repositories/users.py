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


def list_depts_by_ids(dept_ids: list[str]) -> list[dict[str, Any]]:
    ids = [str(d) for d in dept_ids if str(d or "").strip()]
    if not ids:
        return []
    placeholders = []
    params: dict[str, Any] = {}
    for i, d in enumerate(ids):
        key = f"d{i}"
        placeholders.append(f"%({key})s")
        params[key] = d
    return fetch_all(
        f"""
        SELECT id, dept_name AS deptName, super_id AS superId, dept_sort AS deptSort
        FROM sy_dept
        WHERE id IN ({', '.join(placeholders)})
        ORDER BY dept_sort ASC, dept_name ASC
        """,
        params,
    )


def can_manage_sale_plan(staff: dict[str, Any] | None) -> bool:
    """对齐 Java saleUserPerformance/queryUsers：仅系统管理员或销售主管。"""
    role = staff_role_name(staff)
    return is_lab_sale_admin(role) or is_lab_sale_manager(role)


def resolve_sale_plan_dept_id(viewer: dict[str, Any], requested_dept_id: str = "") -> str | None:
    """解析销售产出计划查询部门。

    - 管理员：空/0 表示全部；指定部门原样返回
    - 销售主管：空/0 回落到本人部门；指定部门须在本人部门树内
    - 其他：无权限（返回 None）
    """
    if not viewer or not can_manage_sale_plan(viewer):
        return None
    role = staff_role_name(viewer)
    req = str(requested_dept_id or "").strip()
    if is_lab_sale_admin(role):
        return "" if req in ("", "0") else req
    own = str(viewer.get("deptId") or "").strip()
    allowed = set(child_dept_ids(own)) if own else set()
    if req in ("", "0"):
        return own
    if req in allowed:
        return req
    return None


def list_sale_plan_depts(viewer: dict[str, Any] | None) -> dict[str, Any]:
    """对齐 Java saleUserPerformance/load + loadDpet。"""
    if not viewer or not can_manage_sale_plan(viewer):
        return {
            "depts": [],
            "deptId": "",
            "deptName": "",
            "canQuery": False,
        }
    role = staff_role_name(viewer)
    if is_lab_sale_admin(role):
        return {
            "depts": list_depts_flat(),
            "deptId": "0",
            "deptName": "全部部门",
            "canQuery": True,
        }
    own = str(viewer.get("deptId") or "").strip()
    allowed_ids = child_dept_ids(own) if own else []
    depts = list_depts_by_ids(allowed_ids)
    dept_name = ""
    for d in depts:
        if str(d.get("id") or "") == own:
            dept_name = str(d.get("deptName") or "")
            break
    return {
        "depts": depts,
        "deptId": own or "0",
        "deptName": dept_name or "本部门",
        "canQuery": True,
    }


def list_staff_users(
    *,
    dept_id: str = "",
    user_name: str = "",
    true_name: str = "",
    user_sex: str | int | None = None,
    utoo_types: list[str] | None = None,
    require_pt_type_staff: bool = False,
    include_helpers: bool = False,
    exact_dept: bool = False,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """员工列表。

    实验室产出计划（对齐 Java getuserinfoMapSTP）：
    - user_status=1 且 pt_type like '%2%'
    - 管理员不过滤 utoo_type（utoo_types=None）
    - 含协助者 / 间接协助者 / 注册时间 / 性别
    - exact_dept=True：精确 dept_id（对齐 Java STP）；False：含下级部门
    """
    where = "WHERE u.user_status = 1"
    params: dict[str, Any] = {}
    if require_pt_type_staff:
        where += " AND u.pt_type LIKE %(pt_type)s"
        params["pt_type"] = "%2%"
    if dept_id and dept_id not in ("0", ""):
        if exact_dept:
            where += " AND u.dept_id = %(dept_id)s"
            params["dept_id"] = str(dept_id)
        else:
            # 树选中上级时仍包含下级（便于现网树筛选）
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
               dept_id AS deptId, utoo_type AS utooType, type,
               pt_type AS ptType, user_status AS userStatus
        FROM sy_users WHERE id = %(id)s LIMIT 1
        """,
        {"id": user_id},
    )


def staff_role_name(staff: dict[str, Any] | None) -> str:
    """优先 utoo_type（对齐 Java SyUsers#getUtoo_type），其次 type。"""
    if not staff:
        return ""
    return str(staff.get("utooType") or staff.get("type") or "").strip()


def is_lab_sale_admin(role: str) -> bool:
    """对齐 Java UserTypes.ADMIN；兼容现网「超级管理员」。"""
    text = (role or "").strip()
    if not text:
        return False
    return text == "系统管理员" or text == "超级管理员" or "管理员" in text


def is_lab_sale_manager(role: str) -> bool:
    """对齐 Java UserTypes.SALE_MANAGER。"""
    return (role or "").strip() == "销售主管"


def is_lab_test_manager(role: str) -> bool:
    """对齐 Java UserTypes.TEST_MANAGER。"""
    return (role or "").strip() == "测试主管"


def is_lab_test_user(role: str) -> bool:
    """对齐 Java UserTypes.TEST_USER。"""
    return (role or "").strip() == "测试人员"


TEST_PERF_TYPES = ["测试人员", "测试主管"]


def list_lab_test_visible_users(staff: dict[str, Any]) -> list[dict[str, Any]]:
    """实验室测试人员绩效可见人员（LabPerformanceController）。

    - 销售主管 / 测试主管：本部门及下级中的测试人员、测试主管
    - 系统管理员：全部测试人员、测试主管
    - 测试人员：仅本人
    - 其他角色：空
    """
    if not staff:
        return []
    role = staff_role_name(staff)
    if is_lab_sale_admin(role):
        return list_staff_users_all(utoo_types=TEST_PERF_TYPES)
    if is_lab_sale_manager(role) or is_lab_test_manager(role):
        dept_ids = child_dept_ids(str(staff.get("deptId") or ""))
        if not dept_ids:
            return []
        return list_staff_users_all(utoo_types=TEST_PERF_TYPES, dept_ids=dept_ids)
    if is_lab_test_user(role):
        return [
            {
                "id": staff.get("id"),
                "userName": staff.get("userName"),
                "trueName": staff.get("trueName"),
                "deptId": staff.get("deptId"),
                "utooType": staff.get("utooType"),
                "deptName": staff.get("deptName"),
            }
        ]
    return []


def _ensure_staff_in_rows(rows: list[dict[str, Any]], staff: dict[str, Any]) -> list[dict[str, Any]]:
    """下拉必须含当前登录人（对齐 Java 页默认 $!user_id）。"""
    sid = str(staff.get("id") or "").strip()
    if not sid:
        return rows
    if any(str(r.get("id") or "") == sid for r in rows):
        return rows
    return [
        {
            "id": staff.get("id"),
            "userName": staff.get("userName"),
            "trueName": staff.get("trueName"),
            "deptId": staff.get("deptId"),
            "utooType": staff.get("utooType"),
            "deptName": staff.get("deptName"),
        },
        *rows,
    ]


def list_lab_sale_selectable_users(staff: dict[str, Any]) -> list[dict[str, Any]]:
    """对齐 Java LabPerformanceSaleuserController#selUsersByDeptId。

    - 销售主管：本部门及下级所有 pt_type 含 2 的启用员工
    - 系统管理员：全部 pt_type 含 2 的启用员工（UserMapper.queryUsersByDeptId2）
    - 其他：仅本人
    """
    role = staff_role_name(staff)
    if is_lab_sale_manager(role):
        dept_ids = child_dept_ids(str(staff.get("deptId") or ""))
        rows = (
            list_staff_users_all(dept_ids=dept_ids, require_pt_type_staff=True)
            if dept_ids
            else [staff]
        )
        return _ensure_staff_in_rows(rows, staff)
    if is_lab_sale_admin(role):
        rows = list_staff_users_all(require_pt_type_staff=True)
        return _ensure_staff_in_rows(rows, staff)
    return [
        {
            "id": staff.get("id"),
            "userName": staff.get("userName"),
            "trueName": staff.get("trueName"),
            "deptId": staff.get("deptId"),
            "utooType": staff.get("utooType"),
            "deptName": staff.get("deptName"),
        }
    ]


def can_view_lab_sale_user(viewer: dict[str, Any], target_user_id: str) -> bool:
    """查询/订单明细权限：目标须在可见人员列表内。"""
    tid = str(target_user_id or "").strip()
    if not tid or not viewer:
        return False
    if str(viewer.get("id") or "") == tid:
        return True
    role = staff_role_name(viewer)
    if is_lab_sale_admin(role):
        return True
    if is_lab_sale_manager(role):
        allowed = {str(r.get("id") or "") for r in list_lab_sale_selectable_users(viewer)}
        return tid in allowed
    return False


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
