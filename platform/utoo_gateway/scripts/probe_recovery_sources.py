#!/usr/bin/env python
"""探测可从哪拉取 qd_pt_new 数据（不写库）。"""
from __future__ import annotations

import pymysql

SOURCES = [
    ("local-root", "127.0.0.1", "root", "970806tt"),
    ("uat-dpt_uat", "rm-m5e5abeh1ypno7j5mo.mysql.rds.aliyuncs.com", "dpt_uat", "tux8fFWUtgsWKS3rSZ!"),
    ("uat-qdroot", "rm-m5e5abeh1ypno7j5mo.mysql.rds.aliyuncs.com", "qdroot", "tux8fFWUtgsWKS3rTz"),
    ("alt120-root", "8.140.119.120", "root", "dfa21a!kdjA23@#"),
]


def probe(label: str, host: str, user: str, password: str) -> None:
    try:
        conn = pymysql.connect(
            host=host, port=3306, user=user, password=password, connect_timeout=10
        )
    except Exception as exc:
        print(f"[{label}] 连接失败: {exc}")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            ver = cur.fetchone()[0]
            cur.execute("SHOW DATABASES")
            dbs = [r[0] for r in cur.fetchall()]
            has = "qd_pt_new" in dbs
            tables = 0
            if has:
                cur.execute("USE `qd_pt_new`")
                cur.execute("SHOW TABLES")
                tables = len(cur.fetchall())
            print(
                f"[{label}] OK MySQL {ver} | 可见库 {len(dbs)} 个 | "
                f"qd_pt_new={'有' if has else '无'} | 表数={tables}"
            )
            if not has and len(dbs) <= 12:
                print(f"         库列表: {dbs}")
    finally:
        conn.close()


def main() -> int:
    print("=== 数据源探测（只读）===\n")
    for item in SOURCES:
        probe(*item)
        print()
    print("若 UAT 有 qd_pt_new 但本账号无权限，需阿里云 RDS 控制台恢复备份或找 DBA 授权/导出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
