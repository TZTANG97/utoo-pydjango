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

    ext = Path(orig_name or "upload").suffix.lower() or ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_root = Path(settings.UPLOAD_DIR)
    target_dir = upload_root / "order"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(data)

    config = get_config_row()
    image_base = image_web_server(config)
    path_store = "order"
    if config and config.get("uploadFilePath"):
        path_store = f"{str(config['uploadFilePath']).strip('/')}/order"

    now = datetime.now()
    try:
        acc_id = accessory_repo.insert_accessory(
            add_time=now,
            name=filename,
            path=path_store,
            ext=content_type or "application/octet-stream",
            info=orig_name or "upload",
            acc_type=acc_type,
            exp_of_id=exp_of_id,
            child_of_id=child_of_id,
        )
        url_base = image_base.rstrip("/")
        return True, "上传成功", {
            "id": acc_id,
            "name": filename,
            "path": path_store,
            "info": orig_name or "upload",
            "ext": content_type or "application/octet-stream",
            "type": acc_type,
            "childOfId": child_of_id,
            "url": f"{url_base}/{path_store}/{filename}",
        }
    except Exception as exc:
        logger.exception("save_order_attachment failed: %s", exc)
        return False, "订单资料上传失败,请重试!", {}
