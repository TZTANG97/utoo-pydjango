"""付款申请扩展 — addCash / saveaccessory / applyDetail"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from qd_common.serialize import to_jsonable

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one
from apps.core.services.sysconfig import get_config_row, image_web_server
from apps.payments.repositories import payment_application as pa_repo
from apps.payments.repositories import order_lookup as order_repo
from apps.payments.repositories.pay_info import save_exp_user_log
from apps.payments.repositories import user_account as ua_repo

logger = logging.getLogger(__name__)

_STATUS_APPLY = {"1": "待审核", "2": "已审核", "3": "已拒绝"}
_STATUS_LOG = {
    ("1", 2): "充值成功",
    ("2", 2): "支付成功",
    ("3", 2): "支付成功",
    ("4", 2): "提现成功",
}


def has_pending_recharge_application(user_id: int) -> bool:
    row = fetch_one(
        """
        SELECT COUNT(1) AS c FROM payment_application t
        WHERE t.deleteStatus = 0 AND t.orderType = 1
          AND t.applyStatus = '1' AND t.userId = %(uid)s
        """,
        {"uid": user_id},
    )
    return int(row.get("c") or 0) > 0 if row else False


def get_default_account() -> dict[str, Any]:
    for sql in (
        """
        SELECT * FROM company_account_info
        WHERE defaultaccount = 1 AND deleteStatus = 0
        LIMIT 1
        """,
        """
        SELECT * FROM company_account_info
        WHERE is_default = 1 AND deleteStatus = 0
        LIMIT 1
        """,
    ):
        try:
            row = fetch_one(sql)
            if row:
                return to_jsonable(row)
        except Exception as exc:
            logger.warning("get_default_account query failed: %s", exc)
    return {}


@transaction.atomic
def add_cash(
    *, user_id: int, money: str, bank_num: str, account_name: str
) -> tuple[bool, str]:
    try:
        amount = Decimal(str(money).strip())
    except (InvalidOperation, ValueError):
        return False, "金额无效"
    if amount <= 0:
        return False, "金额必须大于0"
    if not (bank_num or "").strip():
        return False, "银行卡号不能为空"
    if not (account_name or "").strip():
        return False, "姓名不能为空"

    pa_num = pa_repo.generate_pa_num("4")
    pa_id = execute_insert(
        """
        INSERT INTO payment_application
            (addTime, deleteStatus, userId, orderType, applyStatus,
             money, bankNum, accountName, pa_num, ptype)
        VALUES
            (NOW(), 0, %(uid)s, '4', '1', %(money)s, %(bank)s, %(name)s, %(pa)s, '0')
        """,
        {
            "uid": user_id,
            "money": float(amount),
            "bank": bank_num.strip(),
            "name": account_name.strip(),
            "pa": pa_num,
        },
    )
    pa_repo.insert_submitted_log(pa_id=pa_id, user_id=user_id)
    ua_repo.get_or_create(user_id)
    execute(
        """
        UPDATE user_account
        SET amount = GREATEST(COALESCE(amount, 0) - %(m)s, 0),
            update_time = NOW()
        WHERE delete_status = 0 AND user_id = %(uid)s
        """,
        {"m": float(amount), "uid": user_id},
    )
    return True, "审核已提交!"


def _link_accessories(
    *, file_ids: str, pa_id: int | None = None, exp_of_id: int | None = None
) -> None:
    for fid in (file_ids or "").split(","):
        fid = fid.strip()
        if not fid.isdigit():
            continue
        if pa_id is not None:
            execute(
                "UPDATE accessory SET pa_id = %(pid)s WHERE id = %(aid)s",
                {"pid": pa_id, "aid": int(fid)},
            )
        elif exp_of_id is not None:
            execute(
                "UPDATE accessory SET exp_of_id = %(oid)s WHERE id = %(aid)s",
                {"oid": exp_of_id, "aid": int(fid)},
            )


@transaction.atomic
def save_accessory(
    *,
    user_id: int,
    order_ids: str,
    file_id: str,
    order_type: str = "2",
    pay_way: str = "3",
) -> tuple[bool, str]:
    raw_ids = [x.strip() for x in (order_ids or "").split(",") if x.strip()]
    if not raw_ids:
        return False, "订单不能为空"
    if not (file_id or "").strip():
        return False, "请上传回执单"

    uid, mobile = order_repo.user_context(user_id)
    file_parts = [x.strip() for x in file_id.split(",") if x.strip()]

    for idx, sid in enumerate(raw_ids):
        oid = int(sid)
        order = order_repo.get_sale_order_for_user(
            order_id=oid, user_id=uid, mobile=mobile
        )
        if not order:
            return False, "订单不存在或无权操作"

        if idx == 0:
            _link_accessories(file_ids=",".join(file_parts), exp_of_id=oid)
        else:
            for fid in file_parts:
                row = fetch_one(
                    "SELECT path, name, type, info, ext FROM accessory WHERE id = %(aid)s LIMIT 1",
                    {"aid": int(fid)},
                )
                if not row:
                    continue
                execute_insert(
                    """
                    INSERT INTO accessory
                        (addTime, deleteStatus, path, name, type, info, ext, exp_of_id)
                    VALUES (NOW(), 0, %(path)s, %(name)s, %(type)s, %(info)s, %(ext)s, %(oid)s)
                    """,
                    {
                        "path": row["path"],
                        "name": row["name"],
                        "type": row["type"],
                        "info": row["info"],
                        "ext": row.get("ext") or "",
                        "oid": oid,
                    },
                )

        total = Decimal(str(order.get("totalPrice") or 0))
        paid = Decimal(str(order_repo.sum_bill(oid, 2)))
        due = max(total - paid, Decimal("0"))

        pa_num = pa_repo.generate_pa_num(order_type or "2")
        pa_id = execute_insert(
            """
            INSERT INTO payment_application
                (addTime, deleteStatus, userId, orderId, orderType,
                 applyStatus, money, pay_way, pa_num, ptype)
            VALUES
                (NOW(), 0, %(uid)s, %(oid)s, %(otype)s, '1', %(money)s, %(pw)s, %(pa)s, '0')
            """,
            {
                "uid": user_id,
                "oid": str(oid),
                "otype": order_type or "2",
                "money": float(due),
                "pw": int(pay_way or 3),
                "pa": pa_num,
            },
        )
        pa_repo.insert_submitted_log(pa_id=pa_id, user_id=user_id)
        execute(
            "UPDATE experiment_order SET isUploadReceipt = 1 WHERE id = %(oid)s",
            {"oid": oid},
        )
        save_exp_user_log(
            user_id,
            f"（支付方式：线下）支付成功，关联单号{order.get('order_id') or oid}",
        )
    return True, "申请已提交"


def _accessory_path(accessory_id: Any, image_base: str) -> str:
    if not accessory_id:
        return ""
    row = fetch_one(
        "SELECT path, name FROM accessory WHERE id = %(aid)s AND deleteStatus = 0 LIMIT 1",
        {"aid": int(accessory_id)},
    )
    if not row or not row.get("path") or not row.get("name"):
        return ""
    base = image_base.rstrip("/")
    return f"{base}/{str(row['path']).strip('/')}/{str(row['name']).strip('/')}"


def _accessory_by_order(order_id: Any, image_base: str) -> str:
    if not order_id:
        return ""
    row = fetch_one(
        """
        SELECT path, name FROM accessory
        WHERE deleteStatus = 0 AND exp_of_id = %(oid)s AND type = 7
        ORDER BY id ASC LIMIT 1
        """,
        {"oid": int(order_id)},
    )
    if not row:
        return ""
    base = image_base.rstrip("/")
    return f"{base}/{str(row['path']).strip('/')}/{str(row['name']).strip('/')}"


def apply_detail(
    *, user_id: int, record_id: str, detail_type: str = "0"
) -> dict[str, Any] | None:
    if not record_id or not str(record_id).strip():
        return {"obj": {}, "files": [], "ofList": [], "logs": []}

    config = get_config_row()
    image_base = image_web_server(config)
    dtype = (detail_type or "0").strip()

    if dtype == "0":
        return _detail_from_application(
            user_id=user_id, record_id=record_id, image_base=image_base
        )
    if dtype in ("1", "3"):
        return _detail_from_pay_log(user_id=user_id, record_id=record_id)
    if dtype == "2":
        return _detail_from_company_log(user_id=user_id, record_id=record_id)
    return None


def _detail_from_application(
    *, user_id: int, record_id: str, image_base: str
) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT * FROM payment_application WHERE id = %(id)s AND deleteStatus = 0 LIMIT 1",
        {"id": int(record_id)},
    )
    if not row or int(row["userId"]) != int(user_id):
        return None

    app = to_jsonable(row)
    app["applyStatus"] = _STATUS_APPLY.get(
        str(app.get("applyStatus") or ""), app.get("applyStatus")
    )
    order_type = str(app.get("orderType") or "")
    pay_way = int(app.get("pay_way") or 0)
    hzd = ""
    if order_type == "1" and pay_way == 3:
        hzd = _accessory_path(app.get("accessoryId"), image_base)
    elif order_type in ("2", "3") and app.get("orderId"):
        hzd = _accessory_by_order(app.get("orderId"), image_base)
    app["hzdPath"] = hzd

    of_list: list[dict[str, Any]] = []
    if app.get("orderId"):
        for oid in str(app["orderId"]).split(","):
            oid = oid.strip()
            if not oid.isdigit():
                continue
            of_row = fetch_one(
                "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
                {"oid": int(oid)},
            )
            if of_row:
                of_list.append(dict(of_row))

    files: list[dict[str, Any]] = []
    if order_type == "1":
        files = fetch_all(
            """
            SELECT id, path, name, info, ext FROM accessory
            WHERE deleteStatus = 0 AND pa_id = %(pid)s
            """,
            {"pid": int(record_id)},
        )
    elif app.get("orderId"):
        for oid in str(app["orderId"]).split(","):
            oid = oid.strip()
            if not oid.isdigit():
                continue
            files.extend(
                fetch_all(
                    """
                    SELECT id, path, name, info, ext FROM accessory
                    WHERE deleteStatus = 0 AND exp_of_id = %(oid)s AND type = 7
                    """,
                    {"oid": int(oid)},
                )
            )

    logs = fetch_all(
        """
        SELECT id, content, paymentId, userId, addTime
        FROM payment_application_log
        WHERE deleteStatus = 0 AND paymentId = %(pid)s
        ORDER BY addTime ASC
        """,
        {"pid": int(record_id)},
    )
    return {
        "obj": app,
        "files": [to_jsonable(f) for f in files],
        "ofList": of_list,
        "logs": [to_jsonable(l) for l in logs],
    }


def _detail_from_pay_log(*, user_id: int, record_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT * FROM pay_info_log WHERE id = %(id)s AND deleteStatus = 0 LIMIT 1",
        {"id": int(record_id)},
    )
    if not row or int(row["user_id"]) != int(user_id):
        return None

    plog = to_jsonable(row)
    pay_type = str(plog.get("pay_type") or "")
    status = int(plog.get("status") or 0)
    app: dict[str, Any] = {
        "id": plog["id"],
        "addTime": plog.get("addTime") or plog.get("payTime"),
        "orderType": pay_type,
        "pay_way": plog.get("pay_way"),
        "pa_num": plog.get("pa_num"),
        "money": plog.get("money"),
        "applyStatus": _STATUS_LOG.get((pay_type, status), str(status)),
    }
    of_list: list[dict[str, Any]] = []
    if plog.get("order_id"):
        for oid in str(plog["order_id"]).split(","):
            oid = oid.strip()
            if not oid.isdigit():
                continue
            of_row = fetch_one(
                "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
                {"oid": int(oid)},
            )
            if of_row:
                of_list.append(dict(of_row))

    files: list[dict[str, Any]] = []
    eor = None
    if plog.get("pa_id"):
        files = fetch_all(
            """
            SELECT id, path, name, info, ext FROM accessory
            WHERE deleteStatus = 0 AND off_recharge_id = %(rid)s
            """,
            {"rid": int(plog["pa_id"])},
        )
        if not files:
            files = fetch_all(
                """
                SELECT id, path, name, info, ext FROM accessory
                WHERE deleteStatus = 0 AND pa_id = %(rid)s
                """,
                {"rid": int(plog["pa_id"])},
            )
        eor_row = fetch_one(
            """
            SELECT id, recharge_num, recharge_type FROM exp_offline_recharge
            WHERE id = %(rid)s LIMIT 1
            """,
            {"rid": int(plog["pa_id"])},
        )
        if eor_row:
            eor = to_jsonable(eor_row)

    body: dict[str, Any] = {
        "obj": app,
        "files": [to_jsonable(f) for f in files],
        "ofList": of_list,
        "logs": None,
    }
    if eor:
        body["eor"] = eor
    return body


def _detail_from_company_log(*, user_id: int, record_id: str) -> dict[str, Any] | None:
    row = fetch_one(
        "SELECT * FROM company_pay_log WHERE id = %(id)s AND deleteStatus = 0 LIMIT 1",
        {"id": int(record_id)},
    )
    if not row:
        return None

    plog = to_jsonable(row)
    pay_type = str(plog.get("pay_type") or "")
    status = int(plog.get("status") or 0)
    app: dict[str, Any] = {
        "id": plog["id"],
        "addTime": plog.get("addTime"),
        "orderType": pay_type,
        "pay_way": plog.get("pay_way"),
        "pa_num": plog.get("pa_num"),
        "money": plog.get("money"),
        "applyStatus": _STATUS_LOG.get((pay_type, status), str(status)),
    }
    of_list: list[dict[str, Any]] = []
    if plog.get("order_id"):
        of_row = fetch_one(
            "SELECT id, order_id FROM experiment_order WHERE id = %(oid)s LIMIT 1",
            {"oid": int(plog["order_id"])},
        )
        if of_row:
            of_list.append(dict(of_row))
    return {"obj": app, "files": None, "ofList": of_list, "logs": None}
