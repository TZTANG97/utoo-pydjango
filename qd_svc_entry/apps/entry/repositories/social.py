from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar


def favorite_exists(*, entry_id: int, user_id: int, fav_type: int) -> bool:
    return (
        fetch_one(
            """
            SELECT id FROM favorite_like
            WHERE deleteStatus = 0 AND entry_id = %(eid)s AND user_id = %(uid)s
              AND type = %(tp)s AND is_cancel = 1
            LIMIT 1
            """,
            {"eid": entry_id, "uid": user_id, "tp": fav_type},
        )
        is not None
    )


def comment_liked_by_user(*, comment_id: int, user_id: int) -> bool:
    return (
        fetch_one(
            """
            SELECT id FROM like_log
            WHERE deleteStatus = 0 AND target_id = %(cid)s AND user_id = %(uid)s
              AND type = 2 AND is_cancel = 1
            LIMIT 1
            """,
            {"cid": comment_id, "uid": user_id},
        )
        is not None
    )


def count_comment_likes(comment_id: int) -> int:
    return int(
        scalar(
            """
            SELECT COUNT(1) FROM like_log
            WHERE deleteStatus = 0 AND target_id = %(cid)s
              AND type = 2 AND is_cancel = 1
            """,
            {"cid": comment_id},
            0,
        )
        or 0
    )


def get_parent_comment_user(parent_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT u.userName, a.path, a.name, c.user_id AS userId
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.id = %(pid)s LIMIT 1
        """,
        {"pid": parent_id},
    )


def batch_favorite_entry_ids(
    entry_ids: list[int], viewer_id: int
) -> list[dict[str, Any]]:
    if not entry_ids:
        return []
    placeholders = ", ".join(f"%(e{i})s" for i in range(len(entry_ids)))
    params: dict[str, Any] = {"uid": viewer_id}
    params.update({f"e{i}": eid for i, eid in enumerate(entry_ids)})
    return fetch_all(
        f"""
        SELECT entry_id, type FROM favorite_like
        WHERE deleteStatus = 0 AND is_cancel = 1 AND user_id = %(uid)s
          AND entry_id IN ({placeholders})
        """,
        params,
    )


def fetch_accessories_by_ids(photo_ids: set[int]) -> list[dict[str, Any]]:
    if not photo_ids:
        return []
    placeholders = ", ".join(f"%(p{i})s" for i in range(len(photo_ids)))
    params = {f"p{i}": pid for i, pid in enumerate(photo_ids)}
    return fetch_all(
        f"""
        SELECT id, path, name FROM accessory
        WHERE deleteStatus = 0 AND id IN ({placeholders})
        """,
        params,
    )


def fetch_top_comments_for_entries(
    entry_ids: list[int], viewer_id: int
) -> list[dict[str, Any]]:
    if not entry_ids:
        return []
    placeholders = ", ".join(f"%(e{i})s" for i in range(len(entry_ids)))
    params: dict[str, Any] = {"uid": viewer_id}
    params.update({f"e{i}": eid for i, eid in enumerate(entry_ids)})
    return fetch_all(
        f"""
        SELECT c.id, c.parent_id AS parentId, c.content, c.is_hot AS isHot,
               c.like_count AS likeCount, c.addTime, c.user_id AS userId,
               c.is_audit AS isAudit, c.top_level AS topLevel, c.entry_id AS entryId,
               u.userName, a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.entry_id IN ({placeholders}) AND c.deleteStatus = 0
          AND c.parent_id IS NULL
          AND c.is_audit = CASE
                WHEN %(uid)s = 0 OR c.user_id != %(uid)s THEN 1
                ELSE c.is_audit END
        ORDER BY c.entry_id, c.is_hot DESC, c.addTime DESC
        """,
        params,
    )


def fetch_replies_for_tops(top_ids: list[int], viewer_id: int) -> list[dict[str, Any]]:
    if not top_ids:
        return []
    tplace = ", ".join(f"%(t{i})s" for i in range(len(top_ids)))
    tparams: dict[str, Any] = {"uid": viewer_id}
    tparams.update({f"t{i}": tid for i, tid in enumerate(top_ids)})
    return fetch_all(
        f"""
        SELECT c.id, c.parent_id AS parentId, c.content, c.is_hot AS isHot,
               c.like_count AS likeCount, c.addTime, c.user_id AS userId,
               c.is_audit AS isAudit, c.top_level AS topLevel,
               u.userName, a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.top_level IN ({tplace}) AND c.deleteStatus = 0
          AND c.parent_id IS NOT NULL
          AND c.is_audit = CASE
                WHEN %(uid)s = 0 OR c.user_id != %(uid)s THEN 1
                ELSE c.is_audit END
        ORDER BY c.top_level, c.addTime DESC
        """,
        tparams,
    )


def fetch_liked_comment_ids(
    comment_ids: list[int], viewer_id: int
) -> list[dict[str, Any]]:
    if not comment_ids:
        return []
    cplace = ", ".join(f"%(c{i})s" for i in range(len(comment_ids)))
    cparams: dict[str, Any] = {"uid": viewer_id}
    cparams.update({f"c{i}": cid for i, cid in enumerate(comment_ids)})
    return fetch_all(
        f"""
        SELECT target_id FROM like_log
        WHERE deleteStatus = 0 AND type = 2 AND is_cancel = 1
          AND user_id = %(uid)s AND target_id IN ({cplace})
        """,
        cparams,
    )


def fetch_comment_like_counts(comment_ids: list[int]) -> list[dict[str, Any]]:
    if not comment_ids:
        return []
    cplace = ", ".join(f"%(c{i})s" for i in range(len(comment_ids)))
    cparams = {f"c{i}": cid for i, cid in enumerate(comment_ids)}
    return fetch_all(
        f"""
        SELECT target_id, COUNT(1) AS cnt FROM like_log
        WHERE deleteStatus = 0 AND type = 2 AND is_cancel = 1
          AND target_id IN ({cplace})
        GROUP BY target_id
        """,
        cparams,
    )


def fetch_parent_users_by_comment_ids(
    parent_ids: list[int],
) -> list[dict[str, Any]]:
    if not parent_ids:
        return []
    pplace = ", ".join(f"%(p{i})s" for i in range(len(parent_ids)))
    pparams = {f"p{i}": pid for i, pid in enumerate(parent_ids)}
    return fetch_all(
        f"""
        SELECT c.id AS commentId, u.userName, u.id AS userId,
               a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.id IN ({pplace})
        """,
        pparams,
    )


def batch_comment_counts(
    entry_ids: list[int], viewer_id: int
) -> list[dict[str, Any]]:
    if not entry_ids:
        return []
    placeholders = ", ".join(f"%(e{i})s" for i in range(len(entry_ids)))
    params: dict[str, Any] = {"uid": viewer_id}
    params.update({f"e{i}": eid for i, eid in enumerate(entry_ids)})
    return fetch_all(
        f"""
        SELECT c.entry_id AS entryId, COUNT(1) AS cnt
        FROM comment c
        WHERE c.entry_id IN ({placeholders}) AND c.deleteStatus = 0
          AND c.parent_id IS NULL
          AND c.is_audit = CASE
                WHEN %(uid)s = 0 OR c.user_id != %(uid)s THEN 1
                ELSE c.is_audit END
        GROUP BY c.entry_id
        """,
        params,
    )
