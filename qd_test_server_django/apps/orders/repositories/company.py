from typing import Any

from apps.core.db_utils import fetch_all, scalar


def count_companies(*, keyword: str = "") -> int:
    where = " WHERE delete_status = 0 AND type = 3"
    params: dict[str, Any] = {}
    if keyword.strip():
        where += " AND name LIKE %(kw)s"
        params["kw"] = f"%{keyword.strip()}%"
    return int(
        scalar(f"SELECT COUNT(1) FROM qd_user_company{where}", params, 0) or 0
    )


def list_companies_page(
    *, keyword: str = "", offset: int = 0, limit: int = 10
) -> list[dict[str, Any]]:
    where = " WHERE delete_status = 0 AND type = 3"
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if keyword.strip():
        where += " AND name LIKE %(kw)s"
        params["kw"] = f"%{keyword.strip()}%"
    return fetch_all(
        f"""
        SELECT * FROM qd_user_company{where}
        ORDER BY add_time DESC LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
    )
