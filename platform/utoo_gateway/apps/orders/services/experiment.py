from collections import defaultdict
from typing import Any

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.orders.repositories import catalog as catalog_repo
from apps.orders.repositories import orders as repo
from apps.orders.services.catalog import _load_photo_map, _photo_url


def build_index_exp_list() -> list[dict[str, Any]]:
    config = get_config_row()
    image_server = image_web_server(config)
    rows = catalog_repo.list_all_experiment_manage()
    by_parent: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_parent[int(row.get("parent_id") or 0)].append(row)
    photo_map = _load_photo_map(
        {int(r["manage_main_photo_id"]) for r in rows if r.get("manage_main_photo_id")}
    )
    roots = [r for r in rows if r.get("type") == 1 and r.get("pt_type") == 2]
    roots.sort(key=lambda r: r.get("sequence") or 0)
    result: list[dict[str, Any]] = []
    for em in roots:
        photo = photo_map.get(int(em.get("manage_main_photo_id") or 0), {})
        sec_list = []
        for sec in by_parent.get(int(em["id"]), []):
            photo2 = photo_map.get(int(sec.get("manage_main_photo_id") or 0), {})
            third_list = [
                {"id": t["id"], "name": t.get("name")}
                for t in by_parent.get(int(sec["id"]), [])
            ]
            sec_list.append(
                {
                    "id": sec["id"],
                    "name": sec.get("name"),
                    "main_photo": _photo_url(
                        image_server, photo2.get("path"), photo2.get("name")
                    ),
                    "intro": sec.get("intro") or "",
                    "project_details": sec.get("project_details") or "",
                    "childList": third_list,
                }
            )
        result.append(
            {
                "id": em["id"],
                "name": em.get("name"),
                "main_photo": _photo_url(
                    image_server, photo.get("path"), photo.get("name")
                ),
                "intro": em.get("intro") or "",
                "project_details": em.get("project_details") or "",
                "childList": sec_list,
            }
        )
    return result


def sel_exp_list(
    *,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    class_id: str = "",
    key_word: str = "",
) -> dict[str, Any]:
    config = get_config_row()
    image_server = image_web_server(config)
    first_id = ""
    sec_id = ""
    if class_id and class_id.isdigit():
        em = repo.get_experiment_manage(int(class_id))
        if em:
            if em.get("type") == 1:
                first_id = str(em["id"])
            elif em.get("type") == 2:
                sec_id = str(em["id"])
    page_size = int(length) if length.isdigit() else 10
    offset = int(start) if start.isdigit() else 0
    total = catalog_repo.count_sel_exp_list(
        key_word=key_word, sec_id=sec_id, first_id=first_id
    )
    rows = catalog_repo.list_sel_exp_page(
        key_word=key_word,
        sec_id=sec_id,
        first_id=first_id,
        offset=offset,
        limit=page_size,
    )
    photo_map = _load_photo_map(
        {int(r["manage_main_photo_id"]) for r in rows if r.get("manage_main_photo_id")}
    )
    data = []
    for row in rows:
        item = dict(row)
        photo = photo_map.get(int(item.get("manage_main_photo_id") or 0), {})
        item["main_photo"] = _photo_url(
            image_server, photo.get("path"), photo.get("name")
        )
        data.append(item)
    return {
        "data": data,
        "draw": int(draw) if draw.isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }


def test_class_detail(em_id: int) -> dict[str, Any] | None:
    em = repo.get_experiment_manage(em_id)
    if not em:
        return None
    config = get_config_row()
    image_server = image_web_server(config)
    photos_url: list[str] = []
    if em.get("manage_main_photo_id"):
        photo_map = _load_photo_map({int(em["manage_main_photo_id"])})
        photo = photo_map.get(int(em["manage_main_photo_id"]), {})
        main_url = _photo_url(image_server, photo.get("path"), photo.get("name"))
        if main_url:
            photos_url.append(main_url)
    for row in catalog_repo.fetch_manage_extra_accessories(em_id):
        url = _photo_url(image_server, row.get("path"), row.get("name"))
        if url:
            photos_url.append(url)
    special_type = None
    if em.get("parent_id"):
        parent = repo.get_experiment_manage(int(em["parent_id"]))
        if parent and parent.get("parent_id"):
            root = repo.get_experiment_manage(int(parent["parent_id"]))
            if root:
                special_type = root.get("special_type")
    return {
        "manage_photos": photos_url,
        "name": em.get("name"),
        "app_project_details": em.get("project_details") or "",
        "special_type": special_type,
    }
