"""讨论列表批量 enrichment — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.entry.repositories import social as social_repo
from apps.entry.services import enrichment
from qd_common.oss_url import build_oss_object_url


def _oss_kwargs() -> dict[str, str]:
    return {
        "public_base_url": getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
        "bucket": getattr(settings, "OSS_BUCKET", "qgongye"),
        "endpoint": getattr(settings, "OSS_ENDPOINT", ""),
    }


def _batch_favorites(entry_ids: list[int], viewer_id: int) -> tuple[set[int], set[int]]:
    liked: set[int] = set()
    collected: set[int] = set()
    for r in social_repo.batch_favorite_entry_ids(entry_ids, viewer_id):
        eid = int(r["entry_id"])
        if int(r["type"]) == 1:
            liked.add(eid)
        elif int(r["type"]) == 2:
            collected.add(eid)
    return liked, collected


def _batch_photos(entries: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    id_set: set[int] = set()
    entry_photo_map: dict[int, list[int]] = {}
    for entry in entries:
        eid = int(entry["id"])
        ids = [
            int(p)
            for p in str(entry.get("photoIds") or "").split(",")
            if p.strip().isdigit()
        ]
        entry_photo_map[eid] = ids
        id_set.update(ids)
    rows = social_repo.fetch_accessories_by_ids(id_set)
    by_id = {int(r["id"]): r for r in rows}
    result: dict[int, list[dict[str, Any]]] = {}
    for eid, pids in entry_photo_map.items():
        photos = [by_id[i] for i in pids if i in by_id]
        result[eid] = enrichment.accessory_list_for_entry(photos)
    return result


def _batch_comment_tree(
    entry_ids: list[int], viewer_id: int
) -> dict[int, list[dict[str, Any]]]:
    if not entry_ids:
        return {}

    top_rows = social_repo.fetch_top_comments_for_entries(entry_ids, viewer_id)
    top_by_entry: dict[int, list[dict[str, Any]]] = {}
    top_ids: list[int] = []
    for row in top_rows:
        c = dict(row)
        eid = int(c["entryId"])
        top_by_entry.setdefault(eid, []).append(c)
        top_ids.append(int(c["id"]))

    reply_by_top: dict[int, list[dict[str, Any]]] = {}
    for row in social_repo.fetch_replies_for_tops(top_ids, viewer_id):
        c = dict(row)
        tl = int(c.get("topLevel") or 0)
        reply_by_top.setdefault(tl, []).append(c)

    all_comment_ids = top_ids + [
        int(c["id"]) for reps in reply_by_top.values() for c in reps
    ]
    liked_comments = {
        int(r["target_id"])
        for r in social_repo.fetch_liked_comment_ids(all_comment_ids, viewer_id)
    }
    like_counts = {
        int(r["target_id"]): int(r["cnt"])
        for r in social_repo.fetch_comment_like_counts(all_comment_ids)
    }

    parent_ids = {
        int(c.get("parentId"))
        for reps in reply_by_top.values()
        for c in reps
        if c.get("parentId")
    }
    parent_users = {
        int(r["commentId"]): r
        for r in social_repo.fetch_parent_users_by_comment_ids(list(parent_ids))
    }

    def _finalize(comment: dict[str, Any]) -> dict[str, Any]:
        cid = int(comment["id"])
        cuid = int(comment.get("userId") or 0)
        comment["userName"] = enrichment.display_name(comment.get("userName"), cuid)
        comment["deleteQx"] = viewer_id == cuid
        comment["isLike"] = 1 if cid in liked_comments else 0
        comment["likeCount"] = like_counts.get(cid, int(comment.get("likeCount") or 0))
        comment["avatar"] = build_oss_object_url(
            comment.get("path"), comment.get("name"), **_oss_kwargs()
        )
        return comment

    out: dict[int, list[dict[str, Any]]] = {}
    for eid, tops in top_by_entry.items():
        tree: list[dict[str, Any]] = []
        for top in tops:
            t = _finalize(top)
            tid = int(t["id"])
            replies = []
            for rep in reply_by_top.get(tid, []):
                r = _finalize(rep)
                pid = int(rep.get("parentId") or 0)
                pu = parent_users.get(pid)
                if pu:
                    r["puserName"] = enrichment.display_name(
                        pu.get("userName"), int(pu.get("userId") or 0)
                    )
                    r["pname"] = pu.get("name") or ""
                    r["ppath"] = pu.get("path") or ""
                replies.append(r)
            t["replies"] = replies
            tree.append(t)
        out[eid] = tree
    return out


def _batch_comment_counts(entry_ids: list[int], viewer_id: int) -> dict[int, int]:
    return {
        int(r["entryId"]): int(r["cnt"])
        for r in social_repo.batch_comment_counts(entry_ids, viewer_id)
    }


def enrich_entries_for_list(
    entries: list[dict[str, Any]],
    *,
    viewer_id: int,
    include_comments: bool = False,
) -> list[dict[str, Any]]:
    if not entries:
        return []
    entry_ids = [int(e["id"]) for e in entries]
    liked, collected = _batch_favorites(entry_ids, viewer_id)
    photo_map = _batch_photos(entries)
    comment_counts = (
        {} if include_comments else _batch_comment_counts(entry_ids, viewer_id)
    )
    comment_map = (
        _batch_comment_tree(entry_ids, viewer_id) if include_comments else {}
    )

    out: list[dict[str, Any]] = []
    for entry in entries:
        eid = int(entry["id"])
        euid = int(entry.get("userId") or 0)
        item = dict(entry)
        item["deleteQx"] = viewer_id == euid if viewer_id else False
        item["isLike"] = 1 if eid in liked else 0
        item["isCollect"] = 1 if eid in collected else 0
        if item.get("likeTime") and not item.get("collectTime"):
            item["collectTime"] = item.get("likeTime")
        item["accessoryList"] = photo_map.get(eid, [])
        item["commentList"] = comment_map.get(eid, [])
        item["commentCount"] = (
            len(item["commentList"])
            if include_comments
            else comment_counts.get(eid, 0)
        )
        out.append(item)
    return out


def enrich_single_entry_comments(entry_id: int, viewer_id: int) -> list[dict[str, Any]]:
    cmap = _batch_comment_tree([entry_id], viewer_id)
    return cmap.get(entry_id, [])
