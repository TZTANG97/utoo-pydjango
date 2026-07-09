#!/usr/bin/env python
"""检查 .env 中的 MySQL 是否可连、库是否存在（启动网关前建议执行）"""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
from django.conf import settings

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_libs = ROOT.parent / "qd_libs_common"
if _libs.is_dir():
    sys.path.insert(0, str(_libs))

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()


def main() -> int:
    db = settings.DATABASES["default"]
    host = db.get("HOST")
    port = int(db.get("PORT") or 3306)
    user = db.get("USER")
    password = db.get("PASSWORD")
    name = db.get("NAME")

    print(f"MySQL: {user}@{host}:{port}")
    print(f"DB_NAME: {name}")
    print()

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            connect_timeout=10,
        )
    except Exception as exc:
        print(f"[FAIL] 无法连接: {exc}")
        print("  检查网络/VPN、白名单、DB_HOST/账号密码")
        return 1

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            ver = cur.fetchone()[0]
            print(f"[OK] 已连接, MySQL {ver}")

            cur.execute("SHOW DATABASES")
            visible = {row[0] for row in cur.fetchall()}
            print(f"[INFO] 当前账号可见库: {sorted(visible)}")

            if name not in visible:
                print(f"[FAIL] 库 `{name}` 不存在或账号无权限 USE")
                print("  常见处理:")
                print("  1) 联系 DBA 为账号授权 qd_pt_new")
                print("  2) 使用有权限的账号，复制 .env.local.example -> .env.local 覆盖 DB_*")
                print("  3) 本地 MySQL 导入 UAT 库后 DB_HOST=127.0.0.1")
                return 1

            cur.execute(f"USE `{name}`")
            cur.execute("SHOW TABLES LIKE 'exp_user'")
            if not cur.fetchone():
                print(f"[WARN] `{name}` 中未找到 exp_user 表（本地库导入不完整）")
                print("  开发环境可执行: python scripts/bootstrap_exp_user_dev.py")
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM exp_user WHERE deleteStatus = 0"
                )
                cnt = cur.fetchone()[0]
                print(f"[OK] 库 `{name}` 可用，exp_user 有效用户约 {cnt} 条")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
