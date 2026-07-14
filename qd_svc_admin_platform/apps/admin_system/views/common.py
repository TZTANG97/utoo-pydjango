from __future__ import annotations

from rest_framework.request import Request


def merge_payload(request: Request) -> dict:
    body = request.data if isinstance(request.data, dict) else {}
    query = {k: request.query_params.get(k) for k in request.query_params.keys()}
    return {**query, **body}


def split_ids(raw) -> list[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if item not in (None, "")]
    return [part.strip() for part in str(raw).split(",") if part.strip()]
