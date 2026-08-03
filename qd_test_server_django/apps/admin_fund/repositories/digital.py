from __future__ import annotations

from datetime import datetime
from typing import Any

from apps.core.db_utils import fetch_all, fetch_one, scalar


def overview(year: str) -> dict[str, Any]:
    """Simplified digital manage center KPIs (full Java board is much larger)."""
    company_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM company_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    user_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM user_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    loan_pay = fetch_one(
        """
        SELECT COALESCE(SUM(loan), 0) AS amount
        FROM company_loan_pay
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    project_pay = fetch_one(
        """
        SELECT COALESCE(SUM(pay_amount), 0) AS amount
        FROM project_pay_detail
        WHERE year = %(year)s
        """,
        {"year": year},
    ) or {}
    balances = fetch_all(
        """
        SELECT
            account_type AS accountType,
            COALESCE(SUM(available_balance), 0) AS availableBalance,
            COALESCE(SUM(freezing_balance), 0) AS freezingBalance
        FROM account
        GROUP BY account_type
        """
    )
    log_count = int(
        scalar(
            """
            SELECT COUNT(*) FROM account_log
            WHERE deleteStatus = 0 AND YEAR(addTime) = %(year)s
            """,
            {"year": year},
        )
        or 0
    )
    monthly = fetch_all(
        """
        SELECT month, COALESCE(SUM(pay_amount), 0) AS amount
        FROM company_pay_detail
        WHERE year = %(year)s
        GROUP BY month
        ORDER BY month
        """,
        {"year": year},
    )
    return {
        "year": year,
        "companyPayTotal": float(company_pay.get("amount") or 0),
        "userPayTotal": float(user_pay.get("amount") or 0),
        "loanPayTotal": float(loan_pay.get("amount") or 0),
        "projectPayTotal": float(project_pay.get("amount") or 0),
        "balances": balances,
        "logCount": log_count,
        "monthlyCompanyPay": monthly,
    }


def _norm_year(year: str) -> str:
    y = str(year or "").strip()
    if not y or y in ("全部", "选择年份", "all", "ALL"):
        return ""
    return y[:4]


def _all_years() -> list[str]:
    """对齐 Java DateUtil.getAllYear：自 2019 起至当前年。"""
    end = datetime.now().year
    return [str(y) for y in range(2019, end + 1)]


def _months_for_year(year: str) -> list[str]:
    """对齐 Java CommUtil.getYearAllMonthByYear：返回 yyyy-MM；当前年只到本月。"""
    y = int(year[:4])
    now = datetime.now()
    last_m = now.month if y == now.year else 12
    return [f"{y:04d}-{m:02d}" for m in range(1, last_m + 1)]


def _us_exchange_rate() -> float:
    try:
        val = scalar("SELECT us_exchange_rate FROM account_setting LIMIT 1", {})
        if val is not None:
            return float(val) or 1.0
    except Exception:
        pass
    return 1.0


def _parse_test_type(test_type: str | int | None) -> int | None:
    raw = str(test_type or "").strip()
    if not raw or raw in ("0", "全部", "null", "undefined"):
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


_STAT_COMPANY_FROM: str | None = None
_STAT_EXP_FROM: str | None = None


def _stat_company_from() -> str:
    """优先双表 UNION（对齐 Java）；若主库无旧表则仅用 _utoo。"""
    global _STAT_COMPANY_FROM
    if _STAT_COMPANY_FROM:
        return _STAT_COMPANY_FROM
    try:
        fetch_one("SELECT 1 AS ok FROM statistic_company_sale LIMIT 1")
        _STAT_COMPANY_FROM = (
            "(SELECT pt.* FROM statistic_company_sale pt "
            "UNION ALL SELECT ut.* FROM statistic_company_sale_utoo ut)"
        )
    except Exception:
        _STAT_COMPANY_FROM = "statistic_company_sale_utoo"
    return _STAT_COMPANY_FROM


def _stat_exp_from() -> str:
    global _STAT_EXP_FROM
    if _STAT_EXP_FROM:
        return _STAT_EXP_FROM
    try:
        fetch_one("SELECT 1 AS ok FROM statistic_experiment_sale LIMIT 1")
        _STAT_EXP_FROM = (
            "(SELECT pt.* FROM statistic_experiment_sale pt "
            "UNION ALL SELECT ut.* FROM statistic_experiment_sale_utoo ut)"
        )
    except Exception:
        _STAT_EXP_FROM = "statistic_experiment_sale_utoo"
    return _STAT_EXP_FROM


def sel_company_sale_by_year(year: str = "", type_code: str = "1") -> dict[str, Any]:
    """公司实验金额列表 — 对齐 Java DigitalManageCenterAction.selCompanySaleByYear。

    数据源：statistic_company_sale ∪ statistic_company_sale_utoo（下单即累计，含未审核）。
    统计表 order_type：1销售 / 2租赁 / 3实验（实验主单6+分包8 均写入 3）。
    """
    y = _norm_year(year)
    try:
        tc = int(str(type_code or "1").strip() or "1")
    except (TypeError, ValueError):
        tc = 1
    if tc not in (1, 2):
        tc = 1

    params: dict[str, Any] = {"stat_type": tc}
    year_sql = ""
    if y:
        year_sql = " AND t.year = %(stat_year)s"
        params["stat_year"] = y

    companies = fetch_all(
        """
        SELECT
            u.id AS id,
            IFNULL(NULLIF(TRIM(u.company_name), ''), CONCAT('公司#', u.id)) AS company_name
        FROM `user` u
        WHERE u.deleteStatus = 0 AND u.userType = 6
        ORDER BY u.id
        """
    )
    from_sql = _stat_company_from()
    sale_rows = fetch_all(
        f"""
        SELECT
            IFNULL(SUM(t.sale_amount), 0) AS totalAmount,
            t.account_type AS account_type,
            t.company_id AS company_id,
            t.order_type AS order_type
        FROM {from_sql} t
        WHERE t.type = %(stat_type)s
          {year_sql}
        GROUP BY t.company_id, t.account_type, t.order_type
        """,
        params,
    )

    by_company: dict[Any, list[dict[str, Any]]] = {}
    for r in sale_rows:
        cid = r.get("company_id")
        by_company.setdefault(cid, []).append(r)

    fx = _us_exchange_rate()
    company_info: list[dict[str, Any]] = []
    gssyzermb = 0.0
    gssyzerus = 0.0
    gsxszermb = 0.0
    gsxszerus = 0.0
    gszlzermb = 0.0
    gszlzerus = 0.0
    zrmb = 0.0

    for idx, u in enumerate(companies):
        cid = u.get("id")
        rmb = us = syrmb = syus = rentrmb = rentus = 0.0
        for map_row in by_company.get(cid, []):
            amt = float(map_row.get("totalAmount") or 0)
            account_type = int(map_row.get("account_type") or 1)
            order_type = int(map_row.get("order_type") or 0)
            if account_type == 1:
                zrmb += amt
                if order_type == 1:
                    rmb = amt
                    gsxszermb += amt
                elif order_type == 2:
                    rentrmb = amt
                    gszlzermb += amt
                elif order_type == 3:
                    syrmb = amt
                    gssyzermb += amt
            elif account_type == 2:
                zrmb += amt * fx
                if order_type == 1:
                    us = amt
                    gsxszerus += amt
                elif order_type == 2:
                    rentus = amt
                    gszlzerus += amt
                elif order_type == 3:
                    syus = amt
                    gssyzerus += amt

        company_info.append(
            {
                "index": idx + 1,
                "id": cid,
                "company_id": cid,
                "company_name": str(u.get("company_name") or ""),
                "rmb": round(rmb, 2),
                "us": round(us, 2),
                "rentrmb": round(rentrmb, 2),
                "rentus": round(rentus, 2),
                "syrmb": round(syrmb, 2),
                "syus": round(syus, 2),
            }
        )

    # 精简页只展示实验列：隐藏实验金额为 0 的公司（总额行仍保留），与小程序一致
    visible = [r for r in company_info if float(r.get("syrmb") or 0) > 0]
    for i, r in enumerate(visible):
        r["index"] = i + 1

    visible.append(
        {
            "index": len(visible) + 1,
            "id": 0,
            "company_id": 0,
            "company_name": f"总额: {round(zrmb, 2)}元",
            "rmb": round(gsxszermb, 2),
            "us": round(gsxszerus, 2),
            "rentrmb": round(gszlzermb, 2),
            "rentus": round(gszlzerus, 2),
            "syrmb": round(gssyzermb, 2),
            "syus": round(gssyzerus, 2),
            "isTotal": True,
        }
    )
    return {
        "companyInfo": visible,
        "total": round(gssyzermb, 2),
        "year": y,
    }


def sel_exp_sale_by_year(
    year: str = "",
    test_type: str = "",
    order_type: int | str = 6,
) -> dict[str, Any]:
    """实验/分包金额柱图 — 对齐 Java selExpSaleByYear。

    - 数据源：statistic_experiment_sale ∪ _utoo（含未审核）
    - year 空：按年轴（2019…当前）
    - year 有值：按月轴 yyyy-MM（当前年截至本月）
    - order_type：6 实验主单 / 8 实验分包
    - test_type：experiment_manage.parent_id 过滤
    """
    y = _norm_year(year)
    try:
        ot = int(order_type)
    except (TypeError, ValueError):
        ot = 6
    if ot not in (6, 8):
        ot = 6
    parent_id = _parse_test_type(test_type)

    params: dict[str, Any] = {
        "currency_type": 1,
        "stat_type": 1,
        "order_type": ot,
    }
    test_sql = ""
    if parent_id is not None:
        test_sql = " AND em.parent_id = %(parent_id)s"
        params["parent_id"] = parent_id

    from_sql = _stat_exp_from()

    if not y:
        axis = _all_years()
        rows = fetch_all(
            f"""
            SELECT IFNULL(SUM(t.sale_amount), 0) AS totalAmount, t.year AS year
            FROM {from_sql} t
            LEFT JOIN experiment_manage em ON t.exp_type_id = em.id
            WHERE t.account_type = %(currency_type)s
              AND t.type = %(stat_type)s
              AND t.order_type = %(order_type)s
              {test_sql}
            GROUP BY t.year
            ORDER BY t.year
            """,
            params,
        )
        by_key = {str(r.get("year") or ""): float(r.get("totalAmount") or 0) for r in rows}
        series = [round(by_key.get(k, 0.0), 2) for k in axis]
        return {
            "expmonth": axis,
            "expSaleAryrmb": series,
            "expqnxsrmb": round(sum(series), 2),
            "year": y,
        }

    axis = _months_for_year(y)
    params["stat_year"] = y
    rows = fetch_all(
        f"""
        SELECT IFNULL(SUM(t.sale_amount), 0) AS totalAmount, t.month AS month
        FROM {from_sql} t
        LEFT JOIN experiment_manage em ON t.exp_type_id = em.id
        WHERE t.account_type = %(currency_type)s
          AND t.type = %(stat_type)s
          AND t.order_type = %(order_type)s
          AND t.year = %(stat_year)s
          {test_sql}
        GROUP BY t.month
        ORDER BY t.month
        """,
        params,
    )
    by_key = {str(r.get("month") or ""): float(r.get("totalAmount") or 0) for r in rows}
    series = [round(by_key.get(k, 0.0), 2) for k in axis]
    # 前端展示用「N月」；同时保留 yyyy-MM 对齐 Java（Vue 直接用返回的 expmonth）
    labels = []
    for m in axis:
        try:
            labels.append(f"{int(m.split('-')[1])}月")
        except (IndexError, ValueError):
            labels.append(m)
    return {
        "expmonth": labels,
        "expSaleAryrmb": series,
        "expqnxsrmb": round(sum(series), 2),
        "year": y,
    }
