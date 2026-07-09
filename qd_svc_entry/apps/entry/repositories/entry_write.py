from typing import Any, Optional

from apps.core.db_utils import execute, execute_insert, fetch_one


def insert_entry(
    *,
    user_id: int,
    title: str,
    content: str,
    photo_ids: str,
) -> None:
    execute(
        """
        INSERT INTO entry (addTime, deleteStatus, user_id, title, content, photo_ids)
        VALUES (NOW(), 0, %(uid)s, %(title)s, %(content)s, %(photos)s)
        """,
        {
            "uid": user_id,
            "title": title,
            "content": content,
            "photos": photo_ids,
        },
    )


def delete_entry_row(entry_id: int) -> None:
    execute("DELETE FROM entry WHERE id = %(eid)s", {"eid": entry_id})


def soft_delete_comments_by_entry(entry_id: int) -> None:
    execute(
        "UPDATE comment SET deleteStatus = 1 WHERE entry_id = %(eid)s",
        {"eid": entry_id},
    )


def get_comment_top_level(comment_id: int) -> dict[str, Any] | None:
    return fetch_one(
        "SELECT id, top_level FROM comment WHERE id = %(cid)s LIMIT 1",
        {"cid": comment_id},
    )


def soft_delete_comment(comment_id: int) -> None:
    execute(
        "UPDATE comment SET deleteStatus = 1 WHERE id = %(cid)s",
        {"cid": comment_id},
    )


def soft_delete_comment_thread(top_level: int) -> None:
    execute(
        """
        UPDATE comment SET deleteStatus = 1
        WHERE top_level = %(tl)s OR id = %(tl)s
        """,
        {"tl": top_level},
    )


def get_entry_favorite_row(
    *, entry_id: int, user_id: int, fav_type: int
) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, is_cancel FROM favorite_like
        WHERE deleteStatus = 0 AND entry_id = %(eid)s
          AND user_id = %(uid)s AND type = %(tp)s
        ORDER BY id DESC LIMIT 1
        """,
        {"eid": entry_id, "uid": user_id, "tp": fav_type},
    )


def update_favorite_cancel(favorite_id: int, cancel_val: int) -> None:
    execute(
        "UPDATE favorite_like SET is_cancel = %(c)s WHERE id = %(id)s",
        {"c": cancel_val, "id": favorite_id},
    )


def insert_entry_favorite(
    *, entry_id: int, user_id: int, fav_type: int
) -> None:
    execute(
        """
        INSERT INTO favorite_like
            (addTime, deleteStatus, entry_id, user_id, type, is_cancel)
        VALUES (NOW(), 0, %(eid)s, %(uid)s, %(tp)s, 1)
        """,
        {"eid": entry_id, "uid": user_id, "tp": fav_type},
    )


def get_comment_like_row(*, comment_id: int, user_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, is_cancel FROM like_log
        WHERE deleteStatus = 0 AND target_id = %(cid)s
          AND user_id = %(uid)s AND type = 2
        ORDER BY id DESC LIMIT 1
        """,
        {"cid": comment_id, "uid": user_id},
    )


def update_comment_like_cancel(like_id: int, cancel_val: int) -> None:
    execute(
        "UPDATE like_log SET is_cancel = %(c)s WHERE id = %(id)s",
        {"c": cancel_val, "id": like_id},
    )


def insert_comment_like(*, user_id: int, comment_id: int) -> None:
    execute(
        """
        INSERT INTO like_log
            (addTime, deleteStatus, user_id, target_id, type, is_cancel)
        VALUES (NOW(), 0, %(uid)s, %(cid)s, 2, 1)
        """,
        {"uid": user_id, "cid": comment_id},
    )


def insert_comment(
    *,
    user_id: int,
    entry_id: int,
    content: str,
    parent_id: Optional[int],
    top_level: Optional[int],
) -> int:
    return execute_insert(
        """
        INSERT INTO comment
            (addTime, deleteStatus, user_id, entry_id, content, parent_id, top_level)
        VALUES (NOW(), 0, %(uid)s, %(eid)s, %(content)s, %(pid)s, %(tl)s)
        """,
        {
            "uid": user_id,
            "eid": entry_id,
            "content": content,
            "pid": parent_id,
            "tl": top_level,
        },
    )


def get_comment_detail(comment_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT c.id, c.parent_id AS parentId, c.content, c.user_id AS userId,
               u.userName
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        WHERE c.id = %(cid)s LIMIT 1
        """,
        {"cid": comment_id},
    )


def get_comment_detail_full(comment_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT c.id, c.parent_id AS parentId, c.content, c.user_id AS userId,
               c.entry_id AS entryId, c.top_level AS topLevel, c.addTime,
               u.userName, a.path, a.name
        FROM comment c
        LEFT JOIN exp_user u ON c.user_id = u.id
        LEFT JOIN accessory a ON u.photo_id = a.id
        WHERE c.id = %(cid)s LIMIT 1
        """,
        {"cid": comment_id},
    )
