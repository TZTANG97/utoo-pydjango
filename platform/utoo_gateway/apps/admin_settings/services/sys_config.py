"""系统设置编排：上传/站点/短信/邮件（SQL 在 repositories）。"""

from __future__ import annotations

import logging
import smtplib
import uuid
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.admin_settings.repositories import sys_config as repo
from apps.core.services.sysconfig import get_config_row, image_web_server

logger = logging.getLogger(__name__)


def get_upload_setting() -> dict[str, Any]:
    return repo.get_upload_setting()


def save_upload_setting(data: dict[str, Any]) -> None:
    repo.save_upload_setting(
        image_save_type=str(data.get("imageSaveType") or "").strip(),
        image_web_server=str(data.get("imageWebServer") or "").strip(),
    )


def get_site_setting() -> dict[str, Any]:
    return repo.get_site_setting()


def save_site_setting(data: dict[str, Any]) -> None:
    logo_id = data.get("websiteLogo_id")
    logo_id_int: int | None = None
    if logo_id not in (None, ""):
        try:
            logo_id_int = int(logo_id)
        except (TypeError, ValueError):
            logo_id_int = None
    repo.save_site_setting(
        website_name=str(data.get("websiteName") or "").strip(),
        title=str(data.get("title") or "").strip(),
        hot_search=str(data.get("hotSearch") or "").strip(),
        service_telphone_list=str(data.get("service_telphone_list") or ""),
        website_logo_id=logo_id_int,
    )


def _oss_configured() -> bool:
    ak = getattr(settings, "OSS_ACCESS_KEY_ID", "") or ""
    sk = getattr(settings, "OSS_ACCESS_KEY_SECRET", "") or ""
    endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").strip()
    return bool(ak and sk and endpoint)


def _try_oss_upload(key: str, data: bytes, content_type: str) -> tuple[bool, str]:
    if not _oss_configured():
        return False, "OSS 未配置"
    try:
        import oss2
    except ImportError:
        return False, "未安装 oss2"
    try:
        endpoint = (getattr(settings, "OSS_ENDPOINT", "") or "").replace("https://", "").replace(
            "http://", ""
        )
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, endpoint, getattr(settings, "OSS_BUCKET", "qgongye") or "qgongye")
        headers = {
            "Content-Type": content_type or "application/octet-stream",
            "Cache-Control": "max-age=2592000",
        }
        bucket.put_object(key, data, headers=headers)
        try:
            bucket.put_object_acl(key, oss2.OBJECT_ACL_PUBLIC_READ)
        except Exception:
            pass
        return True, "ok"
    except Exception as exc:
        logger.exception("logo OSS upload failed: %s", exc)
        return False, str(exc)


def upload_website_logo(*, data: bytes, orig_name: str, content_type: str) -> tuple[bool, str, dict]:
    """对齐 Java sys_config_save 中 websiteLogo 上传：upload/system + accessory。"""
    if not data:
        return False, "文件为空", {}
    file_ext = Path(orig_name or "logo.png").suffix.lower() or ".png"
    filename = f"{uuid.uuid4().hex}{file_ext}"
    try:
        config = get_config_row()
    except Exception:
        config = None
    upload_file_path = "upload"
    if config and config.get("uploadFilePath"):
        upload_file_path = str(config["uploadFilePath"]).strip().strip("/\\") or "upload"
    path_rel = f"{upload_file_path}/system"
    image_base = image_web_server(config) if config else ""
    if not image_base:
        image_base = (
            getattr(settings, "OSS_PUBLIC_BASE_URL", "")
            or getattr(settings, "IMAGE_WEB_SERVER", "")
            or ""
        ).rstrip("/")
    # Java accessory.path = uploadFilePath + "/system"（相对）；展示时拼 imageWebServer
    path_store = path_rel

    oss_ok, oss_msg = _try_oss_upload(f"{path_rel}/{filename}", data, content_type)
    if not oss_ok:
        # 无 OSS 时允许仅改库路径（文件需已在 CDN）；这里失败则明确报错
        return False, f"Logo 上传失败: {oss_msg}", {}

    logo_id = repo.update_or_create_website_logo(
        path=path_store,
        name=filename,
        ext=file_ext.lstrip(".")[:32],
        size=float(len(data)),
    )
    site = repo.get_site_setting()
    return True, "上传成功", {"websiteLogo_id": logo_id, "websiteLogoUrl": site.get("websiteLogoUrl")}


def bind_website_logo_by_path(*, path: str, name: str) -> tuple[bool, str]:
    path = (path or "").strip()
    name = (name or "").strip()
    if not path or not name:
        return False, "请填写 Logo 路径与文件名"
    repo.update_or_create_website_logo(path=path, name=name)
    return True, "已更新 Logo"


def get_sms_setting() -> dict[str, Any]:
    return repo.get_sms_setting()


def _truthy(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return bool(int(val))
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def save_sms_setting(data: dict[str, Any]) -> None:
    repo.save_sms_setting(sms_enable=_truthy(data.get("smsEnbale")))


def get_email_setting() -> dict[str, Any]:
    return repo.get_email_setting()


def save_email_setting(data: dict[str, Any]) -> None:
    repo.save_email_setting(
        email_enable=_truthy(data.get("emailEnable")),
        email_host=str(data.get("emailHost") or "").strip(),
        email_port=str(data.get("emailPort") or "").strip(),
        email_user_name=str(data.get("emailUserName") or "").strip(),
        email_user=str(data.get("emailUser") or "").strip(),
        email_pws=str(data.get("emailPws") or ""),
    )


def test_mail(email: str) -> tuple[bool, str]:
    """对齐 Java /edit/test_mail.htm：用当前邮件配置发测试信。"""
    to_addr = (email or "").strip()
    if not to_addr:
        return False, "请填写测试邮箱"
    cfg = repo.get_email_setting()
    if not cfg.get("emailEnable"):
        return False, "邮件功能已关闭"
    host = (cfg.get("emailHost") or "").strip()
    if not host:
        return False, "请先配置 SMTP 服务器"
    try:
        port = int(str(cfg.get("emailPort") or "25").strip() or "25")
    except ValueError:
        return False, "SMTP 端口无效"
    user = (cfg.get("emailUser") or "").strip()
    password = str(cfg.get("emailPws") or "")
    from_name = (cfg.get("emailUserName") or "").strip() or user
    msg = MIMEText("销售订单创建成功!", "plain", "utf-8")
    msg["Subject"] = "新销售订单"
    msg["From"] = from_name if "@" in from_name else (f"{from_name} <{user}>" if user else from_name)
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            try:
                smtp.starttls()
            except smtplib.SMTPException:
                pass
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(user or from_name, [to_addr], msg.as_string())
        return True, "邮件测试成功"
    except Exception as exc:
        logger.warning("test_mail failed: %s", exc)
        return False, f"邮件测试失败：{exc}"
