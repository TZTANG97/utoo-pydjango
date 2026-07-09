from typing import Any

from django.db import connection

from qd_common.serialize import row_to_dict, to_jsonable


def fetch_all(sql: str, params: dict | list | None = None) -> list[dict[str, Any]]:
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        if not cur.description:
            return []
        cols = [c[0] for c in cur.description]
        return [row_to_dict(dict(zip(cols, row))) for row in cur.fetchall()]


def fetch_one(sql: str, params: dict | list | None = None) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def scalar(sql: str, params: dict | list | None = None, default=0):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        row = cur.fetchone()
        if not row:
            return default
        return to_jsonable(row[0])


def execute(sql: str, params: dict | list | None = None) -> int:
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.rowcount


def execute_insert(sql: str, params: dict | list | None = None) -> int:
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        return int(cur.lastrowid or 0)
