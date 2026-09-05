from __future__ import annotations

from rest_framework.request import Request


def merge_payload(request: Request) -> dict:
    # QueryDict 用 ** 展开会变成 list；.get() 才是单值字符串
    raw = request.data
    if hasattr(raw, "get") and hasattr(raw, "keys"):
        body = {k: raw.get(k) for k in raw.keys()}
    else:
        body = {}
    query = {k: request.query_params.get(k) for k in request.query_params.keys()}
    return {**query, **body}


def split_ids(raw) -> list[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if item not in (None, "")]
    return [part.strip() for part in str(raw).split(",") if part.strip()]
