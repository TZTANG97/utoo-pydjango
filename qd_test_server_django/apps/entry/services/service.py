"""讨论社区业务 — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any, Optional

from django.conf import settings
from django.db import transaction

from apps.entry.repositories import entry as entry_repo
from apps.entry.repositories import entry_write as entry_write_repo
from apps.entry.services import enrichment, enrichment_bulk
from qd_common.oss_url import build_oss_object_url


def _datatable(
    entries: list[dict[str, Any]], draw: str, *, total: int | None = None
) -> dict[str, Any]:
    n = total if total is not None else len(entries)
    d = int(draw) if str(draw).isdigit() else 1
    return {
        "data": entries,
        "draw": d,
        "recordsTotal": n,
        "recordsFiltered": n,
    }


def _oss_kwargs() -> dict[str, str]:
    return {
        "public_base_url": getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
        "bucket": getattr(settings, "OSS_BUCKET", "qgongye"),
        "endpoint": getattr(settings, "OSS_ENDPOINT", ""),
    }


class EntryService:
    @staticmethod
    def comment_tree(
        *,
        viewer_id: int,
        start: str = "0",
        length: str = "10",
        draw: str = "1",
        order_by: str = "addTime",
        order_type: str = "desc",
    ) -> dict[str, Any]:
        offset, limit = entry_repo.page_offset_limit(start, length)
        total = entry_repo.count_entries(is_audit=1)
        rows = entry_repo.fetch_entries_page(
            offset=offset,
            limit=limit,
            is_audit=1,
            order_by=order_by,
            order_type=order_type,
            sort_viewer_id=viewer_id,
        )
        data = enrichment_bulk.enrich_entries_for_list(
            rows, viewer_id=viewer_id, include_comments=False
        )
        return _datatable(data, draw, total=total)

    @staticmethod
    def publish_list(
        *,
        user_id: int,
        start: str = "0",
        length: str = "10",
        draw: str = "1",
        order_by: str = "addTime",
        order_type: str = "desc",
    ) -> dict[str, Any]:
        offset, limit = entry_repo.page_offset_limit(start, length)
        total = entry_repo.count_entries(user_id=user_id, is_audit=1)
        rows = entry_repo.fetch_entries_page(
            offset=offset,
            limit=limit,
            user_id=user_id,
            is_audit=1,
            order_by=order_by,
            order_type=order_type,
            sort_viewer_id=user_id,
        )
        data = enrichment_bulk.enrich_entries_for_list(
            rows, viewer_id=user_id, include_comments=False
        )
        return _datatable(data, draw, total=total)

    @staticmethod
    def like_list(
        *,
        user_id: int,
        fav_type: int,
        start: str = "0",
        length: str = "10",
        draw: str = "1",
    ) -> dict[str, Any]:
        offset, limit = entry_repo.page_offset_limit(start, length)
        total = entry_repo.count_liked_entries(user_id=user_id, fav_type=fav_type)
        rows = entry_repo.fetch_liked_entries_page(
            offset=offset,
            limit=limit,
            user_id=user_id,
            fav_type=fav_type,
        )
        data = enrichment_bulk.enrich_entries_for_list(
            rows, viewer_id=user_id, include_comments=False
        )
        return _datatable(data, draw, total=total)

    @staticmethod
    def entry_comments(*, viewer_id: int, entry_id: int) -> list[dict[str, Any]]:
        return enrichment_bulk.enrich_single_entry_comments(entry_id, viewer_id)

    @staticmethod
    def entry_detail(*, user_id: int, entry_id: int) -> Optional[dict[str, Any]]:
        entry = entry_repo.fetch_entry_by_id(entry_id)
        if not entry:
            return None
        rows = enrichment_bulk.enrich_entries_for_list(
            [entry], viewer_id=user_id, include_comments=True
        )
        return rows[0] if rows else None

    @staticmethod
    def insert_entry(
        *,
        user_id: int,
        title: str,
        content: str,
        photo_ids: str = "",
    ) -> tuple[bool, str]:
        entry_write_repo.insert_entry(
            user_id=user_id,
            title=title or "",
            content=content or "",
            photo_ids=photo_ids or "",
        )
        return True, "新增成功"

    @staticmethod
    def delete_entry(entry_id: int) -> tuple[bool, str]:
        with transaction.atomic():
            entry_write_repo.delete_entry_row(entry_id)
            entry_write_repo.soft_delete_comments_by_entry(entry_id)
        return True, "删除成功"

    @staticmethod
    def soft_delete_comment(comment_id: int) -> tuple[bool, str]:
        row = entry_write_repo.get_comment_top_level(comment_id)
        if not row:
            return False, "评论不存在"
        with transaction.atomic():
            entry_write_repo.soft_delete_comment(comment_id)
            top = row.get("top_level") or row["id"]
            entry_write_repo.soft_delete_comment_thread(int(top))
        return True, "删除成功"

    @staticmethod
    def toggle_entry_favorite(
        *,
        user_id: int,
        entry_id: int,
        is_flag: str,
        fav_type: int,
    ) -> Optional[dict[str, Any]]:
        row = entry_write_repo.get_entry_favorite_row(
            entry_id=entry_id, user_id=user_id, fav_type=fav_type
        )
        cancel_val = 0 if is_flag == "0" else 1
        with transaction.atomic():
            if row:
                entry_write_repo.update_favorite_cancel(int(row["id"]), cancel_val)
            elif is_flag == "1":
                entry_write_repo.insert_entry_favorite(
                    entry_id=entry_id, user_id=user_id, fav_type=fav_type
                )
        entry = entry_repo.fetch_entry_by_id(entry_id, require_audit=False)
        if not entry:
            return None
        rows = enrichment_bulk.enrich_entries_for_list(
            [entry], viewer_id=user_id, include_comments=False
        )
        return rows[0] if rows else None

    @staticmethod
    def toggle_comment_like(
        *,
        user_id: int,
        comment_id: int,
        is_flag: str,
    ) -> Optional[dict[str, Any]]:
        row = entry_write_repo.get_comment_like_row(
            comment_id=comment_id, user_id=user_id
        )
        with transaction.atomic():
            if is_flag == "0":
                if row and int(row.get("is_cancel") or 0) == 1:
                    entry_write_repo.update_comment_like_cancel(int(row["id"]), 0)
            elif is_flag == "1":
                if row:
                    entry_write_repo.update_comment_like_cancel(int(row["id"]), 1)
                else:
                    entry_write_repo.insert_comment_like(
                        user_id=user_id, comment_id=comment_id
                    )
        crow = entry_write_repo.get_comment_detail(comment_id)
        if not crow:
            return None
        comment = dict(crow)
        comment["isLike"] = 1 if is_flag == "1" else 0
        comment["likeCount"] = enrichment.comment_like_count(comment_id)
        return comment

    @staticmethod
    def insert_comment(
        *,
        user_id: int,
        entry_id: int,
        content: str,
        parent_id: str = "",
        top_level: str = "",
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        pid = int(parent_id) if parent_id and parent_id.isdigit() else None
        tl = int(top_level) if top_level and top_level.isdigit() else None
        new_id = entry_write_repo.insert_comment(
            user_id=user_id,
            entry_id=entry_id,
            content=content or "",
            parent_id=pid,
            top_level=tl,
        )
        if not new_id:
            return False, "评论失败", None
        detail = entry_write_repo.get_comment_detail_full(int(new_id))
        if not detail:
            return True, "操作成功", None
        comment = dict(detail)
        comment["userName"] = enrichment.display_name(
            comment.get("userName"), int(comment.get("userId") or 0)
        )
        if pid:
            puser, pname, ppath = enrichment.parent_user_names(pid)
            comment["puserName"] = puser
            comment["pname"] = pname
            comment["ppath"] = ppath
        comment["avatar"] = build_oss_object_url(
            comment.get("path"), comment.get("name"), **_oss_kwargs()
        )
        return True, "操作成功", comment
