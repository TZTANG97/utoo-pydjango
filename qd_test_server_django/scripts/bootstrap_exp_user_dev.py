#!/usr/bin/env python
"""
本地 qd_pt_new 缺少 exp_user 时：建最小表 + 测试账号（默认 18211984686 / 123456）
不用于生产。完整数据请从 UAT 导入 exp_user 表。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_libs = ROOT.parent / "qd_libs_common"
if _libs.is_dir():
    sys.path.insert(0, str(_libs))

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.db import connection
from qd_common.password_java import encrypt_password_for_storage

DDL = """
CREATE TABLE IF NOT EXISTS `exp_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `addTime` datetime DEFAULT NULL,
  `deleteStatus` bit(1) NOT NULL DEFAULT b'0',
  `mobile` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `trueName` varchar(255) DEFAULT NULL,
  `userName` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `idcard` varchar(255) DEFAULT NULL,
  `userType` tinyint DEFAULT 1,
  `is_identify` int DEFAULT 0,
  `photo_id` bigint DEFAULT NULL,
  `parent_id` bigint DEFAULT NULL,
  `company_name` varchar(200) DEFAULT NULL,
  `area_id` bigint DEFAULT NULL,
  `address_info` varchar(255) DEFAULT NULL,
  `wx_nickname` varchar(255) DEFAULT NULL,
  `identity` int DEFAULT NULL,
  `is_accept_message` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_exp_user_mobile` (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

TEST_MOBILE = os.getenv("TEST_LOGIN_MOBILE", "18211984686")
TEST_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "123456")
TEST_USER_ID = int(os.getenv("TEST_LOGIN_USER_ID", "8752"))


def main() -> int:
    pwd_hash = encrypt_password_for_storage(TEST_PASSWORD)
    with connection.cursor() as cur:
        cur.execute("SHOW TABLES LIKE 'exp_user'")
        exists = cur.fetchone() is not None
        if not exists:
            print("[bootstrap] creating exp_user ...")
            cur.execute(DDL)
        else:
            print("[bootstrap] exp_user already exists")

        cur.execute(
            "SELECT id FROM exp_user WHERE mobile = %s AND deleteStatus = 0 LIMIT 1",
            [TEST_MOBILE],
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE exp_user SET password = %s WHERE id = %s",
                [pwd_hash, row[0]],
            )
            print(f"[bootstrap] updated password for id={row[0]} mobile={TEST_MOBILE}")
        else:
            cur.execute(
                """
                INSERT INTO exp_user
                (id, deleteStatus, mobile, password, userName, trueName, userType, is_identify)
                VALUES (%s, b'0', %s, %s, %s, %s, 1, 0)
                """,
                [TEST_USER_ID, TEST_MOBILE, pwd_hash, TEST_MOBILE, "测试用户"],
            )
            print(f"[bootstrap] inserted test user id={TEST_USER_ID} mobile={TEST_MOBILE}")

    print(f"[bootstrap] login: {TEST_MOBILE} / {TEST_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
