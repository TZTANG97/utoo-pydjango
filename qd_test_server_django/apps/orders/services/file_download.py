"""附件下载 — downloadFile.ajax"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from django.conf import settings

from apps.core.db_utils import fetch_one

logger = logging.getLogger(__name__)


def fetch_accessory_row(accessory_id: int) -> Optional[dict]:
    return fetch_one(
        """
        SELECT id, name, path, info, ext
        FROM accessory
        WHERE id = %(aid)s AND deleteStatus = 0
        LIMIT 1
        """,
        {"aid": accessory_id},
    )


def build_download_filename(acc: dict) -> str:
    file_name = (acc.get("name") or "download").strip()
    info = (acc.get("info") or file_name).strip()
    dot = info.rfind(".")
    if dot != -1:
        info = info[:dot]
    ext_dot = file_name.rfind(".")
    ext = file_name[ext_dot:] if ext_dot != -1 else ""
    return f"{info}{ext}" if info else file_name


def _object_key(path: str, name: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    n = (name or "").strip().lstrip("/")
    for sep in (
        getattr(settings, "OSS_PUBLIC_BASE_URL", ""),
        getattr(settings, "IMAGE_WEB_SERVER", ""),
    ):
        if sep and sep in p:
            p = p.split(sep.rstrip("/"), 1)[-1].lstrip("/")
            break
    if p and n:
        return f"{p.strip('/')}/{n}"
    return p or n


def _try_oss_download(key: str) -> Optional[bytes]:
    if not (
        getattr(settings, "OSS_ACCESS_KEY_ID", "")
        and getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
    ):
        return None
    try:
        import oss2

        endpoint = (settings.OSS_ENDPOINT or "").replace("https://", "").replace(
            "http://", ""
        )
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, endpoint, settings.OSS_BUCKET)
        return bucket.get_object(key).read()
    except Exception as exc:
        logger.warning("OSS download failed key=%s: %s", key, exc)
        return None


def load_accessory_bytes(accessory_id: int) -> tuple[Optional[bytes], str]:
    acc = fetch_accessory_row(accessory_id)
    if not acc:
        return None, ""
    download_name = build_download_filename(acc)
    key = _object_key(acc.get("path") or "", acc.get("name") or "")

    data = _try_oss_download(key) if key else None
    if data:
        return data, download_name

    local_path = Path(settings.UPLOAD_DIR) / key.replace("/", os.sep)
    if local_path.is_file():
        return local_path.read_bytes(), download_name

    logger.warning("attachment not found id=%s key=%s", accessory_id, key)
    return None, download_name
