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
