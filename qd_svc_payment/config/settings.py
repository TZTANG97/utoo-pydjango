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
    environ.Env.read_env(_local)

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
    "apps.payments",
    "apps.pc_payment",
    "apps.wx",  # 原 qd_svc_wx：扫码登录 / 预约 / 反馈，已并入本进程
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
SERVER_PORT_HTTP = env.int("SERVER_PORT_HTTP", default=18084)
DEBUG_RELOAD = env.bool("DEBUG_RELOAD", default=True)

OSS_ENDPOINT = env("OSS_ENDPOINT", default="")
OSS_BUCKET = env("OSS_BUCKET", default="qgongye")
OSS_PUBLIC_BASE_URL = env("OSS_PUBLIC_BASE_URL", default="")
IMAGE_WEB_SERVER = env("IMAGE_WEB_SERVER", default="")

_redis_password = env("REDIS_PASSWORD", default="")
_redis_host = env("REDIS_HOST", default="127.0.0.1")
_redis_port = env.int("REDIS_PORT", default=6379)
_redis_db = env.int("REDIS_DATABASE", default=1)
_redis_auth = f":{_redis_password}@" if _redis_password else ""
REDIS_URL = f"redis://{_redis_auth}{_redis_host}:{_redis_port}/{_redis_db}"

API_PREFIX = env("API_PREFIX", default="/api")
CORS_HTTPS = env("CORS_HTTPS", default="")

PAY_USER_LOCK_SECONDS = env.int("PAY_USER_LOCK_SECONDS", default=30)
PAY_NOTIFY_LOCK_SECONDS = env.int("PAY_NOTIFY_LOCK_SECONDS", default=120)

WEIXIN_APPID = env("WEIXIN_APPID", default="")
WEIXIN_SECRET = env("WEIXIN_SECRET", default="")
WEIXIN_GZH_APPID = env("WEIXIN_GZH_APPID", default="")
WEIXIN_GZH_SECRET = env("WEIXIN_GZH_SECRET", default="")
WEIXIN_GZH_TOKEN = env("WEIXIN_GZH_TOKEN", default="")
WEIXIN_GZH_MINI_THUMB_MEDIA_ID = env("WEIXIN_GZH_MINI_THUMB_MEDIA_ID", default="")
WEIXIN_MP_APPID = env("WEIXIN_MP_APPID", default="")
WEIXIN_MP_SECRET = env("WEIXIN_MP_SECRET", default="")
WEIXIN_MP_AUTH_PAGEPATH = env(
    "WEIXIN_MP_AUTH_PAGEPATH", default="staffB/auth_phone/auth_phone"
)
WEIXIN_MERCHANT_ID = env("WEIXIN_MERCHANT_ID", default="")
WEIXIN_MERCHANT_SERIAL_NUMBER = env("WEIXIN_MERCHANT_SERIAL_NUMBER", default="")
WEIXIN_API_V3_KEY = env("WEIXIN_API_V3_KEY", default="")
WEIXIN_PRIVATE_KEY_PATH = env("WEIXIN_PRIVATE_KEY_PATH", default="")

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
