#!/usr/bin/env python
"""
本机重建空库 qd_pt_new + Django 系统表 + 最小 exp_user（仅够登录联调，不是全量业务数据）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import pymysql
from django.conf import settings


def main() -> int:
    db = settings.DATABASES["default"]
    name = db["NAME"]
    conn = pymysql.connect(
        host=db["HOST"],
        port=int(db["PORT"]),
        user=db["USER"],
        password=db["PASSWORD"],
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()
    print(f"[init] 已确保库 `{name}` 存在")

    subprocess.check_call(
        [sys.executable, str(ROOT / "manage.py"), "migrate", "--noinput"],
        cwd=ROOT,
    )
    print("[init] Django migrate 完成")

    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "bootstrap_exp_user_dev.py")],
        cwd=ROOT,
    )
    print("[init] 测试账号已写入 exp_user")
    print("[init] 登录: 18211984686 / 123456")
    print("[init] 注意: 订单/分类等业务表仍需从 RDS 备份或 DBA 导出后导入")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
