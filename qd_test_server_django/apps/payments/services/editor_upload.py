"""富文本图片 — seller/swf_upload.ajax"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.core.db_utils import execute_insert
from apps.core.services.sysconfig import get_config_row, image_web_server

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "image/gif",
    "image/webp",
}
MAX_BYTES = 5 * 1024 * 1024
UPLOAD_DIR_GOODS = "goods"


def upload_editor_image(
    *, data: bytes, filename_hint: str, content_type: str
) -> tuple[bool, str, dict[str, Any]]:
    ct = (content_type or "").lower()
    if ct and ct not in ALLOWED_IMAGE_TYPES:
        ext = Path(filename_hint or "").suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            return False, "仅支持图片格式", {}
    if not data:
        return False, "文件为空", {}
    if len(data) > MAX_BYTES:
        return False, "图片大小不能超过5MB", {}

    ext = ".jpg"
    if "png" in ct or (filename_hint or "").lower().endswith(".png"):
        ext = ".png"
    elif "gif" in ct:
        ext = ".gif"
    elif "webp" in ct:
        ext = ".webp"

    filename = f"{uuid.uuid4().hex}{ext}"
    path_store = UPLOAD_DIR_GOODS
    upload_root = Path(settings.UPLOAD_DIR)
    target_dir = upload_root / path_store
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(data)

    config = get_config_row()
    image_base = image_web_server(config) or getattr(settings, "IMAGE_WEB_SERVER", "")
    public_url = f"{image_base.rstrip('/')}/{path_store}/{filename}"

    try:
        image_id = execute_insert(
            """
            INSERT INTO accessory
                (addTime, deleteStatus, name, path, ext, width, height)
            VALUES (%(t)s, 0, %(name)s, %(path)s, %(ext)s, 0, 0)
            """,
            {
                "t": datetime.now(),
                "name": filename,
                "path": path_store,
                "ext": ct or f"image/{ext.lstrip('.')}",
            },
        )
        return True, "上传成功", {
            "url": public_url,
            "id": image_id,
            "remainSpace": 0,
        }
    except Exception as exc:
        logger.exception("upload_editor_image failed: %s", exc)
        return False, "图片保存失败", {}
