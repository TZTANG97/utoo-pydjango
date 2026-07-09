from typing import Any

from apps.orders.repositories import test_or_sure as repo


def list_test_or_sure_children(
    *, user_id: int, order_id: int, action_type: str
) -> list[dict[str, Any]]:
    del action_type
    parent = repo.get_online_parent_order(order_id)
    if not parent or int(parent.get("is_online") or 0) != 1:
        return []
    if int(parent.get("custom_user_id") or 0) != int(user_id):
        return []
    return repo.list_eligible_children(order_id)
