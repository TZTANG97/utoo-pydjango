"""订单附件上传 — uploadChildData.ajax

对齐 Java ExperimentOrderController.uploadChildData：
1) 本地临时落盘；2) 上传阿里云 OSS（PublicRead）；3) 写 accessory。
库内 path 存 imageWebServer + uploadFilePath/order（与 Java 一致），便于交叉预览。
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
        return int(getattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024) or (100 * 1024 * 1024))
    except (TypeError, ValueError):
        return 100 * 1024 * 1024


def _object_key(path_store: str, filename: str) -> str:
    """OSS object key：upload/order/uuid.ext（不含域名）。"""
    p = (path_store or "").strip().replace("\\", "/").strip("/")
    # 若误传入完整 URL，剥掉协议与域名
    if "://" in p:
        p = p.split("://", 1)[-1]
        if "/" in p:
            p = p.split("/", 1)[-1]
        else:
            p = ""
    n = (filename or "").strip().lstrip("/")
    if p and n:
        return f"{p}/{n}"
    return p or n


def _oss_configured() -> bool:
    ak = getattr(settings, "OSS_ACCESS_KEY_ID", "") or ""
    sk = getattr(settings, "OSS_ACCESS_KEY_SECRET", "") or ""
    endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").strip()
    return bool(ak and sk and endpoint)


def _try_oss_upload(key: str, data: bytes, content_type: str) -> tuple[bool, str]:
    """上传到阿里云 OSS（对齐 Java FileUploadUtil：PublicRead + Cache-Control）。"""
    if not _oss_configured():
        return False, "OSS 未配置（缺少 ACCESS_KEY / SECRET / ENDPOINT）"
    if not key:
        return False, "OSS key 为空"
    try:
        import oss2
    except ImportError:
        logger.warning("oss2 not installed; cannot upload key=%s", key)
        return False, "未安装 oss2 依赖"
    try:
        endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").replace("https://", "").replace(
            "http://", ""
        )
        ak = settings.OSS_ACCESS_KEY_ID
        sk = settings.OSS_ACCESS_KEY_SECRET
        bucket_name = getattr(settings, "OSS_BUCKET", "qgongye") or "qgongye"
        auth = oss2.Auth(ak, sk)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        headers = {
            "Content-Type": (content_type or "application/octet-stream"),
            # 对齐 Java setCache：缓存 30 天
            "Cache-Control": "max-age=2592000",
        }
        bucket.put_object(key, data, headers=headers)
        # 对齐 Java metadata.setObjectAcl(PublicRead)
        try:
            bucket.put_object_acl(key, oss2.OBJECT_ACL_PUBLIC_READ)
        except Exception as acl_exc:
            logger.warning("OSS set ACL failed key=%s: %s", key, acl_exc)
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
    subdir: str = "order",
    info: str | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    if not data:
        return False, "文件为空", {}
    max_bytes = _max_upload_bytes()
    if len(data) > max_bytes:
        mb = max(1, max_bytes // (1024 * 1024))
        return False, f"文件大小不能超过{mb}MB", {}

    file_ext = Path(orig_name or "upload").suffix.lower() or ".bin"
    # Java FileUploadUtil：UUID + 原扩展名
    filename = f"{uuid.uuid4().hex}{file_ext}"
    upload_root = Path(getattr(settings, "UPLOAD_DIR", None) or "upload")
    if not upload_root.is_absolute():
        base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
        upload_root = base / upload_root
    # 本地临时目录（与 Java 先落盘再推 OSS 一致）；收款/开票凭据用 bill
    folder = (subdir or "order").strip().strip("/\\") or "order"
    target_dir = upload_root / folder
    local_path = target_dir / filename
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
    except OSError as exc:
        logger.exception("save_order_attachment write failed: %s", exc)
        return False, "订单资料上传失败,请重试!", {}

    try:
        config = get_config_row()
    except Exception:
        logger.exception("get_config_row failed during upload")
        config = None
    image_base = image_web_server(config) if config is not None else ""
    if not image_base:
        image_base = (getattr(settings, "OSS_PUBLIC_BASE_URL", "") or getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")

    upload_file_path = "upload"
    if config and config.get("uploadFilePath"):
        upload_file_path = str(config["uploadFilePath"]).strip().strip("/\\") or "upload"
    # OSS key 前缀与 Java：config.getUploadFilePath()+"/order|bill"
    path_rel = f"{upload_file_path}/{folder}"
    # 库表 path 对齐 Java：imageWebServer + "/" + uploadFilePath + "/order|bill"
    path_store = f"{image_base.rstrip('/')}/{path_rel}" if image_base else path_rel

    mime = (content_type or "").strip() or "application/octet-stream"
    ext_store = (mime[:64] if len(mime) <= 64 else file_ext.lstrip(".") or "bin")[:64]
    info_store = (info if info is not None else (orig_name or "upload"))[:255]

    oss_key = _object_key(path_rel, filename)
    oss_ok, oss_msg = _try_oss_upload(oss_key, data, mime)
    if not oss_ok:
        try:
            local_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False, f"文件上传到云存储失败: {oss_msg}", {}

    now = datetime.now()
    try:
        acc_id = accessory_repo.insert_accessory(
            add_time=now,
            name=filename,
            path=path_store,
            ext=ext_store,
            info=info_store,
            acc_type=acc_type,
            exp_of_id=exp_of_id,
            child_of_id=child_of_id,
        )
        url = f"{path_store.rstrip('/')}/{filename}".replace("\\", "/")
        return True, "上传成功", {
            "id": acc_id,
            "name": filename,
            "path": path_store,
            "info": info_store,
            "ext": ext_store,
            "type": acc_type,
            "childOfId": child_of_id,
            "url": url,
        }
    except Exception as exc:
        logger.exception("save_order_attachment failed: %s", exc)
        return False, "订单资料上传失败,请重试!", {}
