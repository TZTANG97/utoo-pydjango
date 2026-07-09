from typing import Any

from apps.core.db_utils import fetch_all, scalar


def load_photo_rows(photo_ids: set[int]) -> list[dict[str, Any]]:
    if not photo_ids:
        return []
    ids = ",".join(str(i) for i in photo_ids)
    return fetch_all(
        f"""
        SELECT id, path, name FROM accessory
        WHERE id IN ({ids}) AND deleteStatus = 0
        """
    )


def list_all_experiment_manage() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, parent_id, type, pt_type, name, sequence, manage_main_photo_id,
               addTime, intro, project_details
        FROM experiment_manage
        WHERE deleteStatus = 0
        ORDER BY sequence ASC
        """
    )


def _sel_exp_where(
    *, key_word: str = "", sec_id: str = "", first_id: str = ""
) -> tuple[str, dict[str, Any]]:
    where_parts = ["t.deleteStatus = 0", "p.parent_id IS NOT NULL"]
    params: dict[str, Any] = {}
    if key_word:
        where_parts.append("t.name LIKE %(name)s")
        params["name"] = f"%{key_word}%"
    if sec_id:
        where_parts.append("t.parent_id = %(parent_id)s")
        params["parent_id"] = int(sec_id)
    if first_id:
        where_parts.append("p1.id = %(first_id)s")
        params["first_id"] = int(first_id)
    return " AND ".join(where_parts), params


def count_sel_exp_list(
    *, key_word: str = "", sec_id: str = "", first_id: str = ""
) -> int:
    where_sql, params = _sel_exp_where(
        key_word=key_word, sec_id=sec_id, first_id=first_id
    )
    return int(
        scalar(
            f"""
            SELECT COUNT(1) FROM experiment_manage t
            LEFT JOIN experiment_manage p ON t.parent_id = p.id
            LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
            WHERE {where_sql}
            """,
            params,
            0,
        )
        or 0
    )


def list_sel_exp_page(
    *,
    key_word: str = "",
    sec_id: str = "",
    first_id: str = "",
    offset: int = 0,
    limit: int = 10,
) -> list[dict[str, Any]]:
    where_sql, params = _sel_exp_where(
        key_word=key_word, sec_id=sec_id, first_id=first_id
    )
    params["limit"] = limit
    params["offset"] = offset
    return fetch_all(
        f"""
        SELECT t.id, t.name, t.manage_main_photo_id, t.intro, t.sequence,
               p.name AS typeName, p1.name AS firstName
        FROM experiment_manage t
        LEFT JOIN experiment_manage p ON t.parent_id = p.id
        LEFT JOIN experiment_manage p1 ON p.parent_id = p1.id
        WHERE {where_sql}
        ORDER BY t.sequence ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )


def fetch_manage_extra_accessories(em_id: int) -> list[dict[str, Any]]:
    try:
        return fetch_all(
            """
            SELECT a.path, a.name FROM accessory a
            WHERE a.deleteStatus = 0 AND a.exp_of_id = %(em_id)s
            """,
            {"em_id": em_id},
        )
    except Exception:
        return []


def count_third_classes(*, class_id: str = "") -> int:
    where = "t.deleteStatus = 0 AND t.type = 3"
    params: dict[str, Any] = {}
    if class_id and str(class_id).isdigit():
        where += " AND t.parent_id = %(pid)s"
        params["pid"] = int(class_id)
    return int(
        scalar(f"SELECT COUNT(1) FROM experiment_manage t WHERE {where}", params, 0) or 0
    )


def list_third_classes_page(
    *, class_id: str = "", offset: int = 0, limit: int = 10
) -> list[dict[str, Any]]:
    where = "t.deleteStatus = 0 AND t.type = 3"
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if class_id and str(class_id).isdigit():
        where += " AND t.parent_id = %(pid)s"
        params["pid"] = int(class_id)
    return fetch_all(
        f"""
        SELECT t.id, t.name, t.manage_main_photo_id, t.intro, t.sequence, t.parent_id
        FROM experiment_manage t
        WHERE {where}
        ORDER BY t.sequence ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )


def list_fir_sec_manage() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, parent_id, type, pt_type, name, sequence, manage_main_photo_id
        FROM experiment_manage
        WHERE deleteStatus = 0
        ORDER BY sequence ASC
        """
    )


def count_third_by_keyword(*, key_word: str = "") -> int:
    where = "t.deleteStatus = 0 AND t.type = 3"
    params: dict[str, Any] = {}
    if key_word and key_word.strip():
        where += " AND t.name LIKE %(kw)s"
        params["kw"] = f"%{key_word.strip()}%"
    return int(
        scalar(f"SELECT COUNT(1) FROM experiment_manage t WHERE {where}", params, 0) or 0
    )


def list_third_by_keyword_page(
    *, key_word: str = "", offset: int = 0, limit: int = 10
) -> list[dict[str, Any]]:
    where = "t.deleteStatus = 0 AND t.type = 3"
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if key_word and key_word.strip():
        where += " AND t.name LIKE %(kw)s"
        params["kw"] = f"%{key_word.strip()}%"
    return fetch_all(
        f"""
        SELECT t.id, t.name, t.manage_main_photo_id
        FROM experiment_manage t
        WHERE {where}
        ORDER BY t.sequence ASC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )


def count_orders_by_class(class_id: int) -> int:
    return int(
        scalar(
            """
            SELECT COUNT(DISTINCT custom_user_id) FROM experiment_order
            WHERE order_status > 0 AND class_id = %(cid)s
            """,
            {"cid": class_id},
            0,
        )
        or 0
    )


def get_first_test_price(class_id: int) -> float:
    rows = fetch_all(
        """
        SELECT test_price FROM experiment_project
        WHERE class_id = %(cid)s ORDER BY id ASC LIMIT 1
        """,
        {"cid": class_id},
    )
    return float(rows[0]["test_price"] or 0) if rows else 0.0


def fetch_project_name_map(project_ids: list[int]) -> dict[int, str]:
    if not project_ids:
        return {}
    uniq = sorted(set(project_ids))
    placeholders = ", ".join(str(i) for i in uniq)
    try:
        rows = fetch_all(
            f"SELECT id, project_name FROM experiment_project WHERE id IN ({placeholders})"
        )
        return {int(r["id"]): (r["project_name"] or "") for r in rows}
    except Exception:
        return {}
