from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_proposals(
    *,
    platform: str = "",
    is_confirmed: str = "",
    order_startime: str = "",
    order_endtime: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """对齐 Java getListBymap1：未传 platform 时仅查 UTOO 相关（2=愉兔, 4=途哲）。"""
    where = "WHERE pi.deleteStatus = 0"
    params: dict[str, Any] = {}
    if platform:
        where += " AND pi.platform = %(platform)s"
        params["platform"] = platform
    else:
        # Java: and(pi.platform = 2 or pi.platform = 4)
        where += " AND pi.platform IN (2, 4)"
    if is_confirmed != "":
        where += " AND pi.is_confirmed = %(is_confirmed)s"
        params["is_confirmed"] = int(is_confirmed)
    if order_startime:
        where += " AND pi.addTime >= %(order_startime)s"
        params["order_startime"] = order_startime
    if order_endtime:
        where += " AND pi.addTime <= %(order_endtime)s"
        params["order_endtime"] = order_endtime
    total = int(
        scalar(f"SELECT COUNT(*) FROM proposal_improve pi {where}", params) or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT pi.*, su.user_name AS userName, su.true_name AS trueName
        FROM proposal_improve pi
        LEFT JOIN sy_users su ON pi.user_id = su.id
        {where}
        ORDER BY pi.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def get_proposal_detail(proposal_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT pi.*, su.user_name AS userName, su.true_name AS trueName
        FROM proposal_improve pi
        LEFT JOIN sy_users su ON pi.user_id = su.id
        WHERE pi.id = %(id)s AND pi.deleteStatus = 0
        LIMIT 1
        """,
        {"id": proposal_id},
    )
    if not row:
        return None
    logs = fetch_all(
        """
        SELECT pil.*, su.user_name AS userName
        FROM proposal_improve_log pil
        LEFT JOIN sy_users su ON pil.user_id = su.id
        WHERE pil.improve_id = %(id)s
        ORDER BY pil.addTime ASC
        """,
        {"id": proposal_id},
    )
    files = fetch_all(
        """
        SELECT id, path, name, info, ext
        FROM accessory
        WHERE improve_id = %(id)s
          AND (deleteStatus = 0 OR deleteStatus IS NULL)
        ORDER BY id ASC
        """,
        {"id": proposal_id},
    )
    return {
        "obj": normalize_row(row),
        "logs": normalize_rows(logs),
        "files": normalize_rows(files),
    }


def add_proposal(
    *,
    content: str,
    platform: str,
    user_id: str,
    accessory_ids: list[int] | None = None,
) -> dict[str, Any]:
    """对齐 Java productOrder/addProposalImprove.ajax。"""
    new_id = execute_insert(
        """
        INSERT INTO proposal_improve
            (addTime, deleteStatus, user_id, platform, content, type, is_confirmed, update_time)
        VALUES
            (NOW(), 0, %(uid)s, %(platform)s, %(content)s, 'proposal', 0, NOW())
        """,
        {
            "uid": (user_id or "")[:64],
            "platform": (platform or "")[:32],
            "content": content,
        },
    )
    for aid in accessory_ids or []:
        if not aid:
            continue
        execute(
            """
            UPDATE accessory
            SET improve_id = %(pid)s
            WHERE id = %(aid)s
              AND (deleteStatus = 0 OR deleteStatus IS NULL)
            """,
            {"pid": new_id, "aid": int(aid)},
        )
    row = fetch_one(
        """
        SELECT *
        FROM proposal_improve
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": new_id},
    )
    return normalize_row(row) or {"id": new_id}


def update_proposal(
    *,
    proposal_id: int,
    is_confirmed: int,
    operator_id: str,
    log_info: str,
) -> None:
    execute(
        """
        UPDATE proposal_improve
        SET is_confirmed = %(is_confirmed)s, update_time = NOW()
        WHERE id = %(id)s AND deleteStatus = 0
        """,
        {"id": proposal_id, "is_confirmed": is_confirmed},
    )
    execute_insert(
        """
        INSERT INTO proposal_improve_log
            (addTime, deleteStatus, user_id, info, improve_id)
        VALUES (NOW(), 0, %(user_id)s, %(info)s, %(improve_id)s)
        """,
        {
            "user_id": operator_id,
            "info": log_info,
            "improve_id": proposal_id,
        },
    )
