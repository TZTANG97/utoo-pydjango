"""
MySQL 5.6/5.7 compatible backend for legacy qd_pt_new.

Django 5 officially requires MySQL >= 8.0.11; this wrapper skips that check.

DATETIME 约定（对齐 Java / docs/代码组织约定.md）：
库内存北京墙钟 naive；读写时按 Asia/Shanghai 解释，禁止把 UTC 墙钟写入业务表。
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.operations import DatabaseOperations as MySQLDatabaseOperations
from django.utils import timezone

logger = logging.getLogger(__name__)

BEIJING_TZ = ZoneInfo("Asia/Shanghai")


class DatabaseOperations(MySQLDatabaseOperations):
    def adapt_datetimefield_value(self, value):
        """aware → 北京墙钟 naive 再落库（勿写 UTC 墙钟）。"""
        if value is None:
            return None
        if hasattr(value, "resolve_expression"):
            return value
        if isinstance(value, datetime) and timezone.is_aware(value):
            return timezone.localtime(value, BEIJING_TZ).replace(tzinfo=None)
        return value

    def convert_datetimefield_value(self, value, expression, connection):
        """库内墙钟视为北京时间，读出为 Asia/Shanghai aware。"""
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return value.replace(tzinfo=BEIJING_TZ)
            return value.astimezone(BEIJING_TZ)
        return value


class DatabaseWrapper(MySQLDatabaseWrapper):
    ops_class = DatabaseOperations

    def check_database_version_supported(self):
        if self.mysql_version < (8, 0, 11):
            logger.warning(
                "Using legacy MySQL %s (Django 5 officially requires 8.0.11+). "
                "Ensure SQL is compatible with MySQL 5.6.",
                ".".join(str(x) for x in self.mysql_version),
            )
