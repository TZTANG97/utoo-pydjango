"""样品属性 / 稳定性 / 属性树 — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any, Optional

from apps.orders.repositories import sample as sample_repo


def list_attribute_states() -> list[dict[str, Any]]:
    return sample_repo.list_attribute_states()


def list_stability() -> list[dict[str, Any]]:
    return sample_repo.list_stability_rows()


def sample_attribute_manage_tree(*, special_id: int) -> Optional[dict[str, Any]]:
    root = sample_repo.get_attribute_root(special_id)
    if not root:
        return None

    children: list[dict[str, Any]] = []
    for node in sample_repo.list_attribute_children(int(root["id"]), level=2):
        n = dict(node)
        n["attributeManageList"] = [
            dict(r)
            for r in sample_repo.list_attribute_children(int(n["id"]), level=3)
        ]
        children.append(n)

    result = dict(root)
    result["attributeManageList"] = children
    return result
