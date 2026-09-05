"""Shared Django database helpers for legacy MySQL 5.6 (qd_pt_new)."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_db_engine() -> str:
    """Map any MySQL engine to the shared 5.6/5.7-compatible backend."""
    engine = os.getenv("DB_ENGINE", "django.db.backends.sqlite3").strip()
    if "legacy_mysql" in engine:
        return engine
    if "sqlite" in engine.lower():
        return engine
    if "mysql" in engine.lower():
        return "shared.db_backends.legacy_mysql"
    # Host set but engine left as default mysql string variants
    if os.getenv("DB_HOST") and os.getenv("DB_LEGACY_MYSQL", "true").lower() in {"1", "true", "yes"}:
        return "shared.db_backends.legacy_mysql"
    return engine


def database_settings(sqlite_path: str | Path) -> dict:
    engine = resolve_db_engine()
    cfg = {
        "ENGINE": engine,
        "NAME": os.getenv("DB_NAME", str(sqlite_path)),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
    }
    if "mysql" in engine.lower() or engine.endswith("legacy_mysql"):
        # 会话时区 +08:00，与现网 Java / 业务 DATETIME 北京墙钟一致
        cfg["OPTIONS"] = {
            "charset": "utf8mb4",
            "init_command": "SET time_zone = '+08:00'",
        }
    return cfg
