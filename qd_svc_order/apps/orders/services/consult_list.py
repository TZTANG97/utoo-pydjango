"""预约列表 / 取消 — 业务层（无 SQL）"""
from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import consult as consult_repo
from apps.orders.services.catalog import _load_photo_map, _photo_url


def exp_make_list() -> list[dict[str, Any]]:
    config = get_config_row()
    image_server = image_web_server(config)
    rows = consult_repo.list_reservable_manage_rows()
    photo_ids = {
        int(r["manage_main_photo_id"])
        for r in rows
        if r.get("manage_main_photo_id")
    }
    photo_map = _load_photo_map(photo_ids)
    out: list[dict[str, Any]] = []
    for em in rows:
        photo = photo_map.get(int(em.get("manage_main_photo_id") or 0))
        path = photo.get("path") if photo else None
        name = photo.get("name") if photo else None
        out.append(
            {
                "id": em["id"],
                "name": em.get("name"),
                "main_photo": _photo_url(image_server, path, name),
                "title": "简短的描述字段",
            }
        )
    return out


def my_exp_make_list(
    *,
    user_id: int,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    startime: str = "",
    endtime: str = "",
) -> dict[str, Any]:
    offset = int(start) if start.isdigit() else 0
    limit = int(length) if length.isdigit() else 10
    total = consult_repo.count_user_consults(
        user_id=user_id, startime=startime, endtime=endtime
    )
    rows = consult_repo.list_user_consults_page(
        user_id=user_id,
        offset=offset,
        limit=limit,
        startime=startime,
        endtime=endtime,
    )
    data = []
    for row in rows:
        item = dict(row)
        st = int(item.get("status") or 0)
        item["is_cancel"] = 0 if st in (2, 3) else 1
        data.append(item)
    return {
        "data": data,
        "draw": int(draw) if draw.isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def exp_user_log_list(user_id: int) -> list[dict[str, Any]]:
    result = my_exp_make_list(
        user_id=user_id, start="0", length="100000", draw="1"
    )
    return [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "addTime": item.get("addTime"),
            "order_num": item.get("order_num"),
        }
        for item in (result.get("data") or [])
    ]


@transaction.atomic
def cancel_consult(*, user_id: int, consult_id: int) -> tuple[bool, str]:
    row = consult_repo.get_consult_owner(consult_id)
    if not row:
        return False, "预约不存在"
    if int(row["user_id"]) != int(user_id):
        return False, "无权操作"
    consult_repo.mark_consult_cancelled(consult_id)
    consult_repo.insert_exp_user_log(user_id=user_id, info="实验预约已取消")
    return True, "取消预约成功!"
