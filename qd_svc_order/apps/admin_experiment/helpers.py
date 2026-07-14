from __future__ import annotations

from typing import Any

from rest_framework.request import Request


def merge_payload(request: Request) -> dict[str, Any]:
    q = {k: request.query_params.get(k) for k in request.query_params.keys()}
    body = request.data if isinstance(request.data, dict) else {}
    return {**q, **body}


def parse_datatable_params(request: Request) -> tuple[int, int, int]:
    data = merge_payload(request)
    start = int(data.get("start") or 0)
    length = int(data.get("length") or 10)
    draw = int(data.get("draw") or 1)
    if length <= 0:
        length = 10
    page = (start // length) + 1
    return draw, page, length


def datatable_payload(*, draw: int, total: int, rows: list) -> dict:
    return {
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": rows,
    }


def page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return "LIMIT %(limit)s OFFSET %(offset)s", {"limit": page_size, "offset": offset}


def to_int(value, default=None):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_sy_staff(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("account_kind") == "sy_user":
        return True
    return str(user.get("user_type")) != "1" and user.get("account_kind") != "exp_user"
