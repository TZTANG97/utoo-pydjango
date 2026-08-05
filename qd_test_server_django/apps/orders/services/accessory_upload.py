"""订单附件上传 — uploadChildData.ajax"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import accessory as accessory_repo

logger = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024


def save_order_attachment(
    *,
    data: bytes,
    orig_name: str,
    content_type: str,
    acc_type: int = 7,
    exp_of_id: int | None = None,
    child_of_id: int | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    if not data:
        return False, "文件为空", {}
    if len(data) > MAX_BYTES:
        return False, "文件大小不能超过10MB", {}

    file_ext = Path(orig_name or "upload").suffix.lower() or ".bin"
    filename = f"{uuid.uuid4().hex}{file_ext}"
    upload_root = Path(settings.UPLOAD_DIR)
    if not upload_root.is_absolute():
        upload_root = Path(settings.BASE_DIR) / upload_root
    target_dir = upload_root / "order"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / filename).write_bytes(data)
    except OSError as exc:
        logger.exception("save_order_attachment write failed: %s", exc)
        return False, "订单资料上传失败,请重试!", {}

    try:
        config = get_config_row()
    except Exception:
        logger.exception("get_config_row failed during upload")
        config = None
    image_base = image_web_server(config) if config is not None else ""
    path_store = "order"
    if config and config.get("uploadFilePath"):
        path_store = f"{str(config['uploadFilePath']).strip('/')}/order"

    # accessory.ext 多为短字段；MIME 过长会导致 INSERT 失败 → 前端「操作失败」
    mime = (content_type or "").strip() or "application/octet-stream"
    ext_store = (mime[:64] if len(mime) <= 64 else file_ext.lstrip(".") or "bin")[:64]

    now = datetime.now()
    try:
        acc_id = accessory_repo.insert_accessory(
            add_time=now,
            name=filename,
            path=path_store,
            ext=ext_store,
            info=(orig_name or "upload")[:255],
            acc_type=acc_type,
            exp_of_id=exp_of_id,
            child_of_id=child_of_id,
        )
        url_base = (image_base or "").rstrip("/")
        url = f"{url_base}/{path_store}/{filename}" if url_base else f"/{path_store}/{filename}"
        return True, "上传成功", {
            "id": acc_id,
            "name": filename,
            "path": path_store,
            "info": orig_name or "upload",
            "ext": ext_store,
            "type": acc_type,
            "childOfId": child_of_id,
            "url": url,
        }
    except Exception as exc:
        logger.exception("save_order_attachment failed: %s", exc)
        return False, "订单资料上传失败,请重试!", {}
