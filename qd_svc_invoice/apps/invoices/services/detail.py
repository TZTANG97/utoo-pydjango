from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.core.db_utils import fetch_all, fetch_one, scalar
from qd_common.serialize import to_jsonable


def _file_url(path: str, name: str) -> str:
    base = (getattr(settings, "IMAGE_WEB_SERVER", "") or "").rstrip("/")
    if not base or not path or not name:
        return ""
    return f"{base}/{path.strip('/')}/{name.strip('/')}"


def get_invoice_apply_detail(*, user_id: int, apply_id: int) -> dict[str, Any] | None:
    ial = fetch_one(
        """
        SELECT t.*, u.userName, u.mobile
        FROM invoice_apply_log t
        LEFT JOIN exp_user u ON t.user_id = u.id
        WHERE t.id = %(aid)s AND t.deleteStatus = 0
        LIMIT 1
        """,
        {"aid": apply_id},
    )
    if not ial:
        return None
    if int(ial.get("user_id") or 0) != int(user_id):
        return None

    order_ids_raw = (ial.get("order_ids") or "").strip()
    of_list: list[dict[str, Any]] = []
    is_sqfp = True
    files: list[dict[str, Any]] = []

    for part in order_ids_raw.split(","):
        part = part.strip()
        if not part:
            continue
        oid = int(part)
        of_row = fetch_one(
            "SELECT * FROM experiment_order WHERE id = %(oid)s LIMIT 1",
            {"oid": oid},
        )
        if of_row:
            of_list.append(of_row)
        cnt = scalar(
            """
            SELECT COUNT(1) FROM invoice_apply_log
            WHERE deleteStatus = 0 AND FIND_IN_SET(%(oid)s, order_ids)
            """,
            {"oid": part},
            0,
        )
        if not cnt:
            is_sqfp = False

        acc_rows = fetch_all(
            """
            SELECT id, name, path, info, ext
            FROM accessory
            WHERE deleteStatus = 0 AND exp_of_id = %(oid)s
            """,
            {"oid": oid},
        )
        for d in acc_rows:
            d = dict(d)
            d["url"] = _file_url(d.get("path") or "", d.get("name") or "")
            files.append(d)

    logs = fetch_all(
        """
        SELECT * FROM invoice_record_log
        WHERE invoice_apply_id = %(aid)s
        ORDER BY addTime DESC
        """,
        {"aid": apply_id},
    )
    log_list = []
    for item in logs:
        item = dict(item)
        uid = item.get("userId") or item.get("user_id")
        if uid:
            u = fetch_one(
                "SELECT true_name, user_name FROM sy_users WHERE id = %(uid)s LIMIT 1",
                {"uid": str(uid)},
            )
            if u:
                item["addusername"] = u.get("true_name") or u.get("user_name")
        log_list.append(to_jsonable(item))

    return {
        "files": files,
        "obj": to_jsonable(ial),
        "ofList": [to_jsonable(x) for x in of_list],
        "ids": order_ids_raw,
        "isSqfp": is_sqfp,
        "logs": log_list,
    }
