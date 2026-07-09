"""头像上传 — updatePhone.ajax"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.auth_pc.repositories import accessory as accessory_repo
from apps.core.services.sysconfig import get_config_row, image_web_server

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_BYTES = 2 * 1024 * 1024


def save_user_avatar(
    *, data: bytes, content_type: str
) -> tuple[bool, str, dict[str, Any]]:
    ct = (content_type or "").lower()
    if ct not in ALLOWED_TYPES:
        return False, "只能上传PNG和JPG格式", {}
    if len(data) > MAX_BYTES:
        return False, "头像大小不能超过2M", {}
    if not data:
        return False, "文件为空", {}

    ext = ".jpg" if "jpeg" in ct or ct == "image/jpg" else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = "user/userPhoto"
    target_dir = Path(settings.UPLOAD_DIR) / rel_path.replace("/", Path.sep)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(data)

    config = get_config_row()
    image_base = image_web_server(config) or getattr(settings, "IMAGE_WEB_SERVER", "")
    url = f"{image_base.rstrip('/')}/{rel_path}/{filename}"

    try:
        image_id = accessory_repo.insert_avatar_row(
            add_time=datetime.now(),
            filename=filename,
            path=rel_path,
            content_type=ct,
        )
        return True, "上传成功", {
            "url": url,
            "imageId": image_id,
            "path": rel_path,
            "name": filename,
            "width": 0,
            "height": 0,
            "ext": ct,
        }
    except Exception as exc:
        logger.exception("save_user_avatar failed: %s", exc)
        return False, "头像上传失败,请重试!", {}
