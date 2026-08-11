"""附件下载 — 对齐 Java experimentOrder/downloadFile.ajax。"""
from __future__ import annotations

import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from django.conf import settings

from apps.core.db_utils import fetch_one
from apps.core.services.sysconfig import get_config_row, image_web_server

logger = logging.getLogger(__name__)


def fetch_accessory_row(accessory_id: int) -> Optional[dict]:
    return fetch_one(
        """
        SELECT id, name, path, info, ext
        FROM accessory
        WHERE id = %(aid)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"aid": accessory_id},
    )


def build_download_filename(acc: dict, name_hint: str = "") -> str:
    file_name = (acc.get("name") or "download").strip()
    hint = (name_hint or "").strip()
    info = (acc.get("info") or file_name).strip()
    base = hint or info
    dot = base.rfind(".")
    if dot != -1:
        base = base[:dot]
    ext_dot = file_name.rfind(".")
    ext = file_name[ext_dot:] if ext_dot != -1 else ""
    if not ext and info.rfind(".") != -1:
        ext = info[info.rfind(".") :]
    return f"{base}{ext}" if base else file_name


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


def _public_url(acc: dict) -> str:
    path = str(acc.get("path") or "").strip().rstrip("/")
    name = str(acc.get("name") or "").strip().lstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return f"{path}/{name}" if name and not path.endswith(name) else path
    try:
        config = get_config_row()
        base = (image_web_server(config) or "").rstrip("/")
    except Exception:
        base = (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")
    if base and path and name:
        return f"{base}/{path}/{name}"
    if base and name:
        return f"{base}/{name}"
    return ""


def _try_oss_download(key: str) -> Optional[bytes]:
    ak = getattr(settings, "OSS_ACCESS_KEY_ID", "") or ""
    sk = getattr(settings, "OSS_ACCESS_KEY_SECRET", "") or ""
    if not (ak and sk and key):
        return None
    try:
        import oss2

        endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").replace("https://", "").replace(
            "http://", ""
        )
        if not endpoint:
            return None
        auth = oss2.Auth(ak, sk)
        bucket = oss2.Bucket(auth, endpoint, getattr(settings, "OSS_BUCKET", "qgongye"))
        return bucket.get_object(key).read()
    except Exception as exc:
        logger.warning("OSS download failed key=%s: %s", key, exc)
        return None


def _try_http_download(url: str) -> Optional[bytes]:
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "utoo-order-download/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        logger.warning("HTTP download failed url=%s: %s", url, exc)
        return None


def _local_file_candidates(upload_root: Path, path: str, name: str) -> list[Path]:
    """兼容 path=upload/order + UPLOAD_DIR=.../upload 与 path=order 等历史写法。"""
    filename = (name or "").strip().lstrip("/")
    path_norm = (path or "").strip().replace("\\", "/").strip("/")
    key = f"{path_norm}/{filename}" if path_norm and filename else (path_norm or filename)
    out: list[Path] = []
    if filename:
        out.append(upload_root / "order" / filename)
        out.append(upload_root / filename)
    if key:
        out.append(upload_root / Path(*key.split("/")))
        parts = key.split("/")
        if len(parts) >= 2 and parts[0] == "upload":
            out.append(upload_root / Path(*parts[1:]))
        if upload_root.name == "upload" and parts and parts[0] == "upload":
            out.append(upload_root.parent / Path(*parts))
    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        uniq.append(p)
    return uniq


def load_accessory_bytes(
    accessory_id: int, *, name_hint: str = ""
) -> tuple[Optional[bytes], str]:
    acc = fetch_accessory_row(accessory_id)
    if not acc:
        return None, ""
    download_name = build_download_filename(acc, name_hint)
    key = _object_key(acc.get("path") or "", acc.get("name") or "")

    data = _try_oss_download(key) if key else None
    if data:
        return data, download_name

    upload_root = Path(getattr(settings, "UPLOAD_DIR", None) or "upload")
    if not upload_root.is_absolute():
        upload_root = Path(getattr(settings, "BASE_DIR", Path.cwd())) / upload_root
    for local_path in _local_file_candidates(
        upload_root, str(acc.get("path") or ""), str(acc.get("name") or "")
    ):
        if local_path.is_file():
            return local_path.read_bytes(), download_name

    data = _try_http_download(_public_url(acc))
    if data:
        return data, download_name

    logger.warning("attachment not found id=%s key=%s", accessory_id, key)
    return None, download_name


def content_disposition(filename: str) -> str:
    """RFC 5987，兼容中文文件名。"""
    safe = filename.replace('"', "").replace("\r", "").replace("\n", "") or "download"
    encoded = quote(safe)
    return f"attachment; filename=\"{safe}\"; filename*=UTF-8''{encoded}"
