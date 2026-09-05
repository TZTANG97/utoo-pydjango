from __future__ import annotations

import uuid
from typing import Any


def new_id() -> str:
    return uuid.uuid4().hex


def page_clause(page: int, page_size: int) -> tuple[str, dict[str, int]]:
    offset = max(page - 1, 0) * page_size
    return " LIMIT %(limit)s OFFSET %(offset)s", {
        "limit": page_size,
        "offset": offset,
    }


def build_tree(
    rows: list[dict[str, Any]],
    *,
    id_key: str = "id",
    parent_key: str = "superId",
    children_key: str = "children",
) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get(id_key) or "")
        if not rid:
            continue
        nodes[rid] = {**row, children_key: []}
    roots: list[dict[str, Any]] = []
    for rid, node in nodes.items():
        pid = node.get(parent_key)
        if pid and str(pid) in nodes and str(pid) != rid:
            nodes[str(pid)][children_key].append(node)
        else:
            roots.append(node)
    return roots
