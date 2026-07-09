from decimal import Decimal

from django.conf import settings

from apps.core.db_utils import fetch_one


def get_config_row() -> dict | None:
    return fetch_one("SELECT * FROM sysconfig WHERE id = 1 LIMIT 1")


def image_web_server(config: dict | None = None) -> str:
    if config and config.get("imageWebServer"):
        return str(config["imageWebServer"]).rstrip("/")
    return (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")


def integral_convert_ratio(config: dict | None = None) -> float:
    if config and config.get("integral_convert_ratio") is not None:
        return float(config["integral_convert_ratio"])
    return 2.0
