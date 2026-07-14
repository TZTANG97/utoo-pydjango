from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import page_clause
from apps.core.db_utils import execute, fetch_all, fetch_one, scalar


def list_entries(
    *,
    is_audit: str | int | None = None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE e.deleteStatus = 0"
    params: dict[str, Any] = {}
    if is_audit not in (None, ""):
        where += " AND e.is_audit = %(is_audit)s"
        params["is_audit"] = is_audit
    total = int(scalar(f"SELECT COUNT(*) FROM entry e {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            e.id,
            e.addTime,
            e.deleteStatus,
            e.user_id AS userId,
            e.title,
            e.content,
            e.updateTime,
            e.photo_ids AS photoIds,
            e.is_audit AS isAudit,
            u.userName,
            a.path,
            a.name
        FROM entry e
        LEFT JOIN exp_user u ON e.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        {where}
        ORDER BY e.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_entry(entry_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            e.id,
            e.addTime,
            e.user_id AS userId,
            e.title,
            e.content,
            e.updateTime,
            e.photo_ids AS photoIds,
            e.is_audit AS isAudit,
            u.userName,
            a.path,
            a.name
        FROM entry e
        LEFT JOIN exp_user u ON e.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE e.id = %(id)s
        LIMIT 1
        """,
        {"id": entry_id},
    )


def toggle_entry_audit(entry_id: int) -> int | None:
    row = fetch_one("SELECT is_audit FROM entry WHERE id = %(id)s LIMIT 1", {"id": entry_id})
    if not row:
        return None
    current = int(row.get("is_audit") or 0)
    next_val = 0 if current == 1 else 1
    execute(
        "UPDATE entry SET is_audit = %(is_audit)s, updateTime = NOW() WHERE id = %(id)s",
        {"id": entry_id, "is_audit": next_val},
    )
    return next_val


def list_comments(*, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE c.deleteStatus = 0 AND c.is_audit = 0"
    total = int(scalar(f"SELECT COUNT(*) FROM comment c {where}") or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            c.id,
            c.addTime,
            c.deleteStatus,
            c.content,
            c.is_audit AS isAudit,
            c.user_id AS userId,
            c.entry_id AS entryId,
            u.userName
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        {where}
        ORDER BY c.addTime DESC
        {clause}
        """,
        page_params,
    )
    return rows, total


def get_comment(comment_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            c.id,
            c.addTime,
            c.content,
            c.is_audit AS isAudit,
            c.user_id AS userId,
            c.entry_id AS entryId,
            u.userName
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        WHERE c.id = %(id)s
        LIMIT 1
        """,
        {"id": comment_id},
    )


def audit_comment(comment_id: int) -> tuple[bool, str]:
    comment = get_comment(comment_id)
    if not comment:
        return False, "评论不存在"
    entry_id = comment.get("entryId")
    if entry_id:
        entry = fetch_one(
            "SELECT is_audit FROM entry WHERE id = %(id)s LIMIT 1",
            {"id": entry_id},
        )
        if entry and int(entry.get("is_audit") or 0) == 0:
            return False, "所属帖子未上架，无法审核通过"
    execute(
        "UPDATE comment SET is_audit = 1 WHERE id = %(id)s",
        {"id": comment_id},
    )
    return True, "审核成功"


def delete_comment(comment_id: int) -> int:
    return execute(
        "UPDATE comment SET deleteStatus = 1 WHERE id = %(id)s",
        {"id": comment_id},
    )
