import random

from apps.core.db_utils import fetch_all
from apps.core.services.sysconfig import get_config_row, image_web_server


def list_pc_banners() -> list[dict]:
    rows = fetch_all(
        """
        SELECT b.is_show, b.project_class, b.website, a.path, a.name
        FROM banner b
        INNER JOIN accessory a ON b.banner_id = a.id
        WHERE b.deleteStatus = 0 AND b.banner_type = 0
        ORDER BY b.sort ASC
        """
    )
    base = image_web_server(get_config_row())
    out = []
    for row in rows:
        path = (row.get("path") or "").strip("/")
        name = row.get("name") or ""
        pic_url = ""
        if name:
            pic_url = f"{base}/{path}/{name}" if path else f"{base}/{name}"
        out.append(
            {
                "picUrl": pic_url,
                "is_show": row.get("is_show"),
                "project_class": row.get("project_class"),
                "website": row.get("website"),
            }
        )
    return out


def list_by_is_show_and_type(
    *,
    is_show: int,
    banner_type: int,
    platform_type: str,
) -> list[dict]:
    """对齐 Java BannerMapping.listByIsShowAndType。"""
    return fetch_all(
        """
        SELECT
            b.id AS bid,
            b.project_class,
            b.website,
            b.addTime AS time,
            b.deleteStatus,
            b.banner_id,
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
            b.is_show
        FROM banner b
        INNER JOIN accessory a ON b.banner_id = a.id
        WHERE b.deleteStatus = 0
          AND b.banner_type = %(banner_type)s
          AND b.is_show = %(is_show)s
          AND b.platform_type = %(platform_type)s
        ORDER BY b.sort ASC
        """,
        {
            "banner_type": banner_type,
            "is_show": is_show,
            "platform_type": platform_type,
        },
    )


def pick_random_cover_banner(*, platform_type: str) -> dict | None:
    """小程序封面：is_show=1, banner_type=2, platform_type=2(愉兔)/3(途哲)。"""
    rows = list_by_is_show_and_type(
        is_show=1, banner_type=2, platform_type=str(platform_type)
    )
    if not rows:
        return None
    return random.choice(rows)
