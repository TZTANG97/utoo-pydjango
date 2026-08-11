"""订单附件上传 — uploadChildData.ajax

本地落盘 +（有凭证时）同步上传 OSS。预览链接指向 imageWebServer/OSS，
若只写本地不传 OSS，浏览器打开会得到 NoSuchKey。
"""
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


def _max_upload_bytes() -> int:
    try:
        return int(getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024) or (50 * 1024 * 1024))
    except (TypeError, ValueError):
        return 50 * 1024 * 1024


def _object_key(path_store: str, filename: str) -> str:
    p = (path_store or "").strip().replace("\\", "/").strip("/")
    n = (filename or "").strip().lstrip("/")
    if p and n:
        return f"{p}/{n}"
    return p or n


def _try_oss_upload(key: str, data: bytes, content_type: str) -> tuple[bool, str]:
    """上传到阿里云 OSS；无凭证时返回 (False, 'skip')，失败返回 (False, 原因)。"""
    ak = getattr(settings, "OSS_ACCESS_KEY_ID", "") or ""
    sk = getattr(settings, "OSS_ACCESS_KEY_SECRET", "") or ""
    if not (ak and sk and key):
        return False, "skip"
    try:
        import oss2
    except ImportError:
        logger.warning("oss2 not installed; skip OSS upload key=%s", key)
        return False, "skip"
    try:
        endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").replace("https://", "").replace(
            "http://", ""
        )
        if not endpoint:
            return False, "OSS_ENDPOINT empty"
        auth = oss2.Auth(ak, sk)
        bucket = oss2.Bucket(auth, endpoint, getattr(settings, "OSS_BUCKET", "qgongye"))
        headers = {"Content-Type": (content_type or "application/octet-stream")}
        bucket.put_object(key, data, headers=headers)
        return True, "ok"
    except Exception as exc:
        logger.exception("OSS upload failed key=%s: %s", key, exc)
        return False, str(exc)


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
    max_bytes = _max_upload_bytes()
    if len(data) > max_bytes:
        mb = max(1, max_bytes // (1024 * 1024))
        return False, f"文件大小不能超过{mb}MB", {}

    file_ext = Path(orig_name or "upload").suffix.lower() or ".bin"
    filename = f"{uuid.uuid4().hex}{file_ext}"
    upload_root = Path(getattr(settings, "UPLOAD_DIR", None) or "upload")
    if not upload_root.is_absolute():
        base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
        upload_root = base / upload_root
    # 与历史 Java/库表约定一致：本地目录 UPLOAD_DIR/order；库内 path 常为 upload/order
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

    mime = (content_type or "").strip() or "application/octet-stream"
    ext_store = (mime[:64] if len(mime) <= 64 else file_ext.lstrip(".") or "bin")[:64]

    oss_key = _object_key(path_store, filename)
    oss_ok, oss_msg = _try_oss_upload(oss_key, data, mime)
    if not oss_ok and oss_msg != "skip":
        # 预览直链指向 OSS；上传失败则勿写库，避免 NoSuchKey 脏数据
        try:
            (target_dir / filename).unlink(missing_ok=True)
        except OSError:
            pass
        return False, f"文件上传到云存储失败: {oss_msg}", {}
    if oss_msg == "skip" and image_base and "aliyuncs.com" in image_base:
        logger.warning(
            "OSS credentials missing but imageWebServer is OSS; preview may 404. key=%s",
            oss_key,
        )

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
