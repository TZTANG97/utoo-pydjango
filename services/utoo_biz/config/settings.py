import os
import sys
from pathlib import Path

import pymysql

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load slot shared-database.env (+ optional local .env) before database_settings().
_slot_root = BASE_DIR.parents[1]  # .../services/utoo_biz -> slot root
_shared_db = _slot_root / "config" / "shared-database.env"
_env_file = BASE_DIR / ".env"
_local_env = BASE_DIR / ".env.local"


def _load_env_file(path: Path, *, override: bool = False) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        if (not override) and key in os.environ and os.environ.get(key, "") != "":
            continue
        os.environ[key] = val.strip().strip('"').strip("'")


_load_env_file(_shared_db, override=False)
_load_env_file(_env_file, override=True)
_load_env_file(_local_env, override=True)

from shared.django_db import database_settings

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "development-only-change-me")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true" and APP_ENV == "development"
ALLOWED_HOSTS = ["*"]

JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
JWT_ISSUER = os.getenv("JWT_ISSUER", "qd-mall-identity")
MALL_JWT_SECRET = os.getenv("MALL_JWT_SECRET", JWT_SECRET)
MALL_JWT_ISSUER = os.getenv("MALL_JWT_ISSUER", JWT_ISSUER)
UTOO_JWT_SECRET_KEY = os.getenv("UTOO_JWT_SECRET_KEY", JWT_SECRET)
UTOO_JWT_TTL_SECONDS = int(os.getenv("UTOO_JWT_TTL_SECONDS", "1800"))
# 与 asset 对齐：缺显式 URL 时代理 503，禁止默认 localhost 假连 / silent twin
UTOO_ORDER_MID_SERVICE_URL = os.getenv(
    "UTOO_ORDER_MID_SERVICE_URL",
    os.getenv("UTOO_ORDER_SERVICE_URL", os.getenv("SVC_ORDER_URL", "")),
).rstrip("/")
UTOO_PAYMENT_MID_SERVICE_URL = os.getenv(
    "UTOO_PAYMENT_MID_SERVICE_URL", os.getenv("SVC_PAYMENT_URL", "")
).rstrip("/")
UTOO_PLATFORM_MID_SERVICE_URL = os.getenv(
    "UTOO_PLATFORM_MID_SERVICE_URL", os.getenv("SVC_ADMIN_PLATFORM_URL", "")
).rstrip("/")
UTOO_IDENTITY_MID_SERVICE_URL = os.getenv(
    "UTOO_IDENTITY_MID_SERVICE_URL",
    os.getenv("IDENTITY_MID_SERVICE_URL", os.getenv("SVC_IDENTITY_URL", "")),
).rstrip("/")
UTOO_GATEWAY_INTERNAL_URL = os.getenv("UTOO_GATEWAY_INTERNAL_URL", "http://127.0.0.1:18083").rstrip("/")
UTOO_ASSET_MID_SERVICE_URL = os.getenv(
    "UTOO_ASSET_MID_SERVICE_URL",
    os.getenv("SVC_ADMIN_ASSET_URL", ""),
).rstrip("/")
UTOO_ORDER_PROXY_TIMEOUT_SECONDS = float(os.getenv("UTOO_ORDER_PROXY_TIMEOUT_SECONDS", "15"))
UTOO_MID_PROXY_TIMEOUT_SECONDS = float(os.getenv("UTOO_MID_PROXY_TIMEOUT_SECONDS", "15"))

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "apps.utoo_experiment",
    "apps.utoo_consumer",
    "apps.utoo_admin.apps.UtooAdminConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": database_settings(BASE_DIR / "utoo_biz.sqlite3"),
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "UNAUTHENTICATED_USER": None,
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TIME_ZONE = "Asia/Shanghai"
USE_TZ = True
