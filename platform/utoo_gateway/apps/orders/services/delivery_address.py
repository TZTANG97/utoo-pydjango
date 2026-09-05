import logging
from datetime import datetime
from typing import Any

from django.db import transaction

from apps.orders.repositories import delivery_address as addr_repo

logger = logging.getLogger(__name__)


def _bit_to_int(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, (bytes, bytearray)):
        return 1 if val and val[0] else 0
    if isinstance(val, bool):
        return 1 if val else 0
    return int(val)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    d = dict(row)
    if d.get("is_default") is not None:
        d["is_default"] = _bit_to_int(d["is_default"]) == 1
    if d.get("deleteStatus") is not None:
        d["deleteStatus"] = _bit_to_int(d["deleteStatus"]) == 0
    return d


def list_delivery_addresses(user_id: int) -> list[dict[str, Any]]:
    rows = addr_repo.list_delivery_addresses(user_id)
    return [_normalize_row(r) for r in rows]


def get_default_address_text(user_id: int) -> str:
    rows = list_delivery_addresses(user_id)
    if not rows:
        return addr_repo.get_user_address_info(user_id)
    default = rows[0]
    for row in rows:
        if row.get("is_default"):
            default = row
            break
    area = default.get("delivery_address") or default.get("address") or ""
    detail = default.get("address_detail") or default.get("detail") or ""
    return f"{area}{detail}".strip()


def resolve_delivery_address_text(delivery_address_ids: str) -> tuple[str, str]:
    raw = (delivery_address_ids or "").strip()
    if not raw:
        return "", raw
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) < 3:
        return raw, raw
    names = [addr_repo.get_district_name(pid) for pid in parts[:3]]
    return "".join(names), ",".join(parts[:3])


def get_delivery_address_list(user_id: int) -> dict[str, Any]:
    return {"expUserDeliveryAddresses": list_delivery_addresses(user_id)}


@transaction.atomic
def insert_delivery_address(
    *,
    user_id: int,
    delivery_name: str,
    delivery_phone: str,
    delivery_address: str,
    detail_address: str,
) -> tuple[bool, str]:
    if not (delivery_name or "").strip():
        return False, "收件人姓名不能为空"
    if not (delivery_phone or "").strip():
        return False, "电话号码不能为空"
    addr_text, addr_ids = resolve_delivery_address_text(delivery_address)
    is_default = 0 if addr_repo.count_user_addresses(user_id) else 1
    try:
        addr_repo.insert_delivery_address_row(
            add_time=datetime.now(),
            user_id=user_id,
            delivery_name=delivery_name.strip(),
            delivery_phone=delivery_phone.strip(),
            addr_text=addr_text,
            detail_address=detail_address or "",
            addr_ids=addr_ids,
            is_default=is_default,
        )
        return True, "新增成功"
    except Exception as exc:
        logger.exception("insert_delivery_address failed: %s", exc)
        return False, f"新增失败：{exc}"


@transaction.atomic
def update_delivery_address(
    *,
    user_id: int,
    record_id: int,
    delivery_name: str,
    delivery_phone: str,
    delivery_address: str,
    detail_address: str,
) -> tuple[bool, str]:
    if not addr_repo.get_owned_address(record_id, user_id):
        return False, "收件地址不存在"
    addr_text, addr_ids = resolve_delivery_address_text(delivery_address)
    try:
        addr_repo.update_delivery_address_row(
            record_id=record_id,
            user_id=user_id,
            delivery_name=delivery_name.strip(),
            delivery_phone=delivery_phone.strip(),
            addr_text=addr_text,
            detail_address=detail_address or "",
            addr_ids=addr_ids,
        )
        return True, "修改成功！"
    except Exception as exc:
        logger.exception("update_delivery_address failed: %s", exc)
        return False, f"修改失败：{exc}"


@transaction.atomic
def delete_or_set_default_address(
    *, user_id: int, record_id: int, op_type: str
) -> tuple[bool, str]:
    row = addr_repo.get_owned_address(record_id, user_id)
    if not row:
        return False, "收件地址不存在"

    if op_type == "1":
        if _bit_to_int(row.get("is_default")) == 1:
            return False, "默认地址不能删除！"
        try:
            addr_repo.soft_delete_address(record_id)
            return True, "删除成功！"
        except Exception as exc:
            return False, f"删除失败：{exc}"

    if op_type == "2":
        try:
            addr_repo.clear_default_addresses(user_id)
            addr_repo.set_address_default(record_id)
            return True, "设置成功！"
        except Exception as exc:
            return False, f"设置失败：{exc}"

    return False, "无效操作类型"
