"""
青岛检测平台 — Django 配置（从 .env 读取，对齐 qd_test_server_py）
"""
from datetime import timedelta
from pathlib import Path
import sys

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

_libs = BASE_DIR.parent / "qd_libs_common"
if _libs.is_dir() and str(_libs) not in sys.path:
    sys.path.insert(0, str(_libs))

env = environ.Env(
    APP_ENV=(str, "development"),
    DEBUG_RELOAD=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")
_shared_db = BASE_DIR.parent / "config" / "shared-database.env"
if _shared_db.is_file():
    environ.Env.read_env(_shared_db)
# 本地覆盖（不提交 git）：解决 UAT 账号无库权限、本机库名不同等
_local_env = BASE_DIR / ".env.local"
if _local_env.is_file():
    environ.Env.read_env(_local_env, overwrite=True)

APP_ENV = env("APP_ENV")
DEBUG = APP_ENV == "development"

SECRET_KEY = env("DJANGO_SECRET_KEY", default=env("JWT_SECRET_KEY", default="change-me-in-production"))
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "apps.core",
    "apps.auth_pc",
    "apps.pc_compat",
    "apps.orders",
    "apps.payments",
    "apps.invoices",
    "apps.entry",
    "apps.wx",
    "apps.admin_core",
    "apps.admin_auth",
    "apps.admin_settings",
    "apps.admin_system",
    "apps.admin_service",
    "apps.admin_ops",
    "apps.admin_digital",
    "apps.admin_inventory",
    "apps.admin_experiment",
    "apps.admin_fund",
    "apps.admin_member",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.NormalizeAcceptHeaderMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Java UAT 多为 MySQL 5.6；Django 5 官方要求 8.0.11+，用 legacy 后端跳过版本校验
_DB_LEGACY = env.bool("DB_LEGACY_MYSQL", default=True)
_DB_ENGINE = env(
    "DB_ENGINE",
    default=(
        "config.db_backends.legacy_mysql"
        if _DB_LEGACY
        else "django.db.backends.mysql"
    ),
)

_db_name = env("DB_NAME", default="qd_pt_new")
DATABASES = {
    "default": {
        "ENGINE": _DB_ENGINE,
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env.int("DB_PORT", default=3306),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "NAME": _db_name,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        # 切勿把 TEST.NAME 设为业务库 qd_pt_new！
        # pytest --django-db 在非交互模式下会对已存在的测试库执行 DROP DATABASE（autoclobber）。
        # 默认使用 test_qd_pt_new；联调接口测试见 tests/conftest.py（live_client，不走建库流程）。
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

_redis_password = env("REDIS_PASSWORD", default="")
_redis_host = env("REDIS_HOST", default="127.0.0.1")
_redis_port = env.int("REDIS_PORT", default=6379)
_redis_db = env.int("REDIS_DATABASE", default=1)
_redis_auth = f":{_redis_password}@" if _redis_password else ""
REDIS_URL = f"redis://{_redis_auth}{_redis_host}:{_redis_port}/{_redis_db}"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": env.int("REDIS_TIMEOUT", default=10000) / 1000,
        },
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_ENABLE_UTC = True

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.auth_pc.authentication.ExpJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

JWT_ALGORITHM = "HS256"

SIMPLE_JWT = {
    "SIGNING_KEY": env("JWT_SECRET_KEY", default=SECRET_KEY),
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=60 * 24)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7)
    ),
}

# —— 业务配置（D1+ 使用）——
SERVER_HOST = env("SERVER_HOST", default="0.0.0.0")
SERVER_PORT_HTTP = env.int("SERVER_PORT_HTTP", default=18083)
API_PREFIX = env("API_PREFIX", default="/api")
DEBUG_RELOAD = env.bool("DEBUG_RELOAD", default=True)

JWT_SECRET_KEY = env("JWT_SECRET_KEY", default=SECRET_KEY)
DEV_SMS_CODE = env("DEV_SMS_CODE", default="111111")

PAY_DEBUG_ENABLED = env.bool("PAY_DEBUG_ENABLED", default=False)
PAY_NOTIFY_USE_QUEUE = env.bool("PAY_NOTIFY_USE_QUEUE", default=True)
PAY_USER_LOCK_SECONDS = env.int("PAY_USER_LOCK_SECONDS", default=30)
PAY_NOTIFY_LOCK_SECONDS = env.int("PAY_NOTIFY_LOCK_SECONDS", default=120)

OSS_ENDPOINT = env("OSS_ENDPOINT", default="")
OSS_BUCKET = env("OSS_BUCKET", default="")
OSS_ACCESS_KEY_ID = env("OSS_ACCESS_KEY_ID", default="")
OSS_ACCESS_KEY_SECRET = env("OSS_ACCESS_KEY_SECRET", default="")
OSS_PUBLIC_BASE_URL = env("OSS_PUBLIC_BASE_URL", default="")
IMAGE_WEB_SERVER = env("IMAGE_WEB_SERVER", default="")
UPLOAD_DIR = env("UPLOAD_DIR", default="upload")
MAX_UPLOAD_SIZE = env.int("MAX_UPLOAD_SIZE", default=10 * 1024 * 1024)

WEIXIN_APPID = env("WEIXIN_APPID", default="")
WEIXIN_SECRET = env("WEIXIN_SECRET", default="")
WEIXIN_GZH_APPID = env("WEIXIN_GZH_APPID", default="")
WEIXIN_GZH_SECRET = env("WEIXIN_GZH_SECRET", default="")
WEIXIN_GZH_TOKEN = env("WEIXIN_GZH_TOKEN", default="")
WEIXIN_MERCHANT_ID = env("WEIXIN_MERCHANT_ID", default="")
WEIXIN_MERCHANT_SERIAL_NUMBER = env("WEIXIN_MERCHANT_SERIAL_NUMBER", default="")
WEIXIN_API_V3_KEY = env("WEIXIN_API_V3_KEY", default="")
WEIXIN_PRIVATE_KEY_PATH = env("WEIXIN_PRIVATE_KEY_PATH", default="")
CORS_HTTPS = env("CORS_HTTPS", default="")

SMS_ACCESS_KEY_ID = env("SMS_ACCESS_KEY_ID", default="")
SMS_ACCESS_KEY_SECRET = env("SMS_ACCESS_KEY_SECRET", default="")

# 微服务上游（MS-1+）；设 SVC_AUTH_URL 后网关转发认证域到 qd_svc_auth :18081
SVC_AUTH_URL = env("SVC_AUTH_URL", default="")
SVC_ORDER_URL = env("SVC_ORDER_URL", default="")
SVC_PAYMENT_URL = env("SVC_PAYMENT_URL", default="")
SVC_INVOICE_URL = env("SVC_INVOICE_URL", default="")
SVC_ENTRY_URL = env("SVC_ENTRY_URL", default="")
SVC_WX_URL = env("SVC_WX_URL", default="")
SVC_ADMIN_ASSET_URL = env("SVC_ADMIN_ASSET_URL", default="")
SVC_ADMIN_PLATFORM_URL = env("SVC_ADMIN_PLATFORM_URL", default="")
