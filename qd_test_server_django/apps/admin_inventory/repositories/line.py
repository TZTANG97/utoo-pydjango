from __future__ import annotations

from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_lines_by_lab(
    *,
    lab_id: str | int,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java /lab/lineList.ajax：按实验室分页列实验线。"""
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.lab_id = %(lab_id)s"
    params: dict[str, Any] = {"lab_id": lab_id}
    total = int(
        scalar(
            f"SELECT COUNT(*) FROM experiment_line t {where}",
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.line_num AS lineNum, t.line_num AS line_num,
            t.lab_id AS labId, t.lab_id AS lab_id,
            t.class_id AS classId, t.class_id AS class_id,
            t.status, t.line_status AS lineStatus, t.line_status AS line_status,
            t.run_num AS runNum, t.deleteStatus,
            m.name AS className
        FROM experiment_line t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows or [], total


def get_line(line_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.line_num AS lineNum, t.line_num AS line_num,
            t.lab_id AS labId, t.lab_id AS lab_id,
            t.class_id AS classId, t.class_id AS class_id,
            t.status, t.line_status AS lineStatus, t.line_status AS line_status,
            t.run_num AS runNum,
            m.name AS className
        FROM experiment_line t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": line_id},
    )


def insert_line(*, lab_id: int, line_num: str, class_id: int) -> int:
    return execute_insert(
        """
        INSERT INTO experiment_line
            (addTime, deleteStatus, line_num, lab_id, class_id, status, line_status)
        VALUES
            (NOW(), 0, %(line_num)s, %(lab_id)s, %(class_id)s, 1, 0)
        """,
        {"line_num": line_num, "lab_id": lab_id, "class_id": class_id},
    )


def update_line(line_id: int, *, line_num: str, class_id: int) -> None:
    execute(
        """
        UPDATE experiment_line
        SET line_num = %(line_num)s, class_id = %(class_id)s
        WHERE id = %(id)s
        """,
        {"id": line_id, "line_num": line_num, "class_id": class_id},
    )


def set_line_status(line_id: int, status: int) -> None:
    execute(
        "UPDATE experiment_line SET status = %(status)s WHERE id = %(id)s",
        {"id": line_id, "status": status},
    )


def list_line_class_options() -> list[dict[str, Any]]:
    """对齐 Java experimentManage/queryAll2.ajax?type=2：二级类 + 其下三级类。"""
    parents = fetch_all(
        """
        SELECT id, name
        FROM experiment_manage
        WHERE IFNULL(deleteStatus, 0) = 0 AND type = 2
        ORDER BY sequence ASC, id ASC
        """
    )
    out: list[dict[str, Any]] = []
    for parent in parents:
        pid = parent.get("id")
        pname = str(parent.get("name") or "")
        children = fetch_all(
            """
            SELECT id, name
            FROM experiment_manage
            WHERE IFNULL(deleteStatus, 0) = 0 AND parent_id = %(pid)s
            ORDER BY sequence ASC, id ASC
            """,
            {"pid": pid},
        )
        for child in children:
            out.append(
                {
                    "id": child.get("id"),
                    "name": f"{child.get('name') or ''} - {pname}".strip(" -"),
                }
            )
        out.append({"id": pid, "name": pname})
    return out
