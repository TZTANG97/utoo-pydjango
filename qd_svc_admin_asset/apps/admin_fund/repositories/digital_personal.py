"""数字化中心 — 非管理员个人看板。对齐 Java selUserAmountByYearsygr / syfbgr / manage_center #else。"""
from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.core.db_utils import fetch_all, fetch_one


def _helper_user_ids(user_id: str) -> list[str]:
    """对齐 Java queryUsersByHelper：本人 + helper_id=本人 的账号。"""
    ids = [str(user_id)]
    if not user_id:
        return ids
    rows = fetch_all(
        """
        SELECT id FROM sy_users
        WHERE CAST(helper_id AS CHAR) = CAST(%(uid)s AS CHAR)
        """,
        {"uid": user_id},
    )
    for r in rows:
        hid = str(r.get("id") or "")
        if hid and hid not in ids:
            ids.append(hid)
    return ids


def _utoo_type(user_id: str) -> str:
    if not user_id:
        return ""
    try:
        row = fetch_one(
            """
            SELECT utoo_type AS utooType
            FROM sy_users
            WHERE CAST(id AS CHAR) = CAST(%(uid)s AS CHAR)
            LIMIT 1
            """,
            {"uid": user_id},
        )
        return str((row or {}).get("utooType") or "").strip()
    except Exception:
        return ""


def _is_sale_manager(user_id: str) -> bool:
    """对齐 Java UserTypes.SALE_MANAGER.getName() == \"销售主管\"。"""
    return _utoo_type(user_id) == "销售主管"


def _months_for_year(year: str, user_ids: list[str], order_type: int, *, table: str) -> list[str]:
    """对齐 selAllDate：优先取统计表有数据的月份；无数据则补全当年 12 月。"""
    placeholders = ", ".join(f"%(u{i})s" for i in range(len(user_ids)))
    params: dict[str, Any] = {f"u{i}": u for i, u in enumerate(user_ids)}
    params["year"] = year
    params["ot"] = order_type
    try:
        rows = fetch_all(
            f"""
            SELECT DISTINCT `month` AS m
            FROM {table}
            WHERE type = 0
              AND CAST(user_id AS CHAR) IN ({placeholders})
              AND LEFT(`month`, 4) = %(year)s
              AND order_type = %(ot)s
            ORDER BY `month`
            """,
            params,
        )
    except Exception:
        rows = []
    months = [str(r.get("m") or "") for r in rows if r.get("m")]
    if months:
        return months
    return [f"{year}-{m:02d}" for m in range(1, 13)]


def _money(v: Any) -> float:
    try:
        return float(Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except Exception:
        return 0.0


def _sel_user_amount_by_year(
    *,
    user_id: str,
    year: str,
    order_type: int,
    kind: str,
) -> dict[str, Any]:
    """
    order_type: 1=实验 2=实验分包（statistic_user_sale_exp / _sm）
    kind: 'exp' | 'expSub' 决定返回字段后缀
    销售主管：读 statistic_user_sale_exp_sm（单用户，对齐 Java）。
    其他：读 statistic_user_sale_exp（含协助者）。
    """
    y = str(year or "").strip() or str(datetime.now().year)
    empty_months = [f"{y}-{m:02d}" for m in range(1, 13)]
    suffix = "Exp" if kind == "exp" else "ExpSub"
    empty = {
        f"userSaleAryrmb{suffix}": [0.0] * 12,
        f"userSaleAryus{suffix}": [0.0] * 12,
        "xmonths": empty_months,
        f"qnxsrmb{suffix}": 0.0,
        f"qnxsus{suffix}": 0.0,
        f"ddslrmb{suffix}": 0,
        f"ddslus{suffix}": 0,
        "year": y,
        "currentUserId": user_id,
    }
    if not user_id:
        return empty

    use_sm = _is_sale_manager(user_id)
    table = "statistic_user_sale_exp_sm" if use_sm else "statistic_user_sale_exp"
    try:
        fetch_one(f"SELECT 1 AS ok FROM {table} LIMIT 1")
    except Exception:
        return empty

    uids = [str(user_id)] if use_sm else _helper_user_ids(user_id)
    months = _months_for_year(y, uids, order_type, table=table)
    placeholders = ", ".join(f"%(u{i})s" for i in range(len(uids)))
    params: dict[str, Any] = {f"u{i}": u for i, u in enumerate(uids)}
    params["year"] = y
    params["ot"] = order_type

    try:
        rows = fetch_all(
            f"""
            SELECT
                SUM(IFNULL(sale_amount, 0)) AS sumtotal,
                SUM(IFNULL(order_count, 0)) AS sumordercount,
                account_type,
                `month` AS m
            FROM {table}
            WHERE type = 0
              AND CAST(user_id AS CHAR) IN ({placeholders})
              AND LEFT(`month`, 4) = %(year)s
              AND order_type = %(ot)s
            GROUP BY account_type, `month`
            ORDER BY `month`
            """,
            params,
        )
    except Exception:
        return empty

    rmb_map = {m: Decimal("0") for m in months}
    usd_map = {m: Decimal("0") for m in months}
    cnt_rmb = Decimal("0")
    cnt_usd = Decimal("0")
    for r in rows:
        m = str(r.get("m") or "")
        if m not in rmb_map:
            rmb_map[m] = Decimal("0")
            usd_map[m] = Decimal("0")
            months.append(m)
        try:
            at = int(r.get("account_type") or 1)
        except (TypeError, ValueError):
            at = 1
        try:
            total = Decimal(str(r.get("sumtotal") or 0))
        except Exception:
            total = Decimal("0")
        try:
            cnt = Decimal(str(r.get("sumordercount") or 0))
        except Exception:
            cnt = Decimal("0")
        if at == 2:
            usd_map[m] += total
            cnt_usd += cnt
        else:
            rmb_map[m] += total
            cnt_rmb += cnt

    months = sorted(set(months))
    rmb_ary = [_money(rmb_map.get(m, 0)) for m in months]
    usd_ary = [_money(usd_map.get(m, 0)) for m in months]
    return {
        f"userSaleAryrmb{suffix}": rmb_ary,
        f"userSaleAryus{suffix}": usd_ary,
        "xmonths": months,
        f"qnxsrmb{suffix}": _money(sum(rmb_ary)),
        f"qnxsus{suffix}": _money(sum(usd_ary)),
        f"ddslrmb{suffix}": int(cnt_rmb),
        f"ddslus{suffix}": int(cnt_usd),
        "year": y,
        "currentUserId": user_id,
    }


def sel_user_amount_by_year_sygr(*, user_id: str, year: str = "") -> dict[str, Any]:
    """个人实验总额：/digitalManage/selUserAmountByYearsygr.ajax"""
    return _sel_user_amount_by_year(user_id=user_id, year=year, order_type=1, kind="exp")


def sel_user_amount_by_year_syfbgr(*, user_id: str, year: str = "") -> dict[str, Any]:
    """个人实验分包总额：/digitalManage/selUserAmountByYearsyfbgr.ajax"""
    return _sel_user_amount_by_year(user_id=user_id, year=year, order_type=2, kind="expSub")


def _has_dept(user_id: str) -> bool:
    """对齐 Java finddeptnamebyuserID：有挂接所属公司账号则为公司基金看板。"""
    if not user_id:
        return False
    try:
        row = fetch_one(
            """
            SELECT r.id
            FROM sy_users r
            LEFT JOIN `user` users ON users.syuser_id = r.id
            WHERE CAST(r.id AS CHAR) = CAST(%(uid)s AS CHAR)
              AND users.deleteStatus = 0
            LIMIT 1
            """,
            {"uid": user_id},
        )
        return bool(row)
    except Exception:
        return False


def _pie_slice(name: str, total: float, company_id: Any = 0) -> dict[str, Any]:
    return {
        "company_name": name,
        "total": total,
        "company_id": company_id or 0,
        "name": name,
        "value": total,
    }


def _split_receive_by_currency(rows: list[dict[str, Any]]) -> tuple[list[dict], list[dict], float, float]:
    """按币种拆分应收/应付行，同公司累加。"""
    rmb: dict[Any, dict[str, Any]] = {}
    usd: dict[Any, dict[str, Any]] = {}
    sum_rmb = Decimal("0")
    sum_usd = Decimal("0")
    for r in rows:
        try:
            ct = int(r.get("currency_type") or 1)
        except (TypeError, ValueError):
            ct = 1
        try:
            amt = Decimal(str(r.get("total_amount") or 0))
        except Exception:
            amt = Decimal("0")
        if amt == 0:
            continue
        cid = r.get("company_id") or 0
        name = str(r.get("company_name") or f"公司#{cid}")
        bucket = usd if ct == 2 else rmb
        if cid not in bucket:
            bucket[cid] = {"name": name, "total": Decimal("0"), "company_id": cid}
        bucket[cid]["total"] += amt
        if ct == 2:
            sum_usd += amt
        else:
            sum_rmb += amt
    rmb_list = [_pie_slice(v["name"], _money(v["total"]), v["company_id"]) for v in rmb.values()]
    usd_list = [_pie_slice(v["name"], _money(v["total"]), v["company_id"]) for v in usd.values()]
    return rmb_list, usd_list, _money(sum_rmb), _money(sum_usd)


def _sel_receive_user(
    *,
    user_id: str,
    order_type: int,
    type_filter: int | None,
    table: str = "statistic_company_overdue_receive_utoo",
) -> list[dict[str, Any]]:
    """对齐 Java companyOverdueReceive(Sm)Service.selAllListUser。"""
    params: dict[str, Any] = {"uid": user_id, "ot": order_type}
    type_sql = ""
    if type_filter is not None:
        type_sql = " AND t.type = %(rtype)s"
        params["rtype"] = type_filter
    try:
        return fetch_all(
            f"""
            SELECT
                IFNULL(t.total_amount, 0) AS total_amount,
                IFNULL(NULLIF(TRIM(u.name), ''), CONCAT('公司#', t.company_id)) AS company_name,
                t.currency_type AS currency_type,
                t.company_id AS company_id
            FROM {table} t
            LEFT JOIN qd_user_company u ON t.company_id = u.id
            WHERE CAST(t.user_id AS CHAR) = CAST(%(uid)s AS CHAR)
              AND t.order_type = %(ot)s
              {type_sql}
            """,
            params,
        )
    except Exception:
        return []


def _sel_pay_user(
    *,
    user_id: str,
    order_type: int,
    table: str = "statistic_company_overdue_pay",
) -> list[dict[str, Any]]:
    """对齐 Java companyOverduePay(Sm)Service.selAllListByParm → selAllList。"""
    try:
        return fetch_all(
            f"""
            SELECT
                IFNULL(t.total_amount, 0) AS total_amount,
                IFNULL(NULLIF(TRIM(u.name), ''), CONCAT('公司#', t.company_id)) AS company_name,
                t.currency_type AS currency_type,
                t.company_id AS company_id
            FROM {table} t
            LEFT JOIN qd_user_company u ON t.company_id = u.id
            WHERE CAST(t.user_id AS CHAR) = CAST(%(uid)s AS CHAR)
              AND t.order_type = %(ot)s
            """,
            {"uid": user_id, "ot": order_type},
        )
    except Exception:
        return []


def sel_user_overdue_pies(*, user_id: str) -> dict[str, Any]:
    """个人应收/应付饼图数据（对齐 Java manage_center #else SSR）。

    deptType=1（公司账号）：应收 order_type 6/8 + type=2；分包应付 order_type=9。
    销售主管：应收/应付走 *_sm 表（应收 12/13，分包应付 8）。
    否则：应收 12/13；分包应付 8（非 sm 表）。
    个人实验应付款：Java 固定为 0。
    """
    empty = {
        "overdueAryrmbsy": [],
        "overdueAryussy": [],
        "overduermbsy": 0.0,
        "overdueussy": 0.0,
        "overdueAryrmbsyfb": [],
        "overdueAryussyfb": [],
        "overduermbsyfb": 0.0,
        "overdueussyfb": 0.0,
        "overdueAryrmbPaysy": [],
        "overdueAryusPaysy": [],
        "overduermbPaysy": 0.0,
        "overdueusPaysy": 0.0,
        "overdueAryrmbPaysyfb": [],
        "overdueAryusPaysyfb": [],
        "overduermbPaysyfb": 0.0,
        "overdueusPaysyfb": 0.0,
        "deptType": "0",
    }
    if not user_id:
        return empty

    is_sm = _is_sale_manager(user_id)
    # 销售主管优先走 Sm 表，避免误判为公司基金后读错 order_type
    is_dept = (not is_sm) and _has_dept(user_id)
    if is_dept:
        recv_exp = _sel_receive_user(user_id=user_id, order_type=6, type_filter=2)
        recv_sub = _sel_receive_user(user_id=user_id, order_type=8, type_filter=2)
        pay_sub = _sel_pay_user(user_id=user_id, order_type=9)
        dept_type = "1"
    elif is_sm:
        recv_exp = _sel_receive_user(
            user_id=user_id,
            order_type=12,
            type_filter=None,
            table="statistic_company_overdue_receive_utoo_sm",
        )
        recv_sub = _sel_receive_user(
            user_id=user_id,
            order_type=13,
            type_filter=None,
            table="statistic_company_overdue_receive_utoo_sm",
        )
        pay_sub = _sel_pay_user(
            user_id=user_id,
            order_type=8,
            table="statistic_company_overdue_pay_sm",
        )
        dept_type = "0"
    else:
        recv_exp = _sel_receive_user(user_id=user_id, order_type=12, type_filter=None)
        recv_sub = _sel_receive_user(user_id=user_id, order_type=13, type_filter=None)
        pay_sub = _sel_pay_user(user_id=user_id, order_type=8)
        dept_type = "0"

    rmb_sy, usd_sy, sum_rmb_sy, sum_usd_sy = _split_receive_by_currency(recv_exp)
    rmb_fb, usd_fb, sum_rmb_fb, sum_usd_fb = _split_receive_by_currency(recv_sub)
    rmb_pay_fb, usd_pay_fb, sum_rmb_pay_fb, sum_usd_pay_fb = _split_receive_by_currency(pay_sub)

    return {
        "overdueAryrmbsy": rmb_sy,
        "overdueAryussy": usd_sy,
        "overduermbsy": sum_rmb_sy,
        "overdueussy": sum_usd_sy,
        "overdueAryrmbsyfb": rmb_fb,
        "overdueAryussyfb": usd_fb,
        "overduermbsyfb": sum_rmb_fb,
        "overdueussyfb": sum_usd_fb,
        # 个人实验应付款：Java 页面写死 0
        "overdueAryrmbPaysy": [],
        "overdueAryusPaysy": [],
        "overduermbPaysy": 0.0,
        "overdueusPaysy": 0.0,
        "overdueAryrmbPaysyfb": rmb_pay_fb,
        "overdueAryusPaysyfb": usd_pay_fb,
        "overduermbPaysyfb": sum_rmb_pay_fb,
        "overdueusPaysyfb": sum_usd_pay_fb,
        "deptType": dept_type,
    }
