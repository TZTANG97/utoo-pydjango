"""系统设置（上传/站点/短信/邮件）— 共用 sysconfig id=1。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.conf import settings

from apps.core.db_utils import execute, fetch_one
from qd_common.oss_url import build_oss_object_url


def _oss_kwargs() -> dict[str, str]:
    return {
        "public_base_url": getattr(settings, "OSS_PUBLIC_BASE_URL", "") or "",
        "bucket": getattr(settings, "OSS_BUCKET", "qgongye") or "qgongye",
        "endpoint": getattr(settings, "OSS_ENDPOINT", "") or "",
    }


def _as_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return bool(int(val))
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _bool_bit(val: Any) -> int:
    return 1 if _as_bool(val) else 0


def get_upload_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, imageSaveType, imageWebServer
        FROM sysconfig
        WHERE id = 1
        LIMIT 1
        """
    )
    if not row:
        return {"id": 1, "imageSaveType": "sidYearMonthDayImg", "imageWebServer": ""}
    return {
        "id": row.get("id") or 1,
        "imageSaveType": row.get("imageSaveType") or "",
        "imageWebServer": row.get("imageWebServer") or "",
    }


def save_upload_setting(*, image_save_type: str, image_web_server: str) -> None:
    execute(
        """
        UPDATE sysconfig
        SET imageSaveType = %(imageSaveType)s,
            imageWebServer = %(imageWebServer)s
        WHERE id = 1
        """,
        {
            "imageSaveType": image_save_type,
            "imageWebServer": image_web_server,
        },
    )


def get_site_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT
            sc.id,
            sc.websiteName,
            sc.title,
            sc.hotSearch,
            sc.service_telphone_list,
            sc.websiteLogo_id,
            acc.path AS logo_path,
            acc.name AS logo_name
        FROM sysconfig sc
        LEFT JOIN accessory acc ON acc.id = sc.websiteLogo_id
        WHERE sc.id = 1
        LIMIT 1
        """
    )
    if not row:
        return {
            "id": 1,
            "websiteName": "",
            "title": "",
            "hotSearch": "",
            "service_telphone_list": "",
            "websiteLogo_id": None,
            "websiteLogoUrl": "",
        }
    logo_url = ""
    if row.get("logo_path") or row.get("logo_name"):
        logo_url = build_oss_object_url(
            row.get("logo_path"),
            row.get("logo_name"),
            **_oss_kwargs(),
        )
        # 若 path 已是完整 URL（含 imageWebServer），优先直连
        p = str(row.get("logo_path") or "").strip()
        n = str(row.get("logo_name") or "").strip()
        if p.startswith("http://") or p.startswith("https://"):
            logo_url = f"{p.rstrip('/')}/{n}" if n and n not in p else p
    return {
        "id": row.get("id") or 1,
        "websiteName": row.get("websiteName") or "",
        "title": row.get("title") or "",
        "hotSearch": row.get("hotSearch") or "",
        "service_telphone_list": row.get("service_telphone_list") or "",
        "websiteLogo_id": row.get("websiteLogo_id"),
        "logoPath": row.get("logo_path") or "",
        "logoName": row.get("logo_name") or "",
        "websiteLogoUrl": logo_url,
    }


def save_site_setting(
    *,
    website_name: str,
    title: str,
    hot_search: str,
    service_telphone_list: str,
    website_logo_id: int | None = None,
) -> None:
    hot = (hot_search or "").replace("，", ",")
    if website_logo_id is not None:
        execute(
            """
            UPDATE sysconfig
            SET websiteName = %(websiteName)s,
                title = %(title)s,
                hotSearch = %(hotSearch)s,
                service_telphone_list = %(tel)s,
                websiteLogo_id = %(logo_id)s
            WHERE id = 1
            """,
            {
                "websiteName": website_name,
                "title": title,
                "hotSearch": hot,
                "tel": service_telphone_list,
                "logo_id": website_logo_id,
            },
        )
        return
    execute(
        """
        UPDATE sysconfig
        SET websiteName = %(websiteName)s,
            title = %(title)s,
            hotSearch = %(hotSearch)s,
            service_telphone_list = %(tel)s
        WHERE id = 1
        """,
        {
            "websiteName": website_name,
            "title": title,
            "hotSearch": hot,
            "tel": service_telphone_list,
        },
    )


def update_or_create_website_logo(
    *,
    path: str,
    name: str,
    ext: str = "",
    size: float = 0,
    width: int = 0,
    height: int = 0,
) -> int:
    """更新已有 websiteLogo accessory，或新建并回写 websiteLogo_id。"""
    row = fetch_one("SELECT websiteLogo_id FROM sysconfig WHERE id = 1 LIMIT 1")
    logo_id = int(row["websiteLogo_id"]) if row and row.get("websiteLogo_id") else None
    now = datetime.now()
    if logo_id:
        execute(
            """
            UPDATE accessory
            SET name = %(name)s,
                path = %(path)s,
                ext = %(ext)s,
                size = %(size)s,
                width = %(width)s,
                height = %(height)s
            WHERE id = %(id)s
            """,
            {
                "id": logo_id,
                "name": name,
                "path": path,
                "ext": (ext or "")[:64],
                "size": size,
                "width": width,
                "height": height,
            },
        )
        return logo_id
    execute(
        """
        INSERT INTO accessory (addTime, deleteStatus, name, path, ext, size, width, height)
        VALUES (%(addTime)s, 0, %(name)s, %(path)s, %(ext)s, %(size)s, %(width)s, %(height)s)
        """,
        {
            "addTime": now,
            "name": name,
            "path": path,
            "ext": (ext or "")[:64],
            "size": size,
            "width": width,
            "height": height,
        },
    )
    new_row = fetch_one("SELECT LAST_INSERT_ID() AS id")
    new_id = int(new_row["id"]) if new_row and new_row.get("id") else 0
    if new_id:
        execute(
            "UPDATE sysconfig SET websiteLogo_id = %(id)s WHERE id = 1",
            {"id": new_id},
        )
    return new_id


def get_sms_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, smsEnbale
        FROM sysconfig
        WHERE id = 1
        LIMIT 1
        """
    )
    if not row:
        return {"id": 1, "smsEnbale": False}
    return {"id": row.get("id") or 1, "smsEnbale": _as_bool(row.get("smsEnbale"))}


def save_sms_setting(*, sms_enable: bool) -> None:
    execute(
        "UPDATE sysconfig SET smsEnbale = %(v)s WHERE id = 1",
        {"v": _bool_bit(sms_enable)},
    )


def get_email_setting() -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, emailEnable, emailHost, emailPort, emailUserName, emailUser, emailPws
        FROM sysconfig
        WHERE id = 1
        LIMIT 1
        """
    )
    if not row:
        return {
            "id": 1,
            "emailEnable": False,
            "emailHost": "",
            "emailPort": "25",
            "emailUserName": "",
            "emailUser": "",
            "emailPws": "",
        }
    port = row.get("emailPort")
    return {
        "id": row.get("id") or 1,
        "emailEnable": _as_bool(row.get("emailEnable")),
        "emailHost": row.get("emailHost") or "",
        "emailPort": "" if port is None else str(port),
        "emailUserName": row.get("emailUserName") or "",
        "emailUser": row.get("emailUser") or "",
        "emailPws": row.get("emailPws") or "",
    }


def save_email_setting(
    *,
    email_enable: bool,
    email_host: str,
    email_port: str,
    email_user_name: str,
    email_user: str,
    email_pws: str,
) -> None:
    execute(
        """
        UPDATE sysconfig
        SET emailEnable = %(emailEnable)s,
            emailHost = %(emailHost)s,
            emailPort = %(emailPort)s,
            emailUserName = %(emailUserName)s,
            emailUser = %(emailUser)s,
            emailPws = %(emailPws)s
        WHERE id = 1
        """,
        {
            "emailEnable": _bool_bit(email_enable),
            "emailHost": email_host,
            "emailPort": email_port,
            "emailUserName": email_user_name,
            "emailUser": email_user,
            "emailPws": email_pws,
        },
    )
