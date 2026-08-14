"""
对齐 Java SaleOrderSplitMoneyServiceImpl + AccountService.querySaleReceivable。

v1 覆盖：
- order_type=6 实验订单（成本固定额 + 毛利%）
- order_type=8 实验分包订单（收款 − 采购成本 → 利润%）

触发：
- 录入收款 qd_bill(type=2) 且 cost_settle=1 → try_split_on_receive
- 成本结清 cost_settle_sure → try_split_on_settle
"""
from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from django.db import transaction

logger = logging.getLogger(__name__)

D0 = Decimal("0")
D100 = Decimal("100")
TWOPLACES = Decimal("0.01")


def _d(v: Any) -> Decimal:
    try:
        return Decimal(str(v or 0))
    except Exception:
        return D0


def _q2(v: Decimal) -> Decimal:
    return v.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_pairs(scale: str | None) -> list[tuple[str, Decimal]]:
    """解析 userId_value,userId_value。"""
    text = (scale or "").strip()
    if not text:
        return []
    out: list[tuple[str, Decimal]] = []
    for part in text.split(","):
        part = part.strip()
        if not part or "_" not in part:
            continue
        uid, raw = part.split("_", 1)
        uid = uid.strip()
        if not uid:
            continue
        out.append((uid, _d(raw.strip().replace("%", ""))))
    return out


def _us_rate() -> Decimal:
    try:
        val = scalar("SELECT us_exchange_rate FROM account_setting LIMIT 1", {}, None)
        rate = _d(val)
        return rate if rate > 0 else Decimal("1")
    except Exception:
        return Decimal("1")


def _rmb_rate() -> Decimal:
    try:
        val = scalar("SELECT rmb_rate FROM account_setting LIMIT 1", {}, None)
        return _d(val) if val is not None else D0
    except Exception:
        return D0


def _ensure_account(user_id: str, account_type: int) -> dict[str, Any]:
    row = fetch_one(
        """
        SELECT id, available_balance AS availableBalance
        FROM account
        WHERE user_id = %(uid)s AND account_type = %(atype)s
        LIMIT 1
        """,
        {"uid": user_id, "atype": account_type},
    )
    if row:
        return row
    aid = execute_insert(
        """
        INSERT INTO account
            (addTime, deleteStatus, account_type, user_id,
             available_balance, freezing_balance, income_total)
        VALUES (NOW(), 0, %(atype)s, %(uid)s, 0, 0, 0)
        """,
        {"atype": account_type, "uid": user_id},
    )
    return {"id": aid, "availableBalance": 0}


def credit_sale_receivable(
    *,
    user_id: str,
    currency_type: int,
    amount: Decimal,
    order_pk: int,
    order_no: str,
    order_type: str,
    log_name: str,
) -> None:
    """对齐 AccountServiceImpl.querySaleReceivable。"""
    if amount == 0:
        return
    atype = int(currency_type or 1)
    acc = _ensure_account(str(user_id), atype)
    available = _d(acc.get("availableBalance"))
    after = _q2(available + amount)
    execute(
        "UPDATE account SET available_balance = %(av)s WHERE id = %(id)s",
        {"av": float(after), "id": acc["id"]},
    )
    # 6/8 → acc_type=13；其它销售默认 8
    acc_type = 13 if str(order_type) in ("6", "8") else 8
    execute_insert(
        """
        INSERT INTO account_log
            (addTime, deleteStatus, deal_time, acc_type, log_amount, after_log_amount,
             log_status, order_id, cz_num, year_reat, account_id, log_name, order_type)
        VALUES
            (NOW(), 0, NOW(), %(acc_type)s, %(amt)s, %(after)s,
             1, %(oid)s, %(cz)s, %(yrate)s, %(aid)s, %(lname)s, 4)
        """,
        {
            "acc_type": acc_type,
            "amt": float(amount),
            "after": float(after),
            "oid": order_pk,
            "cz": str(order_no or order_pk),
            "yrate": float(_rmb_rate()),
            "aid": acc["id"],
            "lname": log_name,
        },
    )
    try:
        execute_insert(
            """
            INSERT INTO account_interest_log
                (addTime, deleteStatus, acc_type, log_amount, after_log_amount,
                 deal_amount, account_id, log_status)
            VALUES
                (NOW(), 0, %(acc_type)s, %(amt)s, %(after)s,
                 %(amt)s, %(aid)s, 1)
            """,
            {
                "acc_type": acc_type,
                "amt": float(amount),
                "after": float(after),
                "aid": acc["id"],
            },
        )
    except Exception:
        # 计息表缺失时不影响主分钱
        pass


def _distribute_percent(
    base: Decimal,
    scale_info: str | None,
    *,
    order: dict[str, Any],
    log_name: str,
) -> None:
    pairs = _parse_pairs(scale_info)
    if not pairs or base == 0:
        return
    currency = int(order.get("currencyType") or order.get("currency_type") or 1)
    ot = str(order.get("orderType") or order.get("order_type") or "")
    oid = int(order["id"])
    ono = str(order.get("orderId") or order.get("order_id") or "")
    running = D0
    for i, (uid, pct) in enumerate(pairs):
        if i == len(pairs) - 1:
            amt = _q2(base - running)
        else:
            amt = _q2(base * pct / D100)
            running += amt
        credit_sale_receivable(
            user_id=uid,
            currency_type=currency,
            amount=amt,
            order_pk=oid,
            order_no=ono,
            order_type=ot,
            log_name=log_name,
        )


def _nosplit_bills(order_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, money, IFNULL(is_split, 0) AS is_split, IFNULL(is_sj, 0) AS is_sj
        FROM qd_bill
        WHERE type = 2 AND exp_of_id = %(oid)s AND IFNULL(is_split, 0) = 0
        """,
        {"oid": order_id},
    )


def _nosplit_sum(order_id: int) -> Decimal:
    return _d(
        scalar(
            """
            SELECT IFNULL(SUM(money), 0)
            FROM qd_bill
            WHERE type = 2 AND exp_of_id = %(oid)s AND IFNULL(is_split, 0) = 0
            """,
            {"oid": order_id},
            0,
        )
    )


def _all_receive_sum(order_id: int) -> Decimal:
    return _d(
        scalar(
            """
            SELECT IFNULL(SUM(money), 0)
            FROM qd_bill
            WHERE type = 2 AND exp_of_id = %(oid)s
            """,
            {"oid": order_id},
            0,
        )
    )


def _mark_split(bills: list[dict[str, Any]], is_sj: int | None = None) -> None:
    for b in bills:
        bid = b.get("id")
        if not bid:
            continue
        try:
            if is_sj is None:
                execute(
                    "UPDATE qd_bill SET is_split = 1 WHERE id = %(id)s",
                    {"id": bid},
                )
            else:
                execute(
                    "UPDATE qd_bill SET is_split = 1, is_sj = %(sj)s WHERE id = %(id)s",
                    {"id": bid, "sj": int(is_sj)},
                )
        except Exception:
            execute(
                "UPDATE qd_bill SET is_split = 1 WHERE id = %(id)s",
                {"id": bid},
            )


def _has_log(order_id: int, kw: str) -> bool:
    n = int(
        scalar(
            """
            SELECT COUNT(*)
            FROM account_log
            WHERE order_id = %(oid)s
              AND IFNULL(deleteStatus, 0) = 0
              AND IFNULL(log_amount, 0) > 0
              AND IFNULL(log_name, '') LIKE %(kw)s
            """,
            {"oid": order_id, "kw": f"%{kw}%"},
            0,
        )
        or 0
    )
    return n > 0


def _sum_log(order_id: int, kw: str) -> Decimal:
    return _d(
        scalar(
            """
            SELECT IFNULL(SUM(log_amount), 0)
            FROM account_log
            WHERE order_id = %(oid)s
              AND IFNULL(deleteStatus, 0) = 0
              AND IFNULL(log_amount, 0) > 0
              AND IFNULL(log_name, '') LIKE %(kw)s
            """,
            {"oid": order_id, "kw": f"%{kw}%"},
            0,
        )
    )


def _load_order(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            id, order_id AS orderId, order_type AS orderType,
            currency_type AS currencyType, cost_settle AS costSettle,
            user_scale_info AS userScaleInfo,
            salecb_user_scale_info AS salecbUserScaleInfo,
            collection_time AS collectionTime,
            totalPrice
        FROM experiment_order
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": order_id},
    )


def _collections_complete(order: dict[str, Any]) -> bool:
    collec = str(order.get("collectionTime") or "")
    parts = [x for x in collec.split(",") if x.strip()] if collec else []
    if not parts:
        return True
    n = int(
        scalar(
            """
            SELECT COUNT(*) FROM qd_bill
            WHERE type = 2 AND exp_of_id = %(oid)s
            """,
            {"oid": order["id"]},
            0,
        )
        or 0
    )
    return n >= len(parts)


def _type8_gates_ok(order_id: int) -> bool:
    """子行全部已处理 + 关联采购单已审核(status>=30)。"""
    pending_child = int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order_child
            WHERE order_form_id = %(oid)s
              AND IFNULL(delete_status, 2) <> 1
              AND IFNULL(op_status, 0) <> 2
            """,
            {"oid": order_id},
            0,
        )
        or 0
    )
    if pending_child > 0:
        return False
    pending_po = int(
        scalar(
            """
            SELECT COUNT(*) FROM experiment_order
            WHERE parent_id = %(oid)s
              AND order_type = '9'
              AND IFNULL(deleteStatus, 0) = 0
              AND IFNULL(order_status, 0) < 30
            """,
            {"oid": order_id},
            0,
        )
        or 0
    )
    return pending_po == 0


def _distribute_cost_weighted(
    salecb: str,
    *,
    order: dict[str, Any],
    weight_base: Decimal,
) -> None:
    """salecb 固定金额列表，按金额权重把 weight_base 分完。"""
    pairs = _parse_pairs(salecb)
    if not pairs or weight_base == 0:
        return
    currency = int(order.get("currencyType") or 1)
    ot = str(order.get("orderType") or "")
    oid = int(order["id"])
    ono = str(order.get("orderId") or "")
    total_cfg = sum((a for _, a in pairs), D0)
    running = D0
    for i, (uid, cfg) in enumerate(pairs):
        if i == len(pairs) - 1:
            amt = _q2(weight_base - running)
        else:
            amt = _q2(weight_base * cfg / total_cfg) if total_cfg > 0 else D0
            running += amt
        credit_sale_receivable(
            user_id=uid,
            currency_type=currency,
            amount=amt,
            order_pk=oid,
            order_no=ono,
            order_type=ot,
            log_name="实验成本回款",
        )


def _split_type6(order: dict[str, Any], *, settle_mode: bool) -> None:
    """实验订单分钱（New 与 Settle 共用，New 含毛利已发生分支）。"""
    oid = int(order["id"])
    scale = order.get("userScaleInfo")
    salecb = (order.get("salecbUserScaleInfo") or "").strip()
    sk = _nosplit_sum(oid)
    bills = _nosplit_bills(oid)
    if sk <= 0 or not bills:
        return

    if not salecb:
        _distribute_percent(sk, scale, order=order, log_name="实验毛利分成回款")
        _mark_split(bills)
        return

    pairs = _parse_pairs(salecb)
    cbfcje = sum((a for _, a in pairs), D0)

    if not settle_mode and _has_log(oid, "实验毛利分成"):
        _distribute_percent(sk, scale, order=order, log_name="实验毛利分成回款")
        _mark_split(bills)
        return

    if not settle_mode and _has_log(oid, "实验成本"):
        yfcb = _sum_log(oid, "实验成本")
        sycbfc = cbfcje - yfcb
        if sk > sycbfc:
            _distribute_cost_weighted(salecb, order=order, weight_base=sycbfc)
            _distribute_percent(sk - sycbfc, scale, order=order, log_name="实验毛利分成回款")
        else:
            _distribute_cost_weighted(salecb, order=order, weight_base=sk)
        _mark_split(bills)
        return

    # Settle / 首次：收款与成本对比
    if sk > cbfcje:
        for uid, cfg in pairs:
            credit_sale_receivable(
                user_id=uid,
                currency_type=int(order.get("currencyType") or 1),
                amount=_q2(cfg),
                order_pk=oid,
                order_no=str(order.get("orderId") or ""),
                order_type="6",
                log_name="实验成本回款",
            )
        _distribute_percent(sk - cbfcje, scale, order=order, log_name="实验毛利分成回款")
    else:
        _distribute_cost_weighted(salecb, order=order, weight_base=sk)
    _mark_split(bills)


def _purchase_orders(parent_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, totalPrice, currency_type AS currencyType, pay_status AS payStatus,
               order_status AS orderStatus
        FROM experiment_order
        WHERE parent_id = %(pid)s
          AND order_type = '9'
          AND IFNULL(deleteStatus, 0) = 0
        """,
        {"pid": parent_id},
    )


def _fx_to_parent(amount: Decimal, child_ct: int, parent_ct: int, rate: Decimal) -> Decimal:
    if int(child_ct or 1) == int(parent_ct or 1):
        return amount
    if int(child_ct) == 2:
        return _q2(amount * rate)
    if rate > 0:
        return _q2(amount / rate)
    return amount


def _split_type8(order: dict[str, Any]) -> None:
    oid = int(order["id"])
    if not _type8_gates_ok(oid):
        return
    parent_ct = int(order.get("currencyType") or 1)
    rate = _us_rate()
    pos = _purchase_orders(oid)
    zcb = D0
    all_paid = True
    for po in pos:
        zcb += _fx_to_parent(_d(po.get("totalPrice")), int(po.get("currencyType") or 1), parent_ct, rate)
        try:
            if int(po.get("payStatus") or 0) != 38:
                all_paid = False
        except (TypeError, ValueError):
            all_paid = False

    sk = _all_receive_sum(oid)
    bills = _nosplit_bills(oid)
    if not bills:
        return
    scale = order.get("userScaleInfo")
    is_sj = 0
    can = True

    if all_paid:
        sjzcb = D0
        for po in pos:
            sjzcb += _all_receive_sum(int(po["id"]))
        fqjs = sk - sjzcb
        if fqjs < 0 and not _collections_complete(order):
            can = False
        elif fqjs >= 0:
            is_sj = 1
        if can:
            _distribute_percent(fqjs, scale, order=order, log_name="实验分包订单利润分成回款")
            _mark_split(bills, is_sj=is_sj)
    else:
        fqjs = sk - zcb
        if fqjs < 0 and not _collections_complete(order):
            can = False
        if can and fqjs != 0:
            _distribute_percent(fqjs, scale, order=order, log_name="实验分包订单利润分成回款")
            _mark_split(bills)


@transaction.atomic
def try_split_on_receive(order_id: int) -> bool:
    """收款落库后触发（要求 cost_settle=1）。"""
    order = _load_order(order_id)
    if not order:
        return False
    try:
        if int(order.get("costSettle") or 0) != 1:
            return False
    except (TypeError, ValueError):
        return False
    ot = str(order.get("orderType") or "")
    try:
        if ot == "6":
            _split_type6(order, settle_mode=False)
            return True
        if ot == "8":
            _split_type8(order)
            return True
    except Exception:
        logger.exception("try_split_on_receive failed order_id=%s", order_id)
        raise
    return False


@transaction.atomic
def try_split_on_settle(order_id: int) -> bool:
    """成本结清后对未分账收款补分。"""
    order = _load_order(order_id)
    if not order:
        return False
    # 结清刚写入，强制按已结清处理
    order["costSettle"] = 1
    has_bill = int(
        scalar(
            """
            SELECT COUNT(*) FROM qd_bill
            WHERE type = 2 AND exp_of_id = %(oid)s
            """,
            {"oid": order_id},
            0,
        )
        or 0
    )
    if has_bill <= 0:
        return False
    ot = str(order.get("orderType") or "")
    try:
        if ot == "6":
            _split_type6(order, settle_mode=True)
            return True
        if ot == "8":
            _split_type8(order)
            return True
    except Exception:
        logger.exception("try_split_on_settle failed order_id=%s", order_id)
        raise
    return False


@transaction.atomic
def save_receive_bill(
    *,
    order_id: int,
    money: Decimal | float | str,
    staff_user_id: str | int = "",
    log_info: str = "录入收款",
    bill_date: str = "",
    accessory_id: int | str | None = None,
) -> tuple[bool, str]:
    """后台录入收款票据并按需分钱。对齐 Java saveBillAndAccessory(type=2)。"""
    order = _load_order(order_id)
    if not order:
        return False, "订单不存在"
    ot = str(order.get("orderType") or "")
    if ot not in ("6", "8", "1", "7"):
        return False, "当前订单类型不支持录入收款"
    amt = _d(money)
    if amt <= 0:
        return False, "收款金额须大于 0"
    try:
        acc_id = int(accessory_id) if accessory_id not in (None, "") else None
    except (TypeError, ValueError):
        acc_id = None
    if acc_id is not None and acc_id <= 0:
        acc_id = None
    params = {
        "oid": order_id,
        "money": float(amt),
        "log_info": (log_info or "录入收款")[:500],
        "uid": str(staff_user_id or "") or None,
        "aid": acc_id,
    }
    if bill_date:
        sql = """
            INSERT INTO qd_bill
                (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark{acc_col})
            VALUES
                (NOW(), %(uid)s, %(oid)s, %(money)s, 2, 0, %(bdate)s, %(log_info)s{acc_val})
            """
        execute(
            sql.format(
                acc_col=", accessory_id" if acc_id else "",
                acc_val=", %(aid)s" if acc_id else "",
            ),
            {**params, "bdate": bill_date},
        )
    else:
        sql = """
            INSERT INTO qd_bill
                (add_time, add_user_id, exp_of_id, money, type, is_split, bill_date, mark{acc_col})
            VALUES
                (NOW(), %(uid)s, %(oid)s, %(money)s, 2, 0, NOW(), %(log_info)s{acc_val})
            """
        execute(
            sql.format(
                acc_col=", accessory_id" if acc_id else "",
                acc_val=", %(aid)s" if acc_id else "",
            ),
            params,
        )
    try:
        try_split_on_receive(order_id)
    except Exception as exc:
        logger.exception("split after save_receive_bill")
        split_msg = f"收款已保存，分钱失败：{exc}"
    else:
        split_msg = ""
    try:
        from apps.admin_experiment.repositories import orders as order_repo

        order_repo._write_order_log(
            order_id,
            f"收款 {float(amt)}" + (f"：{log_info}" if log_info else ""),
            user_id=staff_user_id,
        )
        order_repo.auto_generate_appointment_after_online_pay(
            order_id=order_id, staff_user_id=staff_user_id
        )
        order_repo.try_finish_main_order(order_id=order_id, staff_user_id=staff_user_id)
    except Exception:
        logger.exception("post receive hooks failed order_id=%s", order_id)
    if split_msg:
        return True, split_msg
    return True, "收款成功"


def _payment_pa_num(pay_type: str = "3") -> str:
    """对齐 Java payInfoLogNumGeranate：ZF/CZ/HK + yyyyMM + 序号。"""
    from datetime import datetime

    prefix_map = {"1": "CZ", "2": "HK", "3": "ZF", "4": "TX"}
    prefix = prefix_map.get(str(pay_type), "ZF")
    orderstr = prefix + datetime.now().strftime("%Y%m")
    row = fetch_one(
        """
        SELECT pa_num FROM pay_info_log
        WHERE pa_num LIKE %(like)s
        ORDER BY pa_num DESC
        LIMIT 1
        """,
        {"like": f"{orderstr}%"},
    )
    if row and row.get("pa_num"):
        try:
            n = int(str(row["pa_num"])[-5:]) + 1
        except (TypeError, ValueError):
            n = 1
    else:
        n = 1
    return orderstr + (str(n).zfill(5) if n < 100000 else str(n))


@transaction.atomic
def save_member_balance_receive(
    *,
    order_id: int,
    money: Decimal | float | str,
    exp_user_id: str | int = "",
    staff_user_id: str | int = "",
    bill_date: str = "",
    accessory_id: int | str | None = None,
) -> tuple[bool, str]:
    """
    对齐 Java bill/amountPay.ajax：线下订单 + 客户账号 → 会员余额收款。
    扣会员余额、写 pay_info_log(pay_way=6)、再录入收款单。
    """
    order = fetch_one(
        """
        SELECT
            id, order_id AS orderId, order_type AS orderType,
            is_online AS isOnline, custom_user_id AS customUserId
        FROM experiment_order
        WHERE id = %(id)s
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not order:
        return False, "订单不存在"
    ot = str(order.get("orderType") or "")
    if ot not in ("6", "8", "1", "7"):
        return False, "当前订单类型不支持录入收款"
    try:
        is_online = int(order.get("isOnline") or 0)
    except (TypeError, ValueError):
        is_online = 0
    if is_online != 0:
        return False, "线上订单不支持会员余额收款"
    cuid_raw = exp_user_id or order.get("customUserId")
    try:
        cuid = int(cuid_raw) if cuid_raw not in (None, "") else 0
    except (TypeError, ValueError):
        cuid = 0
    if not cuid:
        return False, "订单未绑定客户账号，无法使用会员余额收款"
    amt = _d(money)
    if amt <= 0:
        return False, "收款金额须大于 0"

    from apps.payments.repositories import user_account as ua_repo

    ua_repo.get_or_create(cuid)
    if ua_repo.deduct_balance(cuid, amt) < 1:
        return False, "余额不足"

    log_id = execute_insert(
        """
        INSERT INTO pay_info_log
            (addTime, deleteStatus, user_id, money, status, order_id,
             pay_type, pay_way, pa_num, use_integral, integral_money, payTime)
        VALUES
            (NOW(), 0, %(uid)s, %(money)s, 2, %(order_id)s,
             3, 6, %(pa_num)s, 0, 0, NOW())
        """,
        {
            "uid": cuid,
            "money": float(amt),
            "order_id": str(order_id),
            "pa_num": _payment_pa_num("3"),
        },
    )
    ua_repo.insert_account_log(cuid, -amt, of_id=int(log_id) if log_id else None)

    ok_flag, msg = save_receive_bill(
        order_id=order_id,
        money=amt,
        staff_user_id=staff_user_id,
        log_info="后端-会员余额收款",
        bill_date=bill_date,
        accessory_id=accessory_id,
    )
    if not ok_flag:
        transaction.set_rollback(True)
        return False, msg or "收款失败"
    return True, msg if msg and msg != "收款成功" else "支付成功!"
