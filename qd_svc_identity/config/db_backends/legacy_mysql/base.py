"""MySQL 5.6/5.7 compatible backend for legacy qd_pt_new."""
import logging

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper

logger = logging.getLogger(__name__)


class DatabaseWrapper(MySQLDatabaseWrapper):
    def check_database_version_supported(self):
        if self.mysql_version < (8, 0, 11):
            logger.warning(
                "Using legacy MySQL %s (Django 5 officially requires 8.0.11+).",
                ".".join(str(x) for x in self.mysql_version),
            )
