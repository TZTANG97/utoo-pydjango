"""附件查询 — 订单详情 / 列表"""
from __future__ import annotations

import logging
from typing import Any

from apps.core.db_utils import fetch_all

logger = logging.getLogger(__name__)


def load_accessories(
    *,
    exp_of_id: int | None = None,
    child_of_id: int | None = None,
    file_type: int | None = None,
    exclude_types: tuple[int, ...] | None = None,
) -> list[dict[str, Any]]:
    clauses = ["deleteStatus = 0"]
    params: dict[str, Any] = {}
    if exp_of_id is not None:
        # Java 实验单附件挂 of_id；本仓新建多写 exp_of_id。复制/详情需两边都查。
        clauses.append("(exp_of_id = %(eid)s OR of_id = %(eid)s)")
        params["eid"] = exp_of_id
    if child_of_id is not None:
        clauses.append("child_of_id = %(cid)s")
        params["cid"] = child_of_id
    if file_type is not None:
        clauses.append("type = %(tp)s")
        params["tp"] = file_type
    if exclude_types:
        clauses.append(
            "IFNULL(type, 0) NOT IN ("
            + ",".join(str(t) for t in exclude_types)
            + ")"
        )
    try:
        return fetch_all(
            f"SELECT * FROM accessory WHERE {' AND '.join(clauses)} ORDER BY id ASC",
            params,
        )
    except Exception as exc:
        # 极端环境若无 of_id 列，回退仅 exp_of_id
        if exp_of_id is not None and "of_id" in str(exc).lower():
            try:
                clauses2 = ["deleteStatus = 0", "exp_of_id = %(eid)s"]
                if child_of_id is not None:
                    clauses2.append("child_of_id = %(cid)s")
                if file_type is not None:
                    clauses2.append("type = %(tp)s")
                if exclude_types:
                    clauses2.append(
                        "IFNULL(type, 0) NOT IN ("
                        + ",".join(str(t) for t in exclude_types)
                        + ")"
                    )
                return fetch_all(
                    f"SELECT * FROM accessory WHERE {' AND '.join(clauses2)} ORDER BY id ASC",
                    params,
                )
            except Exception as exc2:
                logger.warning("load_accessories fallback failed: %s", exc2)
                return []
        logger.warning("load_accessories failed: %s", exc)
        return []


def load_all_test_files(sale_order_id: int) -> list[dict[str, Any]]:
    try:
        return fetch_all(
            """
            SELECT t.* FROM accessory t
            WHERE t.deleteStatus = 0 AND t.type = 4
              AND t.child_of_id IN (
                SELECT poc.order_child_id
                FROM experiment_order p
                LEFT JOIN experiment_order s ON p.parent_id = s.id
                LEFT JOIN exp_qd_purchase_order_child poc ON p.id = poc.purchase_order_id
                WHERE p.order_status > 0 AND s.id = %(sid)s
              )
            """,
            {"sid": sale_order_id},
        )
    except Exception as exc:
        logger.warning("load_all_test_files failed: %s", exc)
        return []
