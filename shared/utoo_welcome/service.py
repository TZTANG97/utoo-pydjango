from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from shared.utoo_welcome import mid as welcome_mid

logger = logging.getLogger(__name__)

def _resolve_welcome_user_type(utoo_type: str | None) -> int:
    """对齐 Java welcome 角色分流（精确 type 名优先，兼顾 indexHtmlAjax）。

    新系统走 /vue/welcome.ajax，公司基金需与公司账号同为 userType=2（资金支出入口）。
    制单员按枚举分支为 userType=5（入口：新增商品/新增实验订单；资产图见 show_assets）。
    公共账号 / 外部合作* → 0（空白页，无图表）。
    """
    role = (utoo_type or "").strip()
    if not role:
        return 0
    upper = role.upper()

    # 0 公共 / 外部合作：尽早返回，避免被「销售」等泛匹配误伤
    if role in ("公共账号", "外部合作公司", "外部合作账号", "外部公司") or any(
        key in role for key in ("公共账号", "外部合作", "外部公司")
    ):
        return 0
    if upper in ("PUBLIC", "OUT_COOPERATE_COMPANY", "OUT_COMPANY"):
        return 0

    # 1 系统管理员
    if role == "系统管理员" or "系统管理员" in role or upper == "ADMIN" or role == "admin":
        return 1

    # 2 公司基金 / 公司账号（对齐 indexHtmlAjax：A_COMPANY_FUND || COMPANY）
    if (
        role in ("公司基金", "公司账号", "公司")
        or "公司基金" in role
        or "公司账号" in role
        or upper in ("COMPANY", "A_COMPANY_FUND")
    ):
        return 2

    # 3 销售主管 / 测试主管
    if (
        role in ("销售主管", "测试主管")
        or "销售主管" in role
        or "测试主管" in role
        or upper in ("SALE_MANAGER", "TEST_MANAGER")
    ):
        return 3

    # 5 制单员（精确分支；勿并入销售人员=4，否则入口卡与旧「制单」页不一致）
    if role == "制单员" or "制单" in role or upper == "A_ORDER_ADDER":
        return 5

    # 6 外部投资
    if role == "外部投资" or "外部投资" in role or upper == "A_OUT_INVEST":
        return 6

    # 7 仓库管理
    if role == "仓库管理" or "仓库" in role or upper == "A_STORE_MANAGER":
        return 7

    # 14 H类用户
    if "H类" in role or role.startswith("H类") or upper.startswith("H_"):
        return 14

    # 4 销售人员 / 测试人员 / C·R·原厂·内勤 等
    if role == "测试人员" or (
        "测试人员" in role and "测试主管" not in role
    ) or upper == "TEST_USER":
        return 4
    if role in (
        "销售人员",
        "原厂销售人员",
        "内勤主管",
        "A类销售人员",
        "C类销售人员",
        "R类人员",
    ):
        return 4
    if any(key in role for key in ("原厂", "内勤", "C类", "R类", "A类销售")):
        return 4
    if "销售" in role and "销售主管" not in role:
        return 4

    return 0


def _resolve_welcome_user_type2(utoo_type: str | None, user_type: int) -> int:
    """对齐 Java IndexViewController userType2（精确名称判断）。

    1=管理员交易图；3=测试人员测试数量；4=销售人员测试年/月图；5=测试主管测试数量。
    C类/原厂/R类/制单员/公司基金等 → 0（无额外业绩图，仅资产+运营/入口卡）。
    """
    role = (utoo_type or "").strip()
    upper = role.upper()
    if "测试主管" in role or upper == "TEST_MANAGER":
        return 5
    if role == "测试人员" or (
        "测试人员" in role and "测试主管" not in role
    ) or upper == "TEST_USER":
        return 3
    # Java：仅 utoo_type 精确等于「销售人员」
    if role == "销售人员" or upper in ("A_SALESPERSON",):
        return 4
    if user_type == 1:
        return 1
    return 0


def _resolve_welcome_user_type3(utoo_type: str | None) -> int:
    """对齐 Java userType3：2=显示「我的实际/实验销售额」。

    仅 type 为「销售人员」或「销售主管」；C类销售人员等为 0。
    """
    role = (utoo_type or "").strip()
    if role in ("销售人员", "销售主管"):
        return 2
    return 0


def _is_test_manager(utoo_type: str | None) -> bool:
    role = (utoo_type or "").strip()
    return "测试主管" in role or role.upper() == "TEST_MANAGER"


def _is_sale_manager_exact(utoo_type: str | None) -> bool:
    """Java：仅 utoo_type 精确为「销售主管」走 selOrderNumBySaleManager。"""
    return (utoo_type or "").strip() == "销售主管"


def previous_six_months(*, today: date | None = None) -> list[str]:
    base = today or date.today()
    year, month = base.year, base.month
    months: list[str] = [""] * 6
    for i in range(5, -1, -1):
        months[i] = f"{year:04d}-{month:02d}"
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    return months


def _months_of_year(year: int, *, today: date | None = None) -> list[str]:
    """当年截至本月（或往年 12 个月）的 yyyy-MM 列表。"""
    base = today or date.today()
    end_m = 12 if year < base.year else base.month
    return [f"{year:04d}-{m:02d}" for m in range(1, end_m + 1)]


def _money_wan(raw: Any) -> str:
    if raw is None or raw == "":
        return "0"
    try:
        v = (Decimal(str(raw)) / Decimal(10000)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return format(v, "f")
    except Exception:
        return "0"


def _fill_months(months: list[str], by_month: dict[str, Any], *, as_wan: bool) -> list[str]:
    values: list[str] = []
    for m in months:
        raw = by_month.get(m)
        if raw is None or raw == "":
            values.append("0")
            continue
        if as_wan:
            values.append(_money_wan(raw))
        else:
            try:
                values.append(str(int(Decimal(str(raw)))))
            except Exception:
                values.append("0")
    return values


def _count_audit_by_manager(
    *,
    order_type: str | int,
    manager_id: str,
    manager_field: str = "sale_manager",
    token: str | None = None,
) -> int:
    """对齐 Java getAuditOrders：order_status=20 + 主管字段（order 中台原子）。"""
    if not manager_id:
        return 0
    if manager_field not in ("sale_manager", "test_manager"):
        manager_field = "sale_manager"
    if not token:
        logger.warning("welcome audit-count empty: no token orderType=%s", order_type)
        return 0
    n = welcome_mid.fetch_audit_count(
        token,
        order_type=order_type,
        manager_id=manager_id,
        manager_field=manager_field,
        order_status=20,
    )
    if n is None:
        logger.warning(
            "welcome audit-count mid miss → 0 orderType=%s manager=%s",
            order_type,
            manager_id,
        )
        return 0
    return n


def _count_pay_audit(
    *,
    manager_id: str,
    order_type: str | int = 9,
    token: str | None = None,
) -> int:
    """对齐 Java getAuditPayOrders：pay_status=32（order 中台原子）。"""
    if not manager_id:
        return 0
    if not token:
        logger.warning("welcome pay-audit-count empty: no token")
        return 0
    n = welcome_mid.fetch_audit_count(
        token,
        order_type=order_type,
        manager_id=manager_id,
        pay_status=32,
    )
    if n is None:
        logger.warning("welcome pay-audit-count mid miss → 0 manager=%s", manager_id)
        return 0
    return n


def _pending_for_manager(
    *,
    user_id: str,
    is_test_manager: bool,
    token: str | None = None,
) -> dict[str, Any]:
    """对齐 Java welcome.html userType=3 五张待审卡。

    1/2/3/5：sale_manager；4：测试主管用 test_manager，销售主管用 sale_manager。
    """
    type9_field = "test_manager" if is_test_manager else "sale_manager"
    return {
        "expOrder": _count_audit_by_manager(
            order_type=6, manager_id=user_id, token=token
        ),
        "selfChildOrder": _count_audit_by_manager(
            order_type=10, manager_id=user_id, token=token
        ),
        "subcontractOrder": _count_audit_by_manager(
            order_type=8, manager_id=user_id, token=token
        ),
        "subcontractSubOrder": _count_audit_by_manager(
            order_type=9,
            manager_id=user_id,
            manager_field=type9_field,
            token=token,
        ),
        # 字段名兼容前端：实际为「待审核付款实验分包子订单」
        "materialSubOrder": _count_pay_audit(
            manager_id=user_id, order_type=9, token=token
        ),
    }


def _count_timeout_ops(
    *,
    user_id: str,
    order_status: int | None = None,
    is_timeout: int | None = None,
    by_sale_manager: bool = False,
    token: str | None = None,
) -> int:
    """对齐 Java selOrderNum / selOrderNumBySaleManager（order 中台原子）。"""
    if not user_id:
        return 0
    if not token:
        logger.warning("welcome timeout-count empty: no token")
        return 0
    n = welcome_mid.fetch_timeout_count(
        token,
        user_id=user_id,
        order_status=order_status,
        is_timeout=is_timeout,
        scope="sale_manager" if by_sale_manager else "staff",
    )
    if n is None:
        logger.warning("welcome timeout-count mid miss → 0 user=%s", user_id)
        return 0
    return n


def _ops_counts(
    *,
    user_id: str,
    user_type: int,
    user_type2: int,
    utoo_type: str = "",
    token: str | None = None,
) -> dict[str, int]:
    """运营 KPI（对齐 Java welcome.htm / IndexViewController）。

    文案统一：未开始测试订单 / 进行中测试订单 / 测试超时订单。
    - 销售主管：statistic_experiment_timeout + audit_manager_id
    - 测试人员及其他：同表 selOrderNum（test/sale/audit/lab_manager 命中本人）
    注意：Java 测试人员第三卡也是「测试超时」，不是「测试通过/已完成」。
    """
    del user_type, user_type2  # 欢迎页运营卡不区分 finish 通过态
    by_sm = _is_sale_manager_exact(utoo_type)
    return {
        "notStarted": _count_timeout_ops(
            user_id=user_id,
            order_status=0,
            by_sale_manager=by_sm,
            token=token,
        ),
        "inProgress": _count_timeout_ops(
            user_id=user_id,
            order_status=1,
            by_sale_manager=by_sm,
            token=token,
        ),
        "passed": 0,
        "timeout": _count_timeout_ops(
            user_id=user_id,
            is_timeout=1,
            by_sale_manager=by_sm,
            token=token,
        ),
        "opsMode": "manager",
    }


def _test_qty_year_chart(
    *,
    year: int,
    sale_user_id: str = "",
    token: str | None = None,
) -> dict[str, Any]:
    """测试数量(年)：按月完成量。销售人员限定其主单关联。"""
    months = _months_of_year(year)
    empty = {
        "year": str(year),
        "months": months,
        "values": [0] * len(months),
        "saleUserId": str(sale_user_id or ""),
    }
    if not token:
        logger.warning("welcome finish-count-by-month empty: no token")
        return empty
    items = welcome_mid.fetch_finish_count_by_month(
        token, year=year, sale_user_id=sale_user_id
    )
    if items is None:
        logger.warning("welcome finish-count-by-month mid miss → empty year=%s", year)
        return empty
    by_m = {str(r.get("month") or ""): int(r.get("count") or 0) for r in items}
    return {
        "year": str(year),
        "months": months,
        "values": [by_m.get(m, 0) for m in months],
        "saleUserId": str(sale_user_id or ""),
    }


def _tester_qty_month_chart(
    *,
    year: int,
    month: int,
    sale_user_id: str = "",
    token: str | None = None,
) -> dict[str, Any]:
    """测试人员测试数量(月)：当月各测试员完成量。"""
    ym = f"{year:04d}-{month:02d}"
    empty = {
        "month": ym,
        "names": [],
        "values": [],
        "userIds": [],
        "saleUserId": str(sale_user_id or ""),
    }
    if not token:
        logger.warning("welcome finish-count-by-tester empty: no token")
        return empty
    items = welcome_mid.fetch_finish_count_by_tester(
        token, year_month=ym, sale_user_id=sale_user_id, limit=30
    )
    if items is None:
        logger.warning("welcome finish-count-by-tester mid miss → empty ym=%s", ym)
        return empty
    return {
        "month": ym,
        "names": [str(r.get("name") or "") for r in items],
        "values": [int(r.get("count") or 0) for r in items],
        "userIds": [str(r.get("userId") or "") for r in items],
        "saleUserId": str(sale_user_id or ""),
    }


def _chart_admin_trade(months: list[str], *, token: str | None = None) -> list[str]:
    if not months:
        return []
    if not token:
        logger.warning("welcome trade-by-month empty: no token")
        return ["0"] * len(months)
    items = welcome_mid.fetch_trade_by_month(token, months)
    if items is None:
        logger.warning("welcome trade-by-month mid miss → zeros")
        return ["0"] * len(months)
    by_month = {str(r.get("month") or ""): r.get("amount") for r in items}
    return _fill_months(months, by_month, as_wan=True)


def _chart_user_test_count(
    months: list[str],
    user_id: str,
    *,
    year: int,
    token: str | None = None,
) -> list[str]:
    """对齐 Java statisticTestNumMonthService.selListGroupByMonth（order 中台原子）。"""
    if not months or not user_id:
        return ["0"] * len(months)
    if not token:
        logger.warning("welcome test-count-by-month empty: no token")
        return ["0"] * len(months)
    items = welcome_mid.fetch_test_count_by_month(token, user_id=user_id, year=year)
    if items is None:
        logger.warning(
            "welcome test-count-by-month mid miss → zeros user=%s year=%s",
            user_id,
            year,
        )
        return ["0"] * len(months)
    by_month: dict[str, Any] = {}
    for r in items:
        ym = str(r.get("month") or "")
        if ym:
            by_month[ym] = r.get("count")
    return _fill_months(months, by_month, as_wan=False)


def _resolve_helper_user_ids(user_id: str, *, token: str | None = None) -> list[str]:
    """本人 + helper 展开：优先 identity 原子 HTTP；失败仅本人 + warning（禁直 SQL）。"""
    uid = str(user_id or "").strip()
    if not uid:
        return []
    if token:
        mid_ids = welcome_mid.fetch_helper_user_ids(token, uid)
        if mid_ids is not None:
            return mid_ids
        logger.warning("welcome helper-ids mid miss → self-only user=%s", uid)
    else:
        logger.warning("welcome helper-ids skipped: no token user=%s", uid)
    return [uid]


def _us_exchange_rate(*, token: str | None = None) -> Decimal:
    """asset 原子汇率；失败默认 1 + warning（禁直 SQL）。"""
    if token:
        raw = welcome_mid.fetch_us_exchange_rate(token)
        if raw is not None:
            try:
                val = Decimal(str(raw))
                if val > 0:
                    return val
            except Exception:
                pass
            logger.warning("welcome us-exchange-rate mid bad value %r → 1", raw)
        else:
            logger.warning("welcome us-exchange-rate mid miss → 1")
    else:
        logger.warning("welcome us-exchange-rate empty: no token → 1")
    return Decimal("1")


def _company_supplier_ids(user_id: str, *, token: str | None = None) -> list[str]:
    """公司账户对应 `user`.id（作 experiment_order.supplier_name）；asset 原子。

    失败→空列表 + warning（保守：按无公司账户走 sale_user 口径）。
    """
    uid = str(user_id or "").strip()
    if not uid:
        return []
    if token:
        ids = welcome_mid.fetch_company_user_ids(token, uid)
        if ids is not None:
            return ids
        logger.warning("welcome company-user-ids mid miss → [] user=%s", uid)
    else:
        logger.warning("welcome company-user-ids empty: no token user=%s", uid)
    return []


def _user_has_company_account(user_id: str, *, token: str | None = None) -> bool:
    return bool(_company_supplier_ids(user_id, token=token))


def _subcontract_gross_profit(
    *,
    user_id: str,
    year: int | None = None,
    sale_user_ids: list[str] | None = None,
    token: str | None = None,
) -> tuple[str, str]:
    """对齐 Java welcome：毛利 = 分包主单总额 − 子单总额（美元按汇率折 RMB）。

    按币种 SUM → order 原子；汇率与毛利算式留在 welcome。失败→空数据+warning。
    """
    empty = ("0.00", "0.00")
    if not user_id:
        return empty
    fx = _us_exchange_rate(token=token)

    company_ids = _company_supplier_ids(user_id, token=token)
    if company_ids:
        scope = "supplier"
        ids = company_ids
    else:
        scope = "sale_user"
        ids = [
            str(x).strip()
            for x in (sale_user_ids or [user_id])
            if str(x or "").strip()
        ]
        if not ids:
            ids = [str(user_id)]

    if not ids:
        return empty
    if not token:
        logger.warning("welcome subcontract-sum empty: no token user=%s", user_id)
        return empty

    data = welcome_mid.fetch_subcontract_sum_by_currency(
        token,
        user_ids=ids,
        scope=scope,
        year=year,
        exchange_rate=fx,
    )
    if data is None:
        logger.warning(
            "welcome subcontract-sum mid miss → empty user=%s year=%s",
            user_id,
            year,
        )
        return empty

    parent_rows = data.get("parent") if isinstance(data.get("parent"), list) else []
    child_rows = data.get("child") if isinstance(data.get("child"), list) else []

    def to_rmb(rows: list[dict[str, Any]]) -> Decimal:
        total = Decimal("0")
        for r in rows:
            try:
                amt = Decimal(str(r.get("amount") or r.get("amt") or 0))
            except Exception:
                amt = Decimal("0")
            try:
                ct = int(r.get("currencyType") or r.get("ct") or 1)
            except Exception:
                ct = 1
            if ct == 2:
                total += (amt * fx).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                total += amt
        return total

    parent_rmb = to_rmb(parent_rows)
    child_rmb = to_rmb(child_rows)
    profit = parent_rmb - child_rmb
    rate = Decimal("0")
    if profit != 0 and parent_rmb != 0:
        rate = (profit / parent_rmb * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    return (
        format(profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        format(rate, "f"),
    )


def _user_sale_by_year(
    *,
    user_id: str,
    year: int,
    order_type_filter: str = "",
    token: str | None = None,
    utoo_type: str = "",
) -> dict[str, Any]:
    """对齐 Java selUserSaleByYear：销售额序列 + 分包按币种 SUM 走 order 原子；毛利算式在本函数。

    order_type_filter: ''=全部(1+2)，'1'=实验，'2'=实验分包（统计表 order_type）。
    """
    months = _months_of_year(year)
    empty = {
        "year": str(year),
        "xmonths": months,
        "userSaleAryrmb": ["0"] * len(months),
        "userSaleAryus": ["0"] * len(months),
        "qnxsrmb": "0.00",
        "qnxsus": "0.00",
        "ddslrmb": 0,
        "ddslus": 0,
        "grmlzhbigdecimal": "0.00",
        "grmlllbigdecimal": "0.00",
    }
    if not user_id or not months:
        return empty

    role = (utoo_type or "").strip()
    use_sm = _is_sale_manager_exact(role)
    # helper 展开走 identity 原子；销售主管不加 helper
    uids = [str(user_id)] if use_sm else _resolve_helper_user_ids(user_id, token=token)
    source = "sm" if use_sm else "exp"

    items: list[dict[str, Any]] | None = None
    if token:
        items = welcome_mid.fetch_user_sale_by_month(
            token,
            user_ids=uids,
            year=year,
            source=source,
            order_type_filter=order_type_filter,
        )
    else:
        logger.warning("welcome user-sale-by-month empty: no token")

    if items is None:
        logger.warning(
            "welcome user-sale-by-month mid miss → empty series user=%s year=%s",
            user_id,
            year,
        )
        grml, grml_rate = _subcontract_gross_profit(
            user_id=user_id, year=year, sale_user_ids=uids, token=token
        )
        empty["grmlzhbigdecimal"] = grml
        empty["grmlllbigdecimal"] = grml_rate
        return empty

    rmb_by: dict[str, Decimal] = {m: Decimal("0") for m in months}
    usd_by: dict[str, Decimal] = {m: Decimal("0") for m in months}
    cnt_rmb = 0
    cnt_usd = 0
    for r in items:
        m = str(r.get("month") or "")
        if m not in rmb_by:
            rmb_by[m] = Decimal("0")
            usd_by[m] = Decimal("0")
            months.append(m)
        try:
            at = int(r.get("accountType") or r.get("account_type") or 1)
        except Exception:
            at = 1
        try:
            price = Decimal(str(r.get("amount") or 0))
        except Exception:
            price = Decimal("0")
        try:
            cnt = int(r.get("orderCount") or 0)
        except Exception:
            cnt = 0
        if at == 2:
            usd_by[m] = usd_by.get(m, Decimal("0")) + price
            cnt_usd += cnt
        else:
            rmb_by[m] = rmb_by.get(m, Decimal("0")) + price
            cnt_rmb += cnt

    months = sorted(set(months))

    def series(src: dict[str, Decimal]) -> list[str]:
        out: list[str] = []
        for m in months:
            v = src.get(m, Decimal("0"))
            out.append(format(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"))
        return out

    rmb_s = series(rmb_by)
    usd_s = series(usd_by)
    sum_rmb = sum((Decimal(x) for x in rmb_s), Decimal("0"))
    sum_usd = sum((Decimal(x) for x in usd_s), Decimal("0"))
    grml, grml_rate = _subcontract_gross_profit(
        user_id=user_id, year=year, sale_user_ids=uids, token=token
    )
    return {
        "year": str(year),
        "xmonths": months,
        "userSaleAryrmb": rmb_s,
        "userSaleAryus": usd_s,
        "qnxsrmb": format(sum_rmb.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "qnxsus": format(sum_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
        "ddslrmb": cnt_rmb,
        "ddslus": cnt_usd,
        "grmlzhbigdecimal": grml,
        "grmlllbigdecimal": grml_rate,
    }


def _balances_from_rows(rows: list[dict[str, Any]]) -> tuple[str, str]:
    rmb, usd = "0.00", "0.00"
    for row in rows or []:
        try:
            at = int(row.get("accountType") or row.get("account_type") or 0)
        except Exception:
            continue
        bal = row.get("availableBalance")
        if bal is None:
            bal = row.get("available_balance")
        try:
            text = format(Decimal(str(bal or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")
        except Exception:
            text = "0.00"
        if at == 1:
            rmb = text
        elif at == 2:
            usd = text
    return rmb, usd


def _user_available_balances(user_id: str, *, token: str | None = None) -> tuple[str, str]:
    """仅 asset mid；失败 → 0.00 + warning（禁 SQL 回退）。"""
    if not user_id:
        return "0.00", "0.00"
    if not token:
        logger.warning("welcome asset-accounts empty: no token user=%s", user_id)
        return "0.00", "0.00"
    mid_rows = welcome_mid.fetch_asset_accounts(token, user_id)
    if mid_rows is None:
        logger.warning("welcome asset-accounts mid miss → 0.00 user=%s", user_id)
        return "0.00", "0.00"
    return _balances_from_rows(mid_rows)


def _menu_count_for_user(user: dict[str, Any], *, token: str | None = None) -> int:
    """仅 identity role menu-ids；失败 → 0 + warning（禁 SQL 回退）。"""
    if not token:
        logger.warning("welcome menu-count empty: no token")
        return 0
    raw = user.get("role_ids") or user.get("roleIds") or []
    if isinstance(raw, str):
        raw = [x for x in raw.split(",") if x.strip()]
    role_ids = [str(x).strip() for x in (raw or []) if str(x).strip() and str(x).strip() != "0"]
    if not role_ids:
        logger.warning(
            "welcome menu-count empty: no role_ids user=%s",
            user.get("user_id"),
        )
        return 0
    return len(welcome_mid.collect_role_menu_ids(token, role_ids))


def _enrich_welcome_user(user: dict[str, Any], *, token: str | None = None) -> dict[str, Any]:
    """优先 identity 原子读；失败保留 JWT/入参字段 + warning（禁 sy_users SQL）。"""
    out = {**user}
    uid = str(user.get("user_id") or "").strip()
    if not token or not uid:
        if uid:
            logger.warning("welcome identity-user skip: no token user=%s", uid)
        return out
    data = welcome_mid.fetch_identity_user(token, uid)
    if not data:
        logger.warning("welcome identity-user mid miss → keep JWT fields user=%s", uid)
        return out
    out.update(
        {
            "true_name": data.get("true_name") or out.get("true_name"),
            "type": data.get("type") if data.get("type") is not None else out.get("type"),
            "utoo_type": data.get("utoo_type") or out.get("utoo_type") or out.get("type"),
            "email": data.get("email") or out.get("email"),
            "mobile_phone_number": data.get("mobile_phone_number")
            or out.get("mobile_phone_number"),
            "dept_id": str(data.get("dept_id") or out.get("dept_id") or ""),
            "dept_name": data.get("dept_name") or out.get("dept_name") or "",
            "user_id": str(data.get("id") or uid),
            "user_name": data.get("user_name") or out.get("user_name"),
        }
    )
    return out


def list_recent_sys_logs(
    limit: int = 10,
    *,
    token: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]]:
    """welcome newlogs：调 order 原子 recent；失败→空列表+日志（禁 SQL 回退）。"""
    if not token:
        logger.warning("welcome syslog-recent empty: no token")
        return []
    items = welcome_mid.fetch_recent_sys_logs(
        token, limit=limit, since=since, until=until
    )
    if items is None:
        logger.warning("welcome syslog-recent mid miss → []")
        return []
    return items


def list_sys_logs_page(
    *,
    offset: int,
    limit: int,
    keyword: str = "",
    add_time: str = "",
    token: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """管理端日志分页：调 order 原子 page；失败→空页+日志（禁 SQL 回退）。"""
    if not token:
        logger.warning("welcome syslog-page empty: no token")
        return [], 0
    data = welcome_mid.fetch_sys_logs_page(
        token,
        offset=int(offset),
        limit=int(limit),
        keyword=keyword or "",
        since=(add_time or "").strip() or None,
    )
    if data is None:
        logger.warning("welcome syslog-page mid miss → empty page")
        return [], 0
    items = data.get("items")
    rows = items if isinstance(items, list) else []
    try:
        total = int(data.get("total") or 0)
    except (TypeError, ValueError):
        total = 0
    return rows, total


def build_welcome_payload(
    user: dict[str, Any],
    *,
    token: str | None = None,
    chart_year: int | None = None,
    order_type_filter: str = "",
) -> dict[str, Any]:
    user = _enrich_welcome_user(user, token=token)
    user_id = str(user.get("user_id") or "")
    login_name = str(user.get("user_name") or "")
    utoo_type = user.get("utoo_type") or user.get("type")
    role_text = str(utoo_type) if utoo_type else ""
    user_type = _resolve_welcome_user_type(role_text)
    user_type2 = _resolve_welcome_user_type2(role_text, user_type)
    user_type3 = _resolve_welcome_user_type3(role_text)
    is_test_mgr = _is_test_manager(role_text)
    dept_name = (user.get("dept_name") or "").strip()

    today = date.today()
    year = today.year
    six_months = previous_six_months(today=today)
    try:
        cy = int(chart_year) if chart_year else year
    except (TypeError, ValueError):
        cy = year
    if cy < 2000 or cy > year + 1:
        cy = year
    ot_filter = str(order_type_filter or "").strip()
    if ot_filter not in ("", "1", "2"):
        ot_filter = ""

    # 管理员近 6 月交易
    ydata: list[str] = []
    if user_type2 == 1:
        ydata = _chart_admin_trade(six_months, token=token)

    # 个人销售额：Java userType3==2（销售主管 / 销售人员；C类无此图）
    sale = (
        _user_sale_by_year(
            user_id=user_id,
            year=cy,
            order_type_filter=ot_filter,
            token=token,
            utoo_type=role_text,
        )
        if user_type3 == 2
        else {
            "year": str(cy),
            "xmonths": [],
            "userSaleAryrmb": [],
            "userSaleAryus": [],
            "qnxsrmb": "0.00",
            "qnxsus": "0.00",
            "ddslrmb": 0,
            "ddslus": 0,
            "grmlzhbigdecimal": "0.00",
            "grmlllbigdecimal": "0.00",
        }
    )

    # 测试人员(ut2=3) / 测试主管(ut2=5)：我的测试数量
    show_test_chart = user_type2 in (3, 5)
    test_months = _months_of_year(cy, today=today) if show_test_chart else []
    test_ydata = (
        _chart_user_test_count(test_months, user_id, year=cy, token=token)
        if show_test_chart
        else []
    )

    account_rmb, account_us = _user_available_balances(user_id, token=token)
    # 资产饼图：公司基金/主管/销售/制单员/投资/仓库/H类；
    # userType=0（公共账号/外部合作）空白页，不得展示图表（旧 show_assets 含 0 是错误）。
    # 制单员=5：Java 模板因 compareRole 常落成 4 才有资产图，精确分支 5 时需显式开启。
    show_assets = user_type in (2, 3, 4, 5, 6, 7, 14)
    show_logs = user_type == 1

    pending = (
        _pending_for_manager(
            user_id=user_id, is_test_manager=is_test_mgr, token=token
        )
        if user_type == 3
        else {
            "expOrder": 0,
            "selfChildOrder": 0,
            "subcontractOrder": 0,
            "subcontractSubOrder": 0,
            "materialSubOrder": 0,
        }
    )
    # Java：userType 3/4/5/6/7 均展示未开始/进行中/超时
    show_ops = user_type in (3, 4, 5, 6, 7) or user_type2 in (3, 5)
    ops = (
        _ops_counts(
            user_id=user_id,
            user_type=user_type,
            user_type2=user_type2,
            utoo_type=role_text,
            token=token,
        )
        if show_ops
        else {
            "notStarted": 0,
            "inProgress": 0,
            "passed": 0,
            "timeout": 0,
            "opsMode": "",
        }
    )

    # Java userType2==4（销售人员）：测试数量(年) + 测试人员测试数量(月)
    is_a_salesperson = user_type2 == 4
    test_year_chart: dict[str, Any] = {"year": str(year), "months": [], "values": []}
    tester_month_chart: dict[str, Any] = {"month": "", "names": [], "values": []}
    if is_a_salesperson:
        test_year_chart = _test_qty_year_chart(
            year=year, sale_user_id=user_id, token=token
        )
        tester_month_chart = _tester_qty_month_chart(
            year=year, month=today.month, sale_user_id=user_id, token=token
        )

    return {
        "userName": user.get("true_name") or user.get("user_name") or "",
        "loginName": login_name,
        "currentUser": login_name,
        "currentUserId": user_id,
        "userType": user_type,
        "userType2": user_type2,
        "userType3": user_type3,
        "roleName": role_text,
        "deptName": dept_name or "",
        "email": user.get("email") or "",
        "mobilePhoneNumber": user.get("mobile_phone_number") or "",
        "menuCount": _menu_count_for_user(user, token=token),
        # admin trade (6 months)
        "xdate": six_months if user_type2 == 1 else [],
        "ydata": ydata,
        # dual-currency personal sale
        "saleYear": sale.get("year"),
        "xmonths": sale.get("xmonths") or [],
        "userSaleAryrmb": sale.get("userSaleAryrmb") or [],
        "userSaleAryus": sale.get("userSaleAryus") or [],
        "qnxsrmb": sale.get("qnxsrmb"),
        "qnxsus": sale.get("qnxsus"),
        "ddslrmb": sale.get("ddslrmb"),
        "ddslus": sale.get("ddslus"),
        "grmlzhbigdecimal": sale.get("grmlzhbigdecimal"),
        "grmlllbigdecimal": sale.get("grmlllbigdecimal"),
        # 测试人员 / 测试主管：本人测试数量
        "expmonth": test_months if show_test_chart else [],
        "expTestAry": test_ydata,
        "testChartYear": str(cy) if show_test_chart else "",
        # 销售人员：测试数量年/月两图
        "showSaleTestCharts": is_a_salesperson,
        "testYearChart": test_year_chart,
        "testerMonthChart": tester_month_chart,
        # assets
        "showAssets": show_assets,
        "accountRMB": account_rmb,
        "accountUS": account_us,
        # KPIs
        "pendingCounts": pending,
        "opsCounts": ops,
        "showOpsCounts": show_ops,
        "newlogs": list_recent_sys_logs(10, token=token) if show_logs else [],
    }
