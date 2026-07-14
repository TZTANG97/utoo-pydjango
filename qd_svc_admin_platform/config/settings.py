from pathlib import Path
import sys

import pymysql

pymysql.install_as_MySQLdb()

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

_libs = BASE_DIR.parent / "qd_libs_common"
if _libs.is_dir() and str(_libs) not in sys.path:
    sys.path.insert(0, str(_libs))

env = environ.Env(APP_ENV=(str, "development"))
environ.Env.read_env(BASE_DIR / ".env")
_shared_db = BASE_DIR.parent / "config" / "shared-database.env"
if _shared_db.is_file():
    environ.Env.read_env(_shared_db)
_local = BASE_DIR / ".env.local"
if _local.is_file():
    environ.Env.read_env(_local, overwrite=True)

APP_ENV = env("APP_ENV")
DEBUG = APP_ENV == "development"
SECRET_KEY = env("DJANGO_SECRET_KEY", default=env("JWT_SECRET_KEY", default="change-me"))
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "apps.core",
    "apps.auth_support",
    "apps.auth_pc",
    "apps.admin_core",
    "apps.admin_system",
    "apps.admin_member",
    "apps.admin_ops",
    "apps.admin_service",
    "apps.admin_settings",
    "apps.payments",
    "apps.entry",
    "apps.invoices",
    "apps.pc_invoice",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

_db_legacy = env.bool("DB_LEGACY_MYSQL", default=True)
DATABASES = {
    "default": {
        "ENGINE": (
            "config.db_backends.legacy_mysql"
            if _db_legacy
            else "django.db.backends.mysql"
        ),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env.int("DB_PORT", default=3306),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "NAME": env("DB_NAME", default="qd_pt_new"),
        "OPTIONS": {"charset": "utf8mb4"},
        "TEST": {"CHARSET": "utf8mb4", "COLLATION": "utf8mb4_unicode_ci"},
    }
}

CORS_ALLOW_ALL_ORIGINS = True
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.auth_support.authentication.ExpJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
}

JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = env("JWT_SECRET_KEY", default=SECRET_KEY)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = env.int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=60 * 24)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = env.int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7)

SERVER_HOST = env("SERVER_HOST", default="0.0.0.0")
SERVER_PORT_HTTP = env.int("SERVER_PORT_HTTP", default=18091)
DEBUG_RELOAD = env.bool("DEBUG_RELOAD", default=True)

OSS_ENDPOINT = env("OSS_ENDPOINT", default="")
OSS_BUCKET = env("OSS_BUCKET", default="qgongye")
OSS_PUBLIC_BASE_URL = env("OSS_PUBLIC_BASE_URL", default="")
IMAGE_WEB_SERVER = env("IMAGE_WEB_SERVER", default="")

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
