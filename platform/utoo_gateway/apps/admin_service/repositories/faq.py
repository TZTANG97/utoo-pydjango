from __future__ import annotations

from typing import Any

from apps.admin_service.helpers import normalize_row, normalize_rows, page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar


def list_problems(
    *,
    problem_description: str = "",
    keywords: str = "",
    hits_order: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE cp.deleteStatus = 0"
    params: dict[str, Any] = {}
    if problem_description:
        where += " AND cp.problem_description LIKE %(problem_description)s"
        params["problem_description"] = f"%{problem_description}%"
    if keywords:
        where += " AND cp.keywords LIKE %(keywords)s"
        params["keywords"] = f"%{keywords}%"
    # Java：hits 空=正序 ASC；hits=2=倒序 DESC
    order_sql = "ORDER BY cp.hits DESC, cp.addTime DESC" if str(hits_order) == "2" else "ORDER BY cp.hits ASC, cp.addTime DESC"
    total = int(scalar(f"SELECT COUNT(*) FROM common_problem cp {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT cp.*
        FROM common_problem cp
        {where}
        {order_sql}
        {clause}
        """,
        {**params, **page_params},
    )
    return normalize_rows(rows), total


def insert_problem(
    *,
    problem_description: str,
    keywords: str,
    problem_answer: str,
    hits: int,
) -> int:
    return execute_insert(
        """
        INSERT INTO common_problem
            (addTime, deleteStatus, problem_description, keywords, problem_answer, hits)
        VALUES (NOW(), 0, %(problem_description)s, %(keywords)s, %(problem_answer)s, %(hits)s)
        """,
        {
            "problem_description": problem_description,
            "keywords": keywords,
            "problem_answer": problem_answer,
            "hits": hits,
        },
    )


def update_problem(
    *,
    problem_id: int,
    problem_description: str,
    keywords: str,
    problem_answer: str,
    hits: int,
) -> None:
    execute(
        """
        UPDATE common_problem
        SET problem_description = %(problem_description)s,
            keywords = %(keywords)s,
            problem_answer = %(problem_answer)s,
            hits = %(hits)s
        WHERE id = %(id)s
        """,
        {
            "id": problem_id,
            "problem_description": problem_description,
            "keywords": keywords,
            "problem_answer": problem_answer,
            "hits": hits,
        },
    )


def delete_problem(problem_id: int) -> int:
    return execute(
        "DELETE FROM common_problem WHERE id = %(id)s",
        {"id": problem_id},
    )


def get_problem(problem_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT * FROM common_problem WHERE id = %(id)s LIMIT 1",
        {"id": problem_id},
    )
    return normalize_row(row)
