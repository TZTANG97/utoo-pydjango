from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _candidate_key_paths() -> list[Path]:
    raw = (getattr(settings, "WEIXIN_PRIVATE_KEY_PATH", "") or "").strip()
    paths: list[Path] = []
    if raw:
        paths.append(Path(raw))
    paths.extend(
        [
            _PROJECT_ROOT / "certs" / "apiclient_key.pem",
            Path(r"F:\apiclient_key.pem"),
            Path("/data/cert/apiclient_key.pem"),
        ]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for p in paths:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def resolve_private_key_path() -> Path | None:
    for path in _candidate_key_paths():
        if path.is_file():
            return path
    return None


def wx_pay_configured() -> bool:
    return bool(
        settings.WEIXIN_APPID
        and settings.WEIXIN_MERCHANT_ID
        and settings.WEIXIN_MERCHANT_SERIAL_NUMBER
        and settings.WEIXIN_API_V3_KEY
        and resolve_private_key_path()
    )


def wx_pay_not_configured_message() -> str:
    tried = ", ".join(str(p) for p in _candidate_key_paths()[:3])
    return (
        "微信支付尚未配置：请在 .env 设置 WEIXIN_*，"
        f"并将 apiclient_key.pem 放到 {_PROJECT_ROOT / 'certs'}。已检查: {tried}"
    )


def notify_api_base() -> str:
    base = (getattr(settings, "CORS_HTTPS", "") or "").strip().rstrip("/")
    if not base:
        port = settings.SERVER_PORT_HTTP
        base = f"http://127.0.0.1:{port}"
    prefix = (getattr(settings, "API_PREFIX", "/api") or "/api").rstrip("/")
    if base.endswith(prefix):
        return base
    return f"{base}{prefix}"


def notify_url(path: str) -> str:
    p = path if path.startswith("/") else f"/{path}"
    return f"{notify_api_base()}{p}"


def load_private_key_pem() -> str:
    path = resolve_private_key_path()
    if not path:
        raise FileNotFoundError(wx_pay_not_configured_message())
    return path.read_text(encoding="utf-8").replace("\\n", "\n")
