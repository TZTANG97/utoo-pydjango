"""wx_openid_info — 公众号 openid ↔ unionid（对齐 Java WxTempInfoMapper）。"""
from __future__ import annotations

import logging
from datetime import datetime

from apps.core.db_utils import execute, fetch_one

logger = logging.getLogger(__name__)


def get_gzh_openid_by_unionid(unionid: str) -> str | None:
    if not unionid:
        return None
    try:
        row = fetch_one(
            """
            SELECT gzh_openid FROM wx_openid_info
            WHERE unionid = %(u)s AND type = 2
            LIMIT 1
            """,
            {"u": unionid},
        )
    except Exception as exc:
        logger.warning("wx_openid_info lookup failed: %s", exc)
        return None
    return str(row["gzh_openid"]) if row and row.get("gzh_openid") else None


def get_unionid_by_gzh_openid(openid: str) -> str | None:
    if not openid:
        return None
    try:
        row = fetch_one(
            """
            SELECT unionid FROM wx_openid_info
            WHERE gzh_openid = %(oid)s AND type = 2
            LIMIT 1
            """,
            {"oid": openid},
        )
    except Exception as exc:
        logger.warning("wx_openid_info unionid lookup failed: %s", exc)
        return None
    return str(row["unionid"]) if row and row.get("unionid") else None


def insert_openid_unionid(openid: str, unionid: str) -> None:
    if not openid or not unionid:
        return
    if get_gzh_openid_by_unionid(unionid):
        return
    try:
        execute(
            """
            INSERT INTO wx_openid_info (gzh_openid, unionid, create_time, type)
            VALUES (%(oid)s, %(u)s, %(t)s, 2)
            """,
            {"oid": openid, "u": unionid, "t": datetime.now()},
        )
    except Exception as exc:
        logger.warning("wx_openid_info insert failed: %s", exc)


def update_sy_user_unionid(openid: str, unionid: str) -> None:
    if not openid or not unionid:
        return
    try:
        execute(
            """
            UPDATE sy_users SET wx_unionid = %(u)s
            WHERE wx_openid = %(oid)s
            """,
            {"u": unionid, "oid": openid},
        )
    except Exception as exc:
        logger.debug("sy_users unionid update skipped: %s", exc)
