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
    row = fetch_one(
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
    if not row:
        return None
    return _enrich_entry_detail(dict(row))


OSS_BASE = "https://qgongye.oss-cn-shanghai.aliyuncs.com/"
DEFAULT_AVATAR = f"{OSS_BASE}goods/531da299-7156-4ad0-95a4-c94e978c924d.jpg"


def _fmt_time(val: Any) -> str:
    if val is None or val == "":
        return ""
    text = str(val)
    return text[:19] if len(text) >= 19 else text


def _avatar_url(path: Any, name: Any) -> str:
    p = str(path or "").strip().rstrip("/")
    n = str(name or "").strip().lstrip("/")
    if p and n:
        return f"{OSS_BASE}{p}/{n}"
    return DEFAULT_AVATAR


def _accessory_url(path: Any, name: Any) -> str:
    p = str(path or "").strip().rstrip("/")
    n = str(name or "").strip().lstrip("/")
    if p and n:
        return f"{OSS_BASE}{p}/{n}"
    return ""


def _photo_urls(photo_ids: Any) -> list[str]:
    raw = str(photo_ids or "").strip()
    if not raw:
        return []
    ids = [p.strip() for p in raw.split(",") if p.strip().isdigit()]
    if not ids:
        return []
    placeholders = ", ".join(f"%(id{i})s" for i in range(len(ids)))
    params = {f"id{i}": int(v) for i, v in enumerate(ids)}
    rows = fetch_all(
        f"""
        SELECT id, path, name FROM accessory
        WHERE IFNULL(deleteStatus, 0) = 0 AND id IN ({placeholders})
        """,
        params,
    )
    by_id = {int(r["id"]): r for r in rows if r.get("id") is not None}
    out: list[str] = []
    for sid in ids:
        r = by_id.get(int(sid))
        if not r:
            continue
        url = _accessory_url(r.get("path"), r.get("name"))
        if url:
            out.append(url)
    return out


def _list_top_comments(entry_id: int) -> list[dict[str, Any]]:
    """对齐 Java commentSection：userId=null，仅已审核一级评论。"""
    return fetch_all(
        """
        SELECT
            c.id,
            c.parent_id AS parentId,
            c.content,
            c.is_hot AS isHot,
            c.like_count AS likeCount,
            c.addTime,
            c.user_id AS userId,
            c.is_audit AS isAudit,
            c.top_level AS topLevel,
            u.userName,
            a.path,
            a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.entry_id = %(eid)s
          AND IFNULL(c.deleteStatus, 0) = 0
          AND c.parent_id IS NULL
          AND c.is_audit = 1
        ORDER BY c.is_hot DESC, c.addTime DESC
        """,
        {"eid": entry_id},
    )


def _list_replies(top_level: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
            c.id,
            c.parent_id AS parentId,
            c.content,
            c.is_hot AS isHot,
            c.like_count AS likeCount,
            c.addTime,
            c.user_id AS userId,
            c.is_audit AS isAudit,
            c.top_level AS topLevel,
            u.userName,
            a.path,
            a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.top_level = %(tl)s
          AND IFNULL(c.deleteStatus, 0) = 0
          AND c.parent_id IS NOT NULL
          AND c.is_audit = 1
        ORDER BY c.addTime ASC
        """,
        {"tl": top_level},
    )


def _parent_user_name(parent_id: Any) -> str:
    if parent_id in (None, ""):
        return ""
    try:
        pid = int(parent_id)
    except (TypeError, ValueError):
        return ""
    row = fetch_one(
        """
        SELECT u.userName, c.user_id AS userId
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        WHERE c.id = %(id)s
        LIMIT 1
        """,
        {"id": pid},
    )
    if not row:
        return ""
    name = str(row.get("userName") or "").strip()
    if name:
        return name
    uid = row.get("userId")
    return f"默认用户{uid}" if uid not in (None, "") else ""


def _normalize_comment(row: dict[str, Any], *, with_replies: bool = False) -> dict[str, Any]:
    uid = row.get("userId")
    user_name = str(row.get("userName") or "").strip()
    if not user_name:
        user_name = f"默认用户{uid}" if uid not in (None, "") else "默认用户"
    item: dict[str, Any] = {
        "id": row.get("id"),
        "parentId": row.get("parentId"),
        "content": row.get("content") or "",
        "userId": uid,
        "userName": user_name,
        "addTime": _fmt_time(row.get("addTime")),
        "addTimes": _fmt_time(row.get("addTime")),
        "isAudit": row.get("isAudit"),
        "likeCount": row.get("likeCount") or 0,
        "avatar": _avatar_url(row.get("path"), row.get("name")),
        "puserName": "",
        "replies": [],
    }
    if with_replies:
        replies_raw = _list_replies(int(row["id"]))
        replies: list[dict[str, Any]] = []
        for r in replies_raw:
            reply = _normalize_comment(r, with_replies=False)
            reply["puserName"] = _parent_user_name(r.get("parentId"))
            replies.append(reply)
        item["replies"] = replies
    return item


def _enrich_entry_detail(row: dict[str, Any]) -> dict[str, Any]:
    entry_id = int(row["id"])
    at = row.get("addTime")
    row["addTime"] = _fmt_time(at)
    row["userName"] = str(row.get("userName") or "").strip() or f"默认用户{row.get('userId') or ''}"
    row["photos"] = _photo_urls(row.get("photoIds"))
    row["stringList"] = row["photos"]
    comments = [_normalize_comment(c, with_replies=True) for c in _list_top_comments(entry_id)]
    row["commentList"] = comments
    row["comments"] = comments
    return row


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
