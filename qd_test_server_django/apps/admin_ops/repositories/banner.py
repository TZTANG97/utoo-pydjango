from __future__ import annotations

from typing import Any

from apps.admin_ops.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_banners(
    *,
    banner_type: int | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE b.deleteStatus = 0"
    params: dict[str, Any] = {}
    if banner_type is not None:
        where += " AND b.banner_type = %(banner_type)s"
        params["banner_type"] = banner_type
    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM banner b
            INNER JOIN accessory a ON b.banner_id = a.id
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            b.id AS bid,
            b.project_class AS projectClass,
            b.website,
            b.addTime AS time,
            b.deleteStatus,
            b.banner_id AS bannerId,
            b.sort,
            b.title,
            b.badescribe,
            b.subheading,
            b.titlesize,
            b.titlecolor,
            b.badescribesize,
            b.badescribecolor,
            b.subheadingsize,
            b.subheadingcolor,
            a.id AS accessoryId,
            a.path,
            a.name,
            b.is_show AS isShow,
            b.banner_type AS bannerType,
            b.platform_type AS platformType,
            pt.name AS ptName
        FROM banner b
        INNER JOIN accessory a ON b.banner_id = a.id
        LEFT JOIN pt_type pt ON b.platform_type = pt.id
        {where}
        ORDER BY b.sort ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_banner(bid: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            b.id AS bid,
            b.project_class AS projectClass,
            b.website,
            b.addTime AS time,
            b.banner_id AS bannerId,
            b.sort,
            b.title,
            b.badescribe,
            b.subheading,
            b.titlesize,
            b.titlecolor,
            b.badescribesize,
            b.badescribecolor,
            b.subheadingsize,
            b.subheadingcolor,
            b.is_show AS isShow,
            b.banner_type AS bannerType,
            b.platform_type AS platformType,
            a.id AS accessoryId,
            a.path,
            a.name
        FROM banner b
        INNER JOIN accessory a ON b.banner_id = a.id
        WHERE b.deleteStatus = 0 AND b.id = %(bid)s
        LIMIT 1
        """,
        {"bid": bid},
    )


def insert_banner(fields: dict[str, Any]) -> int:
    return execute_insert(
        """
        INSERT INTO banner
            (addTime, deleteStatus, banner_id, sort, is_show,
             title, badescribe, subheading, titlesize, titlecolor,
             badescribesize, badescribecolor, subheadingsize, subheadingcolor,
             project_class, website, banner_type, platform_type)
        VALUES
            (NOW(), 0, %(banner_id)s, %(sort)s, %(is_show)s,
             %(title)s, %(badescribe)s, %(subheading)s, %(titlesize)s, %(titlecolor)s,
             %(badescribesize)s, %(badescribecolor)s, %(subheadingsize)s, %(subheadingcolor)s,
             %(project_class)s, %(website)s, %(banner_type)s, %(platform_type)s)
        """,
        fields,
    )


def update_banner(banner_id: int, fields: dict[str, Any]) -> None:
    execute(
        """
        UPDATE banner
        SET sort = %(sort)s,
            banner_id = %(banner_id)s,
            is_show = %(is_show)s,
            title = %(title)s,
            badescribe = %(badescribe)s,
            subheading = %(subheading)s,
            titlesize = %(titlesize)s,
            titlecolor = %(titlecolor)s,
            badescribesize = %(badescribesize)s,
            badescribecolor = %(badescribecolor)s,
            subheadingsize = %(subheadingsize)s,
            subheadingcolor = %(subheadingcolor)s,
            project_class = %(project_class)s,
            website = %(website)s,
            banner_type = %(banner_type)s,
            platform_type = %(platform_type)s
        WHERE id = %(id)s
        """,
        {**fields, "id": banner_id},
    )


def update_isshow(bid: int, is_show: int) -> None:
    execute(
        "UPDATE banner SET is_show = %(is_show)s WHERE id = %(bid)s",
        {"bid": bid, "is_show": is_show},
    )


def delete_banner(bid: int) -> int:
    return execute("DELETE FROM banner WHERE id = %(id)s", {"id": bid})
