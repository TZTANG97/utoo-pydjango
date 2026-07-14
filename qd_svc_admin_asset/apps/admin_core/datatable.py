from __future__ import annotations

from rest_framework.request import Request


def parse_datatable_params(request: Request) -> tuple[int, int, int]:
    q = request.query_params
    body = request.data if isinstance(request.data, dict) else {}
    start = int(q.get("start") or body.get("start") or 0)
    length = int(q.get("length") or body.get("length") or 10)
    draw = int(q.get("draw") or body.get("draw") or 1)
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


def parse_datatable(request: Request) -> dict:
    q = {k: request.query_params.get(k) for k in request.query_params.keys()}
    body = request.data if isinstance(request.data, dict) else {}
    merged = {**q, **body}
    start = int(merged.get("start") or 0)
    length = int(merged.get("length") or 10)
    if length <= 0:
        length = 10
    return {
        **merged,
        "draw": int(merged.get("draw") or 1),
        "start": start,
        "length": length,
        "offset": start,
        "limit": length,
        "page": (start // length) + 1,
    }


def datatable_response(*, draw: int, total: int, rows: list) -> dict:
    return datatable_payload(draw=draw, total=total, rows=rows)
