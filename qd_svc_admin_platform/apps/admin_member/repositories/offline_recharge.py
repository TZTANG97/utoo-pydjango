from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from apps.admin_member.helpers import page_clause
from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from apps.payments.repositories import user_account as ua_repo


def list_recharges(
    *,
    user_id: str = "",
    recharge_num: str = "",
    start_time: str = "",
    end_time: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE t.deleteStatus = 0"
    params: dict[str, Any] = {}
    if user_id:
        where += " AND t.user_id = %(user_id)s"
        params["user_id"] = user_id
    if recharge_num:
        where += " AND t.recharge_num LIKE %(recharge_num)s"
        params["recharge_num"] = f"%{recharge_num}%"
    if start_time:
        where += " AND t.addTime >= %(start_time)s"
        params["start_time"] = start_time
    if end_time:
        where += " AND t.addTime <= %(end_time)s"
        params["end_time"] = end_time
    total = int(scalar(f"SELECT COUNT(*) FROM exp_offline_recharge t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.user_id AS userId, t.recharge_num AS rechargeNum,
            t.money, t.status, t.mark, t.recharge_type AS rechargeType,
            t.is_invoice AS isInvoice, t.add_user_id AS addUserId,
            u.trueName, u.mobile, u.userName,
            su.user_name AS czry,
            IFNULL(kp.kpje, 0) AS kpje
        FROM exp_offline_recharge t
        LEFT JOIN exp_user u ON t.user_id = u.id
        LEFT JOIN sy_users su ON t.add_user_id = su.id
        LEFT JOIN (
            SELECT SUM(b.money) AS kpje, b.off_recharge_id
            FROM qd_bill b
            WHERE b.type = 1 AND b.off_recharge_id IS NOT NULL
            GROUP BY b.off_recharge_id
        ) kp ON t.id = kp.off_recharge_id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows, total


def get_recharge(recharge_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.addTime, t.user_id AS userId, t.recharge_num AS rechargeNum,
            t.money, t.status, t.mark, t.recharge_type AS rechargeType,
            t.is_invoice AS isInvoice, t.add_user_id AS addUserId,
            u.trueName, u.mobile, u.userName,
            su.user_name AS czry
        FROM exp_offline_recharge t
        LEFT JOIN exp_user u ON t.user_id = u.id
        LEFT JOIN sy_users su ON t.add_user_id = su.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": recharge_id},
    )


def _next_recharge_num() -> str:
    prefix = "XTXXCZDH" + datetime.now().strftime("%Y%m%d")
    row = fetch_one(
        """
        SELECT recharge_num FROM exp_offline_recharge
        WHERE recharge_num LIKE %(prefix)s
        ORDER BY id DESC
        LIMIT 1
        """,
        {"prefix": f"{prefix}%"},
    )
    seq = 1
    if row and row.get("recharge_num"):
        try:
            seq = int(str(row["recharge_num"])[-5:]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:05d}"


def _next_pay_num() -> str:
    prefix = "CZ" + datetime.now().strftime("%Y%m")
    row = fetch_one(
        """
        SELECT pa_num FROM pay_info_log
        WHERE pa_num LIKE %(prefix)s
        ORDER BY id DESC
        LIMIT 1
        """,
        {"prefix": f"{prefix}%"},
    )
    seq = 1
    if row and row.get("pa_num"):
        try:
            seq = int(str(row["pa_num"])[-5:]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:05d}"


def create_recharge(
    *,
    user_id: int,
    money: Decimal,
    mark: str,
    recharge_type: int,
    add_user_id: str,
) -> int:
    recharge_num = _next_recharge_num()
    rid = execute_insert(
        """
        INSERT INTO exp_offline_recharge
            (addTime, deleteStatus, user_id, recharge_num, money, status,
             add_user_id, is_invoice, mark, recharge_type)
        VALUES
            (NOW(), 0, %(user_id)s, %(recharge_num)s, %(money)s, 1,
             %(add_user_id)s, 1, %(mark)s, %(recharge_type)s)
        """,
        {
            "user_id": user_id,
            "recharge_num": recharge_num,
            "money": float(money),
            "add_user_id": add_user_id,
            "mark": mark,
            "recharge_type": recharge_type,
        },
    )
    execute_insert(
        """
        INSERT INTO exp_offline_recharge_log
            (addTime, deleteStatus, log_info, log_user_id, recharge_id)
        VALUES (NOW(), 0, '确认充值', %(log_user_id)s, %(recharge_id)s)
        """,
        {"log_user_id": add_user_id, "recharge_id": rid},
    )
    ua_repo.get_or_create(user_id)
    pay_way = 5 if recharge_type == 0 else 7
    plog_id = execute_insert(
        """
        INSERT INTO pay_info_log
            (addTime, deleteStatus, user_id, money, status, pay_type, pay_way, pa_id, pa_num)
        VALUES
            (NOW(), 0, %(user_id)s, %(money)s, 2, 1, %(pay_way)s, %(pa_id)s, %(pa_num)s)
        """,
        {
            "user_id": user_id,
            "money": float(money),
            "pay_way": pay_way,
            "pa_id": rid,
            "pa_num": _next_pay_num(),
        },
    )
    ua_repo.add_recharge_credit(user_id, money)
    ua_repo.insert_account_log(user_id, money, of_id=plog_id)
    return rid
