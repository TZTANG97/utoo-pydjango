from collections import defaultdict
from typing import Any

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import catalog as catalog_repo


def _photo_url(base: str, path: str | None, name: str | None) -> str:
    if not name:
        return ""
    root = (base or "").rstrip("/")
    p = (path or "").strip("/")
    return f"{root}/{p}/{name}" if p else f"{root}/{name}"


def _load_photo_map(photo_ids: set[int]) -> dict[int, dict]:
    rows = catalog_repo.load_photo_rows(photo_ids)
    return {int(r["id"]): r for r in rows}


def build_index_class_list() -> list[dict[str, Any]]:
    config = get_config_row()
    image_server = image_web_server(config)
    rows = catalog_repo.list_all_experiment_manage()
    by_parent: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_parent[int(row.get("parent_id") or 0)].append(row)

    photo_ids = {
        int(r["manage_main_photo_id"])
        for r in rows
        if r.get("manage_main_photo_id")
    }
    photo_map = _load_photo_map(photo_ids)

    roots = [r for r in rows if r.get("type") == 1 and r.get("pt_type") == 2]
    roots.sort(key=lambda r: r.get("sequence") or 0)

    result: list[dict[str, Any]] = []
    for em in roots:
        sec_list = []
        for sec in by_parent.get(int(em["id"]), []):
            t_list = []
            for third in by_parent.get(int(sec["id"]), []):
                if not third.get("addTime"):
                    continue
                photo = photo_map.get(int(third.get("manage_main_photo_id") or 0), {})
                t_list.append(
                    {
                        "id": third["id"],
                        "name": third.get("name"),
                        "main_photo": _photo_url(
                            image_server,
                            photo.get("path"),
                            photo.get("name"),
                        ),
                    }
                )
            sec_list.append(
                {
                    "id": sec["id"],
                    "name": sec.get("name"),
                    "tList": t_list,
                }
            )
        photo = photo_map.get(int(em.get("manage_main_photo_id") or 0), {})
        result.append(
            {
                "id": em["id"],
                "name": em.get("name"),
                "main_photo": _photo_url(
                    image_server, photo.get("path"), photo.get("name")
                ),
                "secList": sec_list,
            }
        )
    return result


def sel_third_class_list(
    *,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    class_id: str = "",
) -> dict[str, Any]:
    config = get_config_row()
    image_server = image_web_server(config)
    page_size = int(length) if str(length).isdigit() else 10
    offset = int(start) if str(start).isdigit() else 0
    total = catalog_repo.count_third_classes(class_id=class_id)
    rows = catalog_repo.list_third_classes_page(
        class_id=class_id, offset=offset, limit=page_size
    )
    photo_map = _load_photo_map(
        {int(r["manage_main_photo_id"]) for r in rows if r.get("manage_main_photo_id")}
    )
    data = []
    for row in rows:
        photo = photo_map.get(int(row.get("manage_main_photo_id") or 0), {})
        item = dict(row)
        item["main_photo"] = _photo_url(
            image_server, photo.get("path"), photo.get("name")
        )
        data.append(item)
    return {
        "data": data,
        "draw": int(draw) if str(draw).isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def sel_fir_and_sec_class_list() -> list[dict[str, Any]]:
    config = get_config_row()
    image_server = image_web_server(config)
    rows = catalog_repo.list_fir_sec_manage()
    by_parent: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_parent[int(row.get("parent_id") or 0)].append(row)
    photo_map = _load_photo_map(
        {int(r["manage_main_photo_id"]) for r in rows if r.get("manage_main_photo_id")}
    )
    roots = [r for r in rows if r.get("type") == 1 and r.get("pt_type") == 2]
    roots.sort(key=lambda r: r.get("sequence") or 0)
    out: list[dict[str, Any]] = []
    for em in roots:
        sec_list: list[dict[str, Any]] = []
        for sec in by_parent.get(int(em["id"]), []):
            third_list = []
            for third in by_parent.get(int(sec["id"]), []):
                photo3 = photo_map.get(int(third.get("manage_main_photo_id") or 0), {})
                third_list.append(
                    {
                        "id": third["id"],
                        "name": third.get("name"),
                        "main_photo": _photo_url(
                            image_server, photo3.get("path"), photo3.get("name")
                        ),
                    }
                )
            if not third_list:
                continue
            photo2 = photo_map.get(int(sec.get("manage_main_photo_id") or 0), {})
            sec_list.append(
                {
                    "id": sec["id"],
                    "name": sec.get("name"),
                    "main_photo": _photo_url(
                        image_server, photo2.get("path"), photo2.get("name")
                    ),
                    "childList": third_list,
                }
            )
        if sec_list:
            out.append({"id": em["id"], "name": em.get("name"), "childList": sec_list})
    return out


def sel_third_class_by_keyword(
    *,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    key_word: str = "",
) -> dict[str, Any]:
    config = get_config_row()
    image_server = image_web_server(config)
    page_size = int(length) if str(length).isdigit() else 10
    offset = int(start) if str(start).isdigit() else 0
    total = catalog_repo.count_third_by_keyword(key_word=key_word)
    rows = catalog_repo.list_third_by_keyword_page(
        key_word=key_word, offset=offset, limit=page_size
    )
    photo_map = _load_photo_map(
        {int(r["manage_main_photo_id"]) for r in rows if r.get("manage_main_photo_id")}
    )
    data: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        cid = int(item["id"])
        photo = photo_map.get(int(item.get("manage_main_photo_id") or 0), {})
        item["main_photo"] = _photo_url(
            image_server, photo.get("path"), photo.get("name")
        )
        item["count"] = catalog_repo.count_orders_by_class(cid)
        item["test_price"] = catalog_repo.get_first_test_price(cid)
        data.append(item)
    return {
        "data": data,
        "draw": int(draw) if str(draw).isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }
