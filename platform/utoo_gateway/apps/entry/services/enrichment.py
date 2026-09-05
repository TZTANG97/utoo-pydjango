"""讨论帖子/评论 enrichment — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.entry.repositories import entry as entry_repo
from apps.entry.repositories import social as social_repo
from qd_common.oss_url import build_oss_object_url


def _oss_kwargs() -> dict[str, str]:
    return {
        "public_base_url": getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
        "bucket": getattr(settings, "OSS_BUCKET", "qgongye"),
        "endpoint": getattr(settings, "OSS_ENDPOINT", ""),
    }


def display_name(user_name: str | None, user_id: int | None) -> str:
    if user_name and str(user_name).strip():
        return str(user_name)
    return f"默认用户{user_id or ''}"


def parent_user_names(parent_id: int | None) -> tuple[str, str, str]:
    if not parent_id:
        return "", "", ""
    prow = social_repo.get_parent_comment_user(int(parent_id))
    if not prow:
        return "", "", ""
    uid = int(prow.get("userId") or 0)
    return (
        display_name(prow.get("userName"), uid),
        prow.get("name") or "",
        prow.get("path") or "",
    )


def accessory_list_for_entry(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in photos:
        item = dict(row)
        p = (item.get("path") or "").strip()
        n = (item.get("name") or "").strip()
        if p.startswith("http://") or p.startswith("https://"):
            parts = p.replace("\\", "/").split("/")
            if len(parts) >= 2:
                item["name"] = parts[-1]
                item["path"] = "/".join(parts[:-1]).split(".com/", 1)[-1]
        item["imageUrl"] = build_oss_object_url(
            item.get("path"), item.get("name"), **_oss_kwargs()
        )
        out.append(item)
    return out


def comment_like_count(comment_id: int) -> int:
    return social_repo.count_comment_likes(comment_id)


def enrich_comment(comment: dict[str, Any], *, viewer_id: int) -> dict[str, Any]:
    cid = int(comment["id"])
    cuid = int(comment.get("userId") or 0)
    comment["userName"] = display_name(comment.get("userName"), cuid)
    comment["deleteQx"] = viewer_id == cuid
    comment["isLike"] = (
        1
        if social_repo.comment_liked_by_user(comment_id=cid, user_id=viewer_id)
        else 0
    )
    comment["likeCount"] = comment_like_count(cid)
    puser, pname, ppath = parent_user_names(comment.get("parentId"))
    if puser:
        comment["puserName"] = puser
        comment["pname"] = pname
        comment["ppath"] = ppath
    comment["avatar"] = build_oss_object_url(
        comment.get("path"), comment.get("name"), **_oss_kwargs()
    )
    replies = entry_repo.fetch_replies(top_level=cid, viewer_id=viewer_id)
    comment["replies"] = [enrich_comment(rep, viewer_id=viewer_id) for rep in replies]
    return comment


def enrich_entry(entry: dict[str, Any], *, viewer_id: int) -> dict[str, Any]:
    eid = int(entry["id"])
    euid = int(entry.get("userId") or 0)
    entry["deleteQx"] = viewer_id == euid
    entry["isLike"] = (
        1 if social_repo.favorite_exists(entry_id=eid, user_id=viewer_id, fav_type=1) else 0
    )
    entry["isCollect"] = (
        1 if social_repo.favorite_exists(entry_id=eid, user_id=viewer_id, fav_type=2) else 0
    )
    photos = entry_repo.fetch_entry_photos(entry.get("photoIds") or "")
    entry["accessoryList"] = accessory_list_for_entry(photos)
    comments = entry_repo.fetch_top_comments(entry_id=eid, viewer_id=viewer_id)
    entry["commentList"] = [enrich_comment(c, viewer_id=viewer_id) for c in comments]
    return entry
