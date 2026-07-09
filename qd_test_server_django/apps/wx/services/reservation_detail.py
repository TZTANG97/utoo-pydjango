from typing import Any

from django.conf import settings

from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.wx.repositories import reservation as res_repo
from qd_common.serialize import to_jsonable


def _photo_url(base: str, path: str | None, name: str | None) -> str:
    if not name:
        return ""
    root = (base or "").rstrip("/")
    p = (path or "").strip("/")
    return f"{root}/{p}/{name}" if p else f"{root}/{name}"


def _enrich_files(rows: list[dict[str, Any]], image_base: str) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        item = dict(row)
        item["url"] = _photo_url(image_base, item.get("path"), item.get("name"))
        out.append(item)
    return out


def _sample_attributes(attribute_id: str) -> list[dict[str, Any]]:
    if not attribute_id.strip():
        return []
    erji_list: list[dict[str, Any]] = []
    sanji_list: list[dict[str, Any]] = []
    for group in attribute_id.split(";"):
        parts = [p.strip() for p in group.split(":") if p.strip()]
        if not parts:
            continue
        if parts[0].isdigit():
            parent = res_repo.get_sample_attribute(int(parts[0]))
            if parent:
                erji_list.append(dict(parent))
        for cid in parts[1:]:
            if cid.isdigit():
                crow = res_repo.get_sample_attribute(int(cid))
                if crow:
                    sanji_list.append(dict(crow))
    for erji in erji_list:
        erji_id = erji.get("id")
        erji["attributeListsanji"] = [
            s for s in sanji_list if s.get("parent_id") == erji_id
        ]
    return [to_jsonable(e) for e in erji_list]


def get_reservation_detail(*, user_id: int, consult_id: int) -> dict[str, Any] | None:
    row = res_repo.get_consult_row(user_id=user_id, consult_id=consult_id)
    if not row:
        return None

    config = get_config_row()
    image_base = image_web_server(config) or getattr(settings, "IMAGE_WEB_SERVER", "")

    st = int(row.get("status") or 0)
    reverso = str(row.get("reverso_context") or "")
    body: dict[str, Any] = {
        "className": row.get("className") or "",
        "userName": row.get("userName") or "",
        "order_num": "",
        "order_id": row.get("order_id"),
        "order_type": "",
        "mobile": row.get("mobile") or "",
        "company_name": row.get("company_name") or "",
        "content": row.get("content") or "",
        "syUserName": row.get("syUserName") or "",
        "send_address": row.get("send_address") or "",
        "order_status": 0,
        "status": st,
        "reverso_context": "是" if reverso == "1" else "否",
        "addressee_name": row.get("addressee_name") or "",
        "addressee_mobile": row.get("addressee_mobile") or "",
        "is_video": row.get("is_video"),
        "is_cancel": 0 if st in (2, 3) else 1,
        "is_arrive": row.get("is_arrive"),
        "is_on": row.get("is_on"),
        "childs": res_repo.list_consult_children(consult_id),
        "files": _enrich_files(res_repo.list_consult_files(consult_id), image_base),
        "ypList": [],
    }

    if row.get("order_id"):
        of = res_repo.get_order_brief(int(row["order_id"]))
        if of:
            body["order_num"] = of.get("order_id") or ""
            body["order_type"] = of.get("order_type") or ""
            body["order_status"] = int(of.get("order_status") or 0)

    yp_list = []
    for yr in res_repo.list_sample_rows(consult_id):
        item = to_jsonable(dict(yr))
        item["sampleAttributeManageList"] = _sample_attributes(
            str(item.get("attribute_id") or "")
        )
        yp_list.append(item)
    body["ypList"] = yp_list
    return body
