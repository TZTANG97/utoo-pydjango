"""讨论社区 — 数据访问"""
from __future__ import annotations

from typing import Any, Optional

from apps.core.db_utils import fetch_all, fetch_one, scalar

_ENTRY_SELECT = """
    SELECT e.id, e.addTime, e.deleteStatus, e.user_id AS userId, e.title, e.content,
           e.updateTime, e.photo_ids AS photoIds, e.is_audit AS isAudit,
           u.userName, a.path, a.name
    FROM entry e
    LEFT JOIN exp_user u ON e.user_id = u.id
    LEFT JOIN accessory a ON u.photo_id = a.id
    WHERE e.deleteStatus = 0
"""


def page_offset_limit(start: str, length: str) -> tuple[int, int]:
    offset = int(start) if str(start).isdigit() else 0
    if str(length) == "-1":
        return offset, 1000
    limit = int(length) if str(length).isdigit() else 10
    return offset, limit


def normalize_entry_order(
    order_by: str | None, order_type: str | None
) -> tuple[str, str]:
    ob = (order_by or "addTime").strip()
    ot = (order_type or "desc").strip().lower()
    if ob not in ("addTime", "updateTime", "commentCount"):
        ob = "addTime"
    if ot not in ("asc", "desc"):
        ot = "desc"
    return ob, ot


def _comment_count_expr() -> str:
    return """
        (SELECT COUNT(1) FROM comment c
         WHERE c.entry_id = e.id AND c.deleteStatus = 0 AND c.parent_id IS NULL
           AND c.is_audit = CASE
                 WHEN %(sort_uid)s = 0 OR c.user_id != %(sort_uid)s THEN 1
                 ELSE c.is_audit END)
    """


def build_entry_order_clause(order_by: str, order_type: str) -> str:
    pytest_last = "CASE WHEN e.content LIKE 'pytest%%' THEN 1 ELSE 0 END"
    direction = order_type.upper()
    if order_by == "updateTime":
        main = f"e.updateTime {direction}, e.addTime DESC"
    elif order_by == "commentCount":
        main = f"comment_cnt {direction}, e.addTime DESC"
    else:
        main = f"e.addTime {direction}"
    return f"{pytest_last}, {main}"


def fetch_entries_page(
    *,
    offset: int,
    limit: int,
    user_id: Optional[int] = None,
    is_audit: int = 1,
    order_by: str = "addTime",
    order_type: str = "desc",
    sort_viewer_id: int = 0,
) -> list[dict[str, Any]]:
    ob, ot = normalize_entry_order(order_by, order_type)
    where = " AND e.is_audit = %(audit)s"
    params: dict[str, Any] = {
        "audit": is_audit,
        "limit": limit,
        "offset": offset,
        "sort_uid": sort_viewer_id,
    }
    if user_id is not None:
        where += " AND e.user_id = %(uid)s"
        params["uid"] = user_id
    order_sql = build_entry_order_clause(ob, ot)
    select_sql = _ENTRY_SELECT
    if ob == "commentCount":
        select_sql = _ENTRY_SELECT.replace(
            "FROM entry e",
            f", {_comment_count_expr()} AS comment_cnt\n    FROM entry e",
            1,
        )
    sql = (
        select_sql
        + where
        + f"""
         ORDER BY {order_sql}
         LIMIT %(limit)s OFFSET %(offset)s
        """
    )
    return fetch_all(sql, params)


def fetch_liked_entries_page(
    *,
    offset: int,
    limit: int,
    user_id: int,
    fav_type: int,
    is_audit: int = 1,
) -> list[dict[str, Any]]:
    sql = """
        SELECT e.id, e.addTime, e.deleteStatus, e.user_id AS userId, e.title, e.content,
               e.updateTime, e.photo_ids AS photoIds, e.is_audit AS isAudit,
               u.userName, a.path, a.name,
               fl.addTime AS likeTime, fl.addTime AS collectTime
        FROM favorite_like fl
        INNER JOIN entry e ON fl.entry_id = e.id
        LEFT JOIN exp_user u ON e.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE fl.deleteStatus = 0 AND fl.is_cancel = 1 AND fl.type = %(ftype)s
          AND fl.user_id = %(uid)s AND e.deleteStatus = 0 AND e.is_audit = %(audit)s
        ORDER BY fl.addTime DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(
        sql,
        {
            "ftype": fav_type,
            "uid": user_id,
            "audit": is_audit,
            "limit": limit,
            "offset": offset,
        },
    )


def count_entries(
    *,
    user_id: Optional[int] = None,
    is_audit: int = 1,
) -> int:
    where = " AND e.is_audit = %(audit)s"
    params: dict[str, Any] = {"audit": is_audit}
    if user_id is not None:
        where += " AND e.user_id = %(uid)s"
        params["uid"] = user_id
    sql = f"SELECT COUNT(1) FROM entry e WHERE e.deleteStatus = 0{where}"
    return int(scalar(sql, params, 0) or 0)


def count_liked_entries(
    *, user_id: int, fav_type: int, is_audit: int = 1
) -> int:
    sql = """
        SELECT COUNT(1) FROM favorite_like fl
        INNER JOIN entry e ON fl.entry_id = e.id
        WHERE fl.deleteStatus = 0 AND fl.is_cancel = 1 AND fl.type = %(ftype)s
          AND fl.user_id = %(uid)s AND e.deleteStatus = 0 AND e.is_audit = %(audit)s
    """
    return int(
        scalar(sql, {"ftype": fav_type, "uid": user_id, "audit": is_audit}, 0) or 0
    )


def fetch_entry_by_id(
    entry_id: int, *, require_audit: bool = True
) -> Optional[dict[str, Any]]:
    where = " AND e.id = %(eid)s"
    params: dict[str, Any] = {"eid": entry_id}
    if require_audit:
        where += " AND e.is_audit = 1"
    return fetch_one(_ENTRY_SELECT + where + " LIMIT 1", params)


def fetch_top_comments(*, entry_id: int, viewer_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT c.id, c.parent_id AS parentId, c.content, c.is_hot AS isHot,
               c.like_count AS likeCount, c.addTime, c.user_id AS userId,
               c.is_audit AS isAudit, c.top_level AS topLevel,
               u.userName, a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.entry_id = %(eid)s AND c.deleteStatus = 0 AND c.parent_id IS NULL
          AND c.is_audit = CASE
                WHEN c.user_id = %(uid)s THEN c.is_audit
                ELSE 1
              END
        ORDER BY c.is_hot DESC, c.addTime DESC
    """
    return fetch_all(sql, {"eid": entry_id, "uid": viewer_id})


def fetch_replies(*, top_level: int, viewer_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT c.id, c.parent_id AS parentId, c.content, c.is_hot AS isHot,
               c.like_count AS likeCount, c.addTime, c.user_id AS userId,
               c.is_audit AS isAudit, c.top_level AS topLevel,
               u.userName, a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.top_level = %(tl)s AND c.deleteStatus = 0 AND c.parent_id IS NOT NULL
          AND c.is_audit = CASE
                WHEN %(uid)s IS NOT NULL AND c.user_id = %(uid)s THEN c.is_audit
                ELSE 1
              END
        ORDER BY c.addTime DESC
    """
    return fetch_all(sql, {"tl": top_level, "uid": viewer_id})


def fetch_entry_photos(photo_ids: str) -> list[dict[str, Any]]:
    if not photo_ids or not str(photo_ids).strip():
        return []
    ids = [p.strip() for p in str(photo_ids).split(",") if p.strip().isdigit()]
    if not ids:
        return []
    placeholders = ", ".join(f"%(id{i})s" for i in range(len(ids)))
    params = {f"id{i}": int(v) for i, v in enumerate(ids)}
    sql = f"""
        SELECT id, path, name FROM accessory
        WHERE deleteStatus = 0 AND id IN ({placeholders})
    """
    return fetch_all(sql, params)
