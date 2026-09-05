import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import unquote

from django.db import transaction

from apps.orders.repositories import consult as consult_repo

logger = logging.getLogger(__name__)

_SAMPLE_COLS = (
    "sample_num",
    "sample_name",
    "main_component",
    "attribute_state",
    "is_magnetic",
    "is_gold_spraying",
    "stability",
    "attribute_id",
    "gold_desc",
)


def parse_sample_information_list(raw: str) -> list[dict[str, Any]]:
    if not raw or not str(raw).strip():
        return []
    decoded = unquote(str(raw))
    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError:
        logger.warning("sampleInformationList JSON parse failed")
        return []
    if not isinstance(payload, dict):
        return []
    items = payload.get("sampleInformationList")
    if items is None or items == "null":
        return []
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def _save_order_samples(*, consult_id: int, samples: list[dict[str, Any]]) -> None:
    for item in samples:
        cols: dict[str, Any] = {"consult_id": consult_id, "deleteStatus": 0}
        for key in _SAMPLE_COLS:
            if key not in item:
                continue
            val = item[key]
            if val is None or val == "":
                continue
            if key in ("sample_num", "is_magnetic", "is_gold_spraying", "attribute_state"):
                try:
                    cols[key] = int(val)
                except (TypeError, ValueError):
                    cols[key] = val
            else:
                cols[key] = val
        consult_repo.insert_order_sample_row(cols)


def _link_consult_accessories(*, consult_id: int, order_list: str) -> None:
    if not order_list or not str(order_list).strip():
        return
    for part in str(order_list).split(","):
        acc_id = part.strip()
        if not acc_id or not acc_id.isdigit():
            continue
        consult_repo.link_accessory_to_consult(
            consult_id=consult_id, accessory_id=int(acc_id)
        )


@transaction.atomic
def create_consult(
    *,
    user_id: int,
    user_name: str,
    mobile: str,
    company_name: str,
    content: str,
    class_id: int,
    recycle: str = "false",
    address: str = "",
    addressee_name: str = "",
    addressee_mobile: str = "",
    is_video: str = "false",
    is_arrive: str = "false",
    is_on: str = "false",
    sample_information_list: str = "",
    order_list: str = "",
) -> tuple[bool, str, int | None]:
    order_num = datetime.now().strftime("%Y%m%d%H%M%S") + str(user_id)[-4:]
    consult_id = consult_repo.insert_service_consult(
        {
            "user_name": user_name,
            "mobile": mobile,
            "company_name": company_name or "",
            "content": content or "",
            "class_id": class_id,
            "user_id": user_id,
            "reverso": "1" if recycle == "true" else "2",
            "address": address or "",
            "addressee_name": addressee_name or "",
            "addressee_mobile": addressee_mobile or "",
            "is_video": 1 if is_video == "true" else 0,
            "is_arrive": 1 if is_arrive == "true" else 0,
            "is_on": 1 if is_on == "true" else 0,
            "order_num": order_num,
        }
    )
    if not consult_id:
        return False, "预约提交失败", None

    samples = parse_sample_information_list(sample_information_list)
    if samples:
        _save_order_samples(consult_id=consult_id, samples=samples)
    _link_consult_accessories(consult_id=consult_id, order_list=order_list)
    try:
        consult_repo.insert_exp_user_log(user_id=user_id, info="实验预约成功")
    except Exception:
        pass
    return True, "您的预约已提交成功", consult_id
