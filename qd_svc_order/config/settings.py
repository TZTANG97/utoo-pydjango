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
    "apps.orders",
    "apps.payments",
    "apps.pc_order",
    "apps.admin_experiment",
    "apps.iot",
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
SERVER_PORT_HTTP = env.int("SERVER_PORT_HTTP", default=18082)
DEBUG_RELOAD = env.bool("DEBUG_RELOAD", default=True)

OSS_ENDPOINT = env("OSS_ENDPOINT", default="")
OSS_BUCKET = env("OSS_BUCKET", default="qgongye")
OSS_PUBLIC_BASE_URL = env("OSS_PUBLIC_BASE_URL", default="")
OSS_ACCESS_KEY_ID = env("OSS_ACCESS_KEY_ID", default="")
OSS_ACCESS_KEY_SECRET = env("OSS_ACCESS_KEY_SECRET", default="")
IMAGE_WEB_SERVER = env("IMAGE_WEB_SERVER", default="")
# 订单资料等本地落盘目录（相对路径相对本服务 BASE_DIR）
UPLOAD_DIR = env("UPLOAD_DIR", default="upload")
# 默认/下限 50MB：发票 PDF、高清图常超旧值 10MB；过低会 HTTP 413
_DEFAULT_MAX_UPLOAD = 50 * 1024 * 1024
MAX_UPLOAD_SIZE = max(env.int("MAX_UPLOAD_SIZE", default=_DEFAULT_MAX_UPLOAD), _DEFAULT_MAX_UPLOAD)
# Django 默认仅约 2.5MB，超限会直接 HTTP 413，需与业务上传上限对齐
DATA_UPLOAD_MAX_MEMORY_SIZE = max(
    env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=MAX_UPLOAD_SIZE), MAX_UPLOAD_SIZE
)
FILE_UPLOAD_MAX_MEMORY_SIZE = max(
    env.int("FILE_UPLOAD_MAX_MEMORY_SIZE", default=MAX_UPLOAD_SIZE), MAX_UPLOAD_SIZE
)

# 公众号模板消息（对齐 Java gzh.appid / gzh.secret / gzh.send）
WEIXIN_APPID = env("WEIXIN_APPID", default="")
WEIXIN_SECRET = env("WEIXIN_SECRET", default="")
WEIXIN_MP_APPID = env("WEIXIN_MP_APPID", default="")
WEIXIN_GZH_APPID = env("WEIXIN_GZH_APPID", default="")
WEIXIN_GZH_SECRET = env("WEIXIN_GZH_SECRET", default="")
WEIXIN_GZH_SEND = env("WEIXIN_GZH_SEND", default="1")

# UTOO × IOT（正式 .env + 本机 .env.local 叠加；见 docs/UTOO-IOT本机交叉配置.md）
IOT_BASE_URL = env("IOT_BASE_URL", default="")
IOT_WEB_URL = env("IOT_WEB_URL", default="")  # 运维前端，如 http://127.0.0.1:5173
IOT_SERVICE_TOKEN = env("IOT_SERVICE_TOKEN", default="")
IOT_HMAC_SECRET = env("IOT_HMAC_SECRET", default="")
IOT_APP_ID = env("IOT_APP_ID", default="utoo-iot")
IOT_CALLBACK_IP_WHITELIST = env("IOT_CALLBACK_IP_WHITELIST", default="")
IOT_HTTP_TIMEOUT = env.int("IOT_HTTP_TIMEOUT", default=15)
IOT_UTOO_CALLBACK_URL = env("IOT_UTOO_CALLBACK_URL", default="")

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
