from typing import Any

from apps.orders.repositories import company as company_repo


def sel_company_name_page(
    *,
    start: str = "0",
    length: str = "10",
    draw: str = "1",
    keyword: str = "",
) -> dict[str, Any]:
    offset = int(start) if str(start).isdigit() else 0
    limit = int(length) if str(length).isdigit() else 10
    total = company_repo.count_companies(keyword=keyword)
    rows = company_repo.list_companies_page(
        keyword=keyword, offset=offset, limit=limit
    )
    return {
        "data": rows,
        "draw": int(draw) if str(draw).isdigit() else 1,
        "recordsTotal": total,
        "recordsFiltered": total,
    }
