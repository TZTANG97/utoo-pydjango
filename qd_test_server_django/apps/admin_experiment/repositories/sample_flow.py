"""实验子订单(type=10)样品/测试流转，对齐 Java ExperimentSubOrderController 核心状态机。"""
from __future__ import annotations

from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one, scalar
from django.db import transaction
from datetime import datetime

# child line statuses (jy.main.js childOrderStatus / ChildOrderStatusEnum)
ST_PROCESSED = 2
ST_ARRIVE = 36
ST_PICK = 37
ST_TESTING = 38
ST_TEST_DONE = 39
ST_RETURN = 41
ST_SHIP_BACK = 42  # 枚举有，但寄回实际落库为 YWC=50
ST_RETAIN = 43  # 枚举有，但留存实际落库为 YWC=50
ST_SCRAP = 44
ST_DONE = 50  # Java 寄回/留存/报废 → ChildOrderStatusEnum.YWC

ACTION_LABEL = {
    ST_ARRIVE: "样品到货",
    ST_PICK: "样品领用",
    ST_TESTING: "开始测试",
    ST_TEST_DONE: "测试完成",
    ST_RETURN: "样品归还",
    ST_SHIP_BACK: "样品寄回",
    ST_RETAIN: "样品留存",
    ST_SCRAP: "样品报废",
    ST_DONE: "已完成",
}


def _parse_ids(raw: Any) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        out = []
        for x in raw:
            try:
                out.append(int(x))
            except (TypeError, ValueError):
                pass
        return out
    text = str(raw).strip()
    if not text:
        return []
    out = []
    for part in text.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out


def _write_log(order_id: int, info: str, user_id: str | int | None = None) -> None:
    uid = str(user_id).strip() if user_id not in (None, "") else None
    try:
        execute(
            """
            INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info, log_user_id)
            VALUES (NOW(), 0, %(oid)s, %(info)s, %(uid)s)
            """,
            {"oid": order_id, "info": (info or "")[:500], "uid": uid},
        )
    except Exception:
        try:
            execute(
                """
                INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info)
                VALUES (NOW(), 0, %(oid)s, %(info)s)
                """,
                {"oid": order_id, "info": (info or "")[:500]},
            )
        except Exception:
            pass


def _bump_main_status(order_id: int, min_status: int) -> None:
    row = fetch_one(
        "SELECT order_status AS st FROM experiment_order WHERE id = %(id)s LIMIT 1",
        {"id": order_id},
    )
    if not row:
        return
    try:
        st = int(row.get("st") or 0)
    except (TypeError, ValueError):
        st = 0
    if st < min_status:
        execute(
            "UPDATE experiment_order SET order_status = %(st)s WHERE id = %(id)s",
            {"st": min_status, "id": order_id},
        )


def _all_children_status_ge(order_id: int, min_st: int) -> bool:
    children = list_children_for_order(order_id)
    if not children:
        return False
    for c in children:
        try:
            cst = int(c.get("orderStatus") or 0)
        except (TypeError, ValueError):
            return False
        if cst < min_st:
            return False
    return True


def _all_children_done(order_id: int) -> bool:
    children = list_children_for_order(order_id)
    if not children:
        return False
    for c in children:
        try:
            cst = int(c.get("orderStatus") or 0)
        except (TypeError, ValueError):
            return False
        if cst != ST_DONE:
            return False
    return True


def _complete_sub_order_if_ready(
    order_id: int, staff_user_id: str | int | None = None
) -> None:
    """对齐 Java updateSubOrderStatus：全部子行=50 时主单→50。"""
    if not _all_children_done(order_id):
        return
    try:
        execute(
            """
            UPDATE experiment_order
            SET order_status = %(st)s, finishTime = NOW()
            WHERE id = %(id)s
            """,
            {"st": ST_DONE, "id": order_id},
        )
    except Exception:
        execute(
            "UPDATE experiment_order SET order_status = %(st)s WHERE id = %(id)s",
            {"st": ST_DONE, "id": order_id},
        )
    _write_log(order_id, "子订单全部完成", user_id=staff_user_id)


def list_children_for_order(order_id: int) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.op_status AS opStatus, c.is_confirm AS isConfirm,
            c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.goods_name AS goodsName
        FROM experiment_order_child c
        WHERE c.order_form_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id
        """,
        {"oid": order_id},
    )
    if rows:
        return rows
    return fetch_all(
        """
        SELECT
            c.id, c.order_id AS childOrderId, c.order_status AS orderStatus,
            c.op_status AS opStatus, c.is_confirm AS isConfirm,
            c.is_meeting AS isMeeting, c.meeting_num AS meetingNum,
            c.line_id AS lineId, c.sample_id AS sampleId,
            c.goods_name AS goodsName
        FROM exp_qd_purchase_order_child poc
        JOIN experiment_order_child c ON poc.order_child_id = c.id
        WHERE poc.purchase_order_id = %(oid)s AND IFNULL(c.delete_status, 2) <> 1
        ORDER BY c.id
        """,
        {"oid": order_id},
    )


def attach_sample_action_flags(row: dict[str, Any]) -> None:
    """写入 Java 同名 *Show 标志；适用实验子订单 type=10 / 分包子订单 type=9。"""
    ot = str(row.get("orderType") or "")
    defaults = {
        "ypdhShow": False,
        "yplyShow": False,
        "kscsShow": False,
        "cswcShow": False,
        "ypghShow": False,
        "ypjhShow": False,
        "yplcShow": False,
        "ypfcShow": False,
        "qrwcShow": False,
        "videoShow": False,
        "canConfirmDone": False,
    }
    for k, v in defaults.items():
        row[k] = v
    if ot not in ("9", "10"):
        return
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    # Java type=9：样品主栏 status≥35；type=10：审核后(≥30)即可
    min_st = 35 if ot == "9" else 30
    if st < min_st:
        return

    children = list_children_for_order(int(row["id"]))
    statuses = []
    for c in children:
        try:
            statuses.append(int(c.get("orderStatus") or -1))
        except (TypeError, ValueError):
            pass

    parent = None
    if row.get("parentId"):
        parent = fetch_one(
            """
            SELECT is_online AS isOnline, reverso_context AS reversoContext, is_video AS isVideo
            FROM experiment_order WHERE id = %(id)s LIMIT 1
            """,
            {"id": row["parentId"]},
        )
    reverso = 0
    is_online = 0
    parent_video = 0
    if parent:
        try:
            reverso = int(parent.get("reversoContext") or 0)
        except (TypeError, ValueError):
            reverso = 0
        try:
            is_online = int(parent.get("isOnline") or 0)
        except (TypeError, ValueError):
            is_online = 0
        try:
            parent_video = int(parent.get("isVideo") or 0)
        except (TypeError, ValueError):
            parent_video = 0
    try:
        self_video = int(row.get("isVideo") or 0)
    except (TypeError, ValueError):
        self_video = 0
    is_video = 1 if (self_video == 1 or parent_video == 1) else 0

    row["ypdhShow"] = ST_PROCESSED in statuses
    row["yplyShow"] = ST_ARRIVE in statuses
    row["kscsShow"] = ST_PICK in statuses
    row["cswcShow"] = ST_TESTING in statuses
    row["ypghShow"] = ST_TEST_DONE in statuses
    has41 = ST_RETURN in statuses

    # Java：线上订单寄回/留存需至少一行 status=41 且 is_sure=1
    def _online_ok() -> bool:
        if is_online != 1:
            return True
        n = int(
            scalar(
                """
                SELECT COUNT(*)
                FROM exp_qd_purchase_order_child poc
                JOIN experiment_order_child c ON poc.order_child_id = c.id
                WHERE poc.purchase_order_id = %(oid)s
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND c.order_status = %(st)s
                  AND IFNULL(c.is_sure, 0) = 1
                """,
                {"oid": int(row["id"]), "st": ST_RETURN},
                0,
            )
            or 0
        )
        return n > 0

    ship_retain_ok = has41 and _online_ok()
    row["ypjhShow"] = ship_retain_ok and reverso == 1
    row["yplcShow"] = ship_retain_ok and reverso != 1

    # 确认完成仅 type=10
    qrwc = False
    if ot == "10":
        for c in children:
            try:
                cst = int(c.get("orderStatus") or 0)
                conf = int(c.get("isConfirm") or 0)
            except (TypeError, ValueError):
                continue
            if cst >= ST_TEST_DONE and conf == 0:
                qrwc = True
                break
    row["qrwcShow"] = qrwc
    row["canConfirmDone"] = qrwc
    # Java：ypfcShow && qrwcShow 才显示复测（type=10）
    row["ypfcShow"] = (
        is_online == 0
        and any(s in (ST_TEST_DONE, ST_RETURN) for s in statuses)
        and (qrwc if ot == "10" else True)
    )

    video_show = False
    video_min = 36 if ot == "9" else ST_ARRIVE
    if is_video == 1 and st >= video_min:
        for c in children:
            try:
                cst = int(c.get("orderStatus") or 0)
                meet = int(c.get("isMeeting") or 0)
            except (TypeError, ValueError):
                continue
            if cst >= ST_ARRIVE and meet == 0:
                video_show = True
                break
    row["videoShow"] = video_show


def attach_type10_action_flags(row: dict[str, Any]) -> None:
    """兼容旧名。"""
    attach_sample_action_flags(row)


def _load_order(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT id, order_id AS orderId, order_type AS orderType, order_status AS orderStatus,
               parent_id AS parentId, is_video AS isVideo
        FROM experiment_order WHERE id = %(id)s LIMIT 1
        """,
        {"id": order_id},
    )


def _set_children_status(
    *,
    order_id: int,
    child_ids: list[int],
    expect_from: set[int] | None,
    to_status: int,
    log_suffix: str,
    extra_sql: str = "",
    extra_params: dict | None = None,
    staff_user_id: str | int | None = None,
    bump_main: bool | str = True,
) -> tuple[bool, str]:
    """
    bump_main:
      True / "min" — 主单 status 升到 to_status（若更小）
      "all_ge" — 仅当全部子行 status >= to_status 时升主单
      "done" — 全部子行=50 时主单→50
      False / "none" — 不改主单
    """
    order = _load_order(order_id)
    if not order:
        return False, "订单不存在"
    if str(order.get("orderType") or "") not in ("9", "10"):
        return False, "仅实验子订单/分包子订单支持该操作"
    if not child_ids:
        return False, "请选择子单行"
    ok_n = 0
    for cid in child_ids:
        child = fetch_one(
            """
            SELECT id, order_id AS childOrderId, order_status AS orderStatus, order_form_id AS ofId
            FROM experiment_order_child
            WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
            LIMIT 1
            """,
            {"id": cid},
        )
        if not child:
            continue
        of_id = child.get("ofId")
        belongs = int(of_id or 0) == int(order_id)
        if not belongs:
            n = int(
                scalar(
                    """
                    SELECT COUNT(*) FROM exp_qd_purchase_order_child
                    WHERE purchase_order_id = %(oid)s AND order_child_id = %(cid)s
                    """,
                    {"oid": order_id, "cid": cid},
                    0,
                )
                or 0
            )
            belongs = n > 0
        if not belongs:
            continue
        try:
            cst = int(child.get("orderStatus") or -1)
        except (TypeError, ValueError):
            cst = -1
        if expect_from is not None and cst not in expect_from:
            continue
        params = {"st": to_status, "id": cid}
        if extra_params:
            params.update(extra_params)
        execute(
            f"""
            UPDATE experiment_order_child
            SET order_status = %(st)s {extra_sql}
            WHERE id = %(id)s
            """,
            params,
        )
        _write_log(
            order_id,
            f"{child.get('childOrderId') or cid}{log_suffix}",
            user_id=staff_user_id,
        )
        ok_n += 1
    if ok_n <= 0:
        return False, "没有可操作的子单行（状态不符或不属于本单）"
    mode = bump_main
    if mode is True:
        mode = "min"
    if mode == "min":
        _bump_main_status(order_id, to_status)
    elif mode == "all_ge":
        if _all_children_status_ge(order_id, to_status):
            _bump_main_status(order_id, to_status)
    elif mode == "done":
        _complete_sub_order_if_ready(order_id, staff_user_id=staff_user_id)
    return True, "操作成功"


@transaction.atomic
def sample_arrive(
    *,
    order_id: int,
    child_ids: Any,
    store_id: str = "",
    store_position_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """
    对齐 Java inTreasury/saveInTreasury type=1：
    - 不选仓库/仓位：仅推进子行状态到样品到货
    - 同时选仓库+仓位：写入样品管理单，并把样品信息落到对应仓位
    - 仅传仓位 id：反查 sample_store_id
    """
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    sid = str(store_id or "").strip()
    spos = str(store_position_id or "").strip()
    if "_" in spos:
        spos = spos.split("_", 1)[-1].strip()
    if ";" in spos:
        spos = spos.split(";", 1)[0].strip()
    if spos and not sid:
        pos_row = fetch_one(
            """
            SELECT id, sample_store_id AS storeId
            FROM sample_goods_store_position
            WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": int(spos) if spos.isdigit() else 0},
        )
        if pos_row and pos_row.get("storeId") is not None:
            sid = str(pos_row.get("storeId"))
    if (sid and not spos) or (spos and not sid):
        return False, "请同时选择仓库名称和仓库位置，或不选"
    log_suffix = "样品到货"
    extra = ""
    extra_params: dict[str, Any] = {}

    if sid and spos:
        if len(ids) != 1:
            return False, "选择仓库位置时请只勾选一行"
        try:
            store_i = int(sid)
            pos_i = int(spos)
        except (TypeError, ValueError):
            return False, "仓库或仓位参数错误"
        store = fetch_one(
            """
            SELECT id, sample_store_name AS storeName
            FROM sample_goods_storehouse
            WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": store_i},
        )
        if not store:
            return False, "仓库不存在"
        pos = fetch_one(
            """
            SELECT
                t.id, t.goods_brand_id AS goodsBrandId, t.number,
                b.block AS blockName
            FROM sample_goods_store_position t
            LEFT JOIN sample_goods_store_block b ON t.sample_block_id = b.id
            WHERE t.id = %(id)s
              AND t.sample_store_id = %(sid)s
              AND IFNULL(t.deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": pos_i, "sid": store_i},
        )
        if not pos:
            return False, "仓库位置不存在"
        try:
            occupied = int(pos.get("goodsBrandId") or 0)
        except (TypeError, ValueError):
            occupied = 0
        if occupied:
            return False, "请确认样本仓库位置为空闲!"
        child = fetch_one(
            """
            SELECT
                id, order_id AS childOrderId, order_status AS orderStatus,
                goods_id AS goodsId, goods_name AS goodsName,
                goods_brand_id AS goodsBrandId, goods_brand_name AS goodsBrandName,
                goods_spec AS goodsSpec
            FROM experiment_order_child
            WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
            LIMIT 1
            """,
            {"id": ids[0]},
        )
        if not child:
            return False, "子单行不存在"
        slot = f"{pos.get('blockName') or ''}-{pos.get('number') or ''}".strip("-")
        store_name = str(store.get("storeName") or "")
        log_suffix = f"样品到货,仓库位置{store_name}; {slot}"
        extra = ", in_status = 1"
        # 占用仓位
        execute(
            """
            UPDATE sample_goods_store_position
            SET goods_brand_id = %(brand_id)s,
                goods_brand_name = %(brand_name)s,
                goods_spec = %(spec)s,
                goods_id = %(goods_id)s,
                position_status = 1,
                sample_name = %(sample_name)s
            WHERE id = %(id)s
            """,
            {
                "id": pos_i,
                "brand_id": child.get("goodsBrandId") or 0,
                "brand_name": str(child.get("goodsBrandName") or "")[:100],
                "spec": str(child.get("goodsSpec") or "")[:200],
                "goods_id": child.get("goodsId") or 0,
                "sample_name": str(child.get("goodsName") or "")[:200],
            },
        )
        # 样品管理单
        out_num = f"YP{datetime.now().strftime('%Y%m%d%H%M%S')}{ids[0]}"
        out_id = execute_insert(
            """
            INSERT INTO exp_goods_out_treasury
                (addTime, deleteStatus, out_num, order_id, store_id, status,
                 in_out_type, ftype, inTreasury_user, sj_out_time)
            VALUES
                (NOW(), 0, %(out_num)s, %(oid)s, %(store_id)s, 1,
                 1, 1, NULL, NOW())
            """,
            {"out_num": out_num, "oid": order_id, "store_id": store_i},
        )
        execute_insert(
            """
            INSERT INTO exp_goods_out_treasury_child
                (addTime, deleteStatus, out_id, order_child_id, goods_id, goods_name,
                 goods_brand_id, goods_brand_name, goods_spec, store_id,
                 store_position_id, got_status)
            VALUES
                (NOW(), 0, %(out_id)s, %(cid)s, %(goods_id)s, %(goods_name)s,
                 %(brand_id)s, %(brand_name)s, %(spec)s, %(store_id)s,
                 %(pos_id)s, 1)
            """,
            {
                "out_id": out_id,
                "cid": ids[0],
                "goods_id": child.get("goodsId") or 0,
                "goods_name": str(child.get("goodsName") or "")[:200],
                "brand_id": child.get("goodsBrandId") or 0,
                "brand_name": str(child.get("goodsBrandName") or "")[:100],
                "spec": str(child.get("goodsSpec") or "")[:200],
                "store_id": store_i,
                "pos_id": pos_i,
            },
        )
        try:
            execute(
                """
                INSERT INTO exp_outin_depot_log
                    (addTime, deleteStatus, of_id, log_info, store_id, store_position_id)
                VALUES
                    (NOW(), 0, %(of_id)s, %(info)s, %(store_id)s, %(pos_id)s)
                """,
                {
                    "of_id": out_id,
                    "info": log_suffix[:500],
                    "store_id": store_i,
                    "pos_id": pos_i,
                },
            )
        except Exception:
            pass
    else:
        # 无仓位：对齐 Java isPosition=0，标记 in_status
        extra = ", in_status = 1"

    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={0, 1, ST_PROCESSED},
        to_status=ST_ARRIVE,
        log_suffix=log_suffix,
        extra_sql=extra,
        extra_params=extra_params or None,
        staff_user_id=staff_user_id,
    )
    if ok and sid and spos:
        return True, "样品入库成功！"
    return ok, msg


def _clear_store_position(pos_id: int) -> None:
    try:
        execute(
            """
            UPDATE sample_goods_store_position
            SET goods_brand_id = NULL, goods_brand_name = NULL, serial_number = NULL,
                goods_id = NULL, goods_spec = NULL, inventory_id = NULL,
                char_number = NULL, sample_name = NULL, position_status = 0
            WHERE id = %(id)s
            """,
            {"id": pos_id},
        )
    except Exception:
        pass


def _child_treasury(child_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.out_id AS outId, t.store_id AS storeId,
            t.store_position_id AS storePosId, t.got_status AS gotStatus
        FROM exp_goods_out_treasury_child t
        LEFT JOIN exp_goods_out_treasury o ON t.out_id = o.id
        WHERE t.order_child_id = %(cid)s
          AND IFNULL(o.status, 0) != 3
        ORDER BY t.id DESC
        LIMIT 1
        """,
        {"cid": child_id},
    )


@transaction.atomic
def sample_pick(
    *,
    order_id: int,
    child_ids: Any,
    store_position_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java type=2：有仓位则须确认仓位，领用后清空仓位。"""
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    order = _load_order(order_id)
    if not order:
        return False, "订单不存在"
    is_video = 0
    try:
        is_video = int(order.get("isVideo") or 0)
    except (TypeError, ValueError):
        is_video = 0
    if not is_video and order.get("parentId"):
        parent = fetch_one(
            "SELECT is_video AS isVideo FROM experiment_order WHERE id = %(id)s LIMIT 1",
            {"id": order["parentId"]},
        )
        if parent:
            try:
                is_video = int(parent.get("isVideo") or 0)
            except (TypeError, ValueError):
                is_video = 0
    spos = str(store_position_id or "").strip()
    if "_" in spos:
        # 兼容扫码 storePosId_123
        parts = spos.split("_", 1)
        if parts[0] == "storePosId" and parts[1].isdigit():
            spos = parts[1]
    for cid in ids:
        child = fetch_one(
            """
            SELECT id, is_meeting AS isMeeting, order_id AS childOrderId
            FROM experiment_order_child WHERE id = %(id)s LIMIT 1
            """,
            {"id": cid},
        )
        if not child:
            continue
        if is_video == 1:
            try:
                meet = int(child.get("isMeeting") or 0)
            except (TypeError, ValueError):
                meet = 0
            if meet != 1:
                return False, f"子单 {child.get('childOrderId') or cid} 请先预约云视频"
        gotc = _child_treasury(cid)
        if gotc and gotc.get("storePosId") is not None and str(gotc.get("storePosId") or "") != "":
            # 未传仓位时，用库存记录中的仓位作为确认（对齐 Java storeInfo 确认后提交）
            confirm_pos = spos or str(gotc.get("storePosId"))
            if str(gotc.get("storePosId")) != str(confirm_pos):
                return False, "样本仓库位置不正确!"
            spos = confirm_pos
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_ARRIVE},
        to_status=ST_PICK,
        log_suffix="样品领用,仓库位置无",
        staff_user_id=staff_user_id,
        bump_main=False,  # Java 领用不升主单到 37
    )
    if not ok:
        return ok, msg
    # 领用后清空仓位占用（对齐 Java）
    for cid in ids:
        gotc = _child_treasury(cid)
        if not gotc:
            continue
        try:
            pos_id = int(gotc.get("storePosId") or 0)
        except (TypeError, ValueError):
            pos_id = 0
        if pos_id:
            _clear_store_position(pos_id)
        try:
            execute(
                """
                UPDATE exp_goods_out_treasury_child
                SET store_id = NULL, store_position_id = NULL, got_status = 2
                WHERE id = %(id)s
                """,
                {"id": gotc["id"]},
            )
        except Exception:
            pass
        try:
            execute(
                """
                INSERT INTO exp_outin_depot_log
                    (addTime, deleteStatus, of_id, log_info)
                VALUES (NOW(), 0, %(of_id)s, %(info)s)
                """,
                {"of_id": gotc.get("outId"), "info": "样品领用,仓库位置无"},
            )
        except Exception:
            pass
    return True, "操作成功"


@transaction.atomic
def test_start(
    *,
    order_id: int,
    child_ids: Any,
    line_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java ceshistart：确认实验平台 lineId 与子行一致，子行→38，主单升至38。"""
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    if len(ids) != 1:
        return False, "开始测试请只勾选一行"
    lid = str(line_id or "").strip()
    if "_" in lid:
        lid = lid.split("_", 1)[-1].strip()
    if not lid:
        return False, "请确认实验平台"
    child = fetch_one(
        """
        SELECT id, order_id AS childOrderId, order_status AS orderStatus,
               line_id AS lineId, test_user_id AS testUserId
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": ids[0]},
    )
    if not child:
        return False, "子单行不存在"
    child_line = str(child.get("lineId") or "").strip()
    if child_line and child_line != lid:
        return False, "实验平台不正确!"
    if not child_line:
        # 创建子单时已要求选平台；若历史数据缺 line_id 则允许写入确认值
        execute(
            "UPDATE experiment_order_child SET line_id = %(lid)s WHERE id = %(id)s",
            {"lid": lid[:64], "id": ids[0]},
        )
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_PICK},
        to_status=ST_TESTING,
        log_suffix="开始测试",
        staff_user_id=staff_user_id,
        bump_main="min",
    )
    if not ok:
        return ok, msg
    # 实验日志：开始测试
    try:
        execute_insert(
            """
            INSERT INTO experiment_log
                (addTime, deleteStatus, order_child_id, start_time, status)
            VALUES (NOW(), 0, %(cid)s, NOW(), 2)
            """,
            {"cid": ids[0]},
        )
    except Exception:
        try:
            execute_insert(
                """
                INSERT INTO experiment_log
                    (addTime, deleteStatus, order_child_id, start_time)
                VALUES (NOW(), 0, %(cid)s, NOW())
                """,
                {"cid": ids[0]},
            )
        except Exception:
            pass
    # 平台占用 +1（失败不阻断）
    try:
        execute(
            """
            UPDATE experiment_line
            SET run_num = IFNULL(run_num, 0) + 1,
                line_status = CASE WHEN IFNULL(line_status, 0) = 0 THEN 1 ELSE line_status END
            WHERE id = %(id)s
            """,
            {"id": int(lid) if lid.isdigit() else 0},
        )
    except Exception:
        pass
    return True, "操作成功"


@transaction.atomic
def test_end(
    *, order_id: int, child_ids: Any, staff_user_id: str | int | None = None
) -> tuple[bool, str]:
    """对齐 Java ceshiend：子行→39；全部≥39 时主单→39。"""
    ids = _parse_ids(child_ids)
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_TESTING},
        to_status=ST_TEST_DONE,
        log_suffix="测试完成",
        staff_user_id=staff_user_id,
        bump_main="all_ge",
    )
    if not ok:
        return ok, msg
    for cid in ids:
        try:
            execute(
                """
                UPDATE experiment_log
                SET end_time = NOW(), status = 3
                WHERE order_child_id = %(cid)s
                  AND end_time IS NULL
                  AND IFNULL(deleteStatus, 0) = 0
                ORDER BY id DESC
                LIMIT 1
                """,
                {"cid": cid},
            )
        except Exception:
            try:
                execute(
                    """
                    UPDATE experiment_log
                    SET end_time = NOW()
                    WHERE order_child_id = %(cid)s AND end_time IS NULL
                    ORDER BY id DESC LIMIT 1
                    """,
                    {"cid": cid},
                )
            except Exception:
                pass
        # 释放平台占用
        try:
            crow = fetch_one(
                "SELECT line_id AS lineId FROM experiment_order_child WHERE id = %(id)s",
                {"id": cid},
            )
            lid = str((crow or {}).get("lineId") or "")
            if lid.isdigit():
                execute(
                    """
                    UPDATE experiment_line
                    SET run_num = GREATEST(IFNULL(run_num, 1) - 1, 0),
                        line_status = CASE
                            WHEN GREATEST(IFNULL(run_num, 1) - 1, 0) = 0 THEN 0
                            ELSE line_status
                        END
                    WHERE id = %(id)s
                    """,
                    {"id": int(lid)},
                )
        except Exception:
            pass
    return True, "操作成功"


@transaction.atomic
def sample_return(
    *,
    order_id: int,
    child_ids: Any,
    store_id: str = "",
    store_position_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java type=5 isPosition=1：归还须选择仓库位置并回写样品库。"""
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    sid = str(store_id or "").strip()
    spos = str(store_position_id or "").strip()
    if "_" in spos:
        parts = spos.split("_", 1)
        if parts[0] == "storePosId" and parts[1].isdigit():
            spos = parts[1]
    if not sid or not spos:
        return False, "请选择仓库位置"
    if len(ids) > 1:
        return False, "选择仓库位置时请只勾选一行"
    try:
        store_i = int(sid)
        pos_i = int(spos)
    except (TypeError, ValueError):
        return False, "仓库或仓位参数错误"
    store = fetch_one(
        """
        SELECT id, sample_store_name AS storeName
        FROM sample_goods_storehouse
        WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": store_i},
    )
    if not store:
        return False, "仓库不存在"
    pos = fetch_one(
        """
        SELECT
            t.id, t.goods_brand_id AS goodsBrandId, t.number,
            b.block AS blockName
        FROM sample_goods_store_position t
        LEFT JOIN sample_goods_store_block b ON t.sample_block_id = b.id
        WHERE t.id = %(id)s
          AND t.sample_store_id = %(sid)s
          AND IFNULL(t.deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": pos_i, "sid": store_i},
    )
    if not pos:
        return False, "仓库位置不存在"
    try:
        occupied = int(pos.get("goodsBrandId") or 0)
    except (TypeError, ValueError):
        occupied = 0
    if occupied:
        return False, "请确认样本仓库位置为空闲!"
    child = fetch_one(
        """
        SELECT
            id, order_id AS childOrderId, order_status AS orderStatus,
            goods_id AS goodsId, goods_name AS goodsName,
            goods_brand_id AS goodsBrandId, goods_brand_name AS goodsBrandName,
            goods_spec AS goodsSpec
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": ids[0]},
    )
    if not child:
        return False, "子单行不存在"
    slot = f"{pos.get('blockName') or ''}-{pos.get('number') or ''}".strip("-")
    store_name = str(store.get("storeName") or "")
    log_suffix = f"样品归还,仓库位置{store_name}; {slot}"
    # 占用仓位
    execute(
        """
        UPDATE sample_goods_store_position
        SET goods_brand_id = %(brand_id)s,
            goods_brand_name = %(brand_name)s,
            goods_spec = %(spec)s,
            goods_id = %(goods_id)s,
            position_status = 1,
            sample_name = %(sample_name)s
        WHERE id = %(id)s
        """,
        {
            "id": pos_i,
            "brand_id": child.get("goodsBrandId") or 0,
            "brand_name": str(child.get("goodsBrandName") or "")[:100],
            "spec": str(child.get("goodsSpec") or "")[:200],
            "goods_id": child.get("goodsId") or 0,
            "sample_name": str(child.get("goodsName") or "")[:200],
        },
    )
    gotc = _child_treasury(ids[0])
    if gotc:
        execute(
            """
            UPDATE exp_goods_out_treasury_child
            SET store_id = %(sid)s, store_position_id = %(pid)s, got_status = 1
            WHERE id = %(id)s
            """,
            {"sid": store_i, "pid": pos_i, "id": gotc["id"]},
        )
        out_id = gotc.get("outId")
    else:
        out_num = f"YP{datetime.now().strftime('%Y%m%d%H%M%S')}{ids[0]}"
        out_id = execute_insert(
            """
            INSERT INTO exp_goods_out_treasury
                (addTime, deleteStatus, out_num, order_id, store_id, status,
                 in_out_type, ftype, inTreasury_user, sj_out_time)
            VALUES
                (NOW(), 0, %(out_num)s, %(oid)s, %(store_id)s, 1,
                 1, 1, NULL, NOW())
            """,
            {"out_num": out_num, "oid": order_id, "store_id": store_i},
        )
        execute_insert(
            """
            INSERT INTO exp_goods_out_treasury_child
                (addTime, deleteStatus, out_id, order_child_id, goods_id, goods_name,
                 goods_brand_id, goods_brand_name, goods_spec, store_id,
                 store_position_id, got_status)
            VALUES
                (NOW(), 0, %(out_id)s, %(cid)s, %(goods_id)s, %(goods_name)s,
                 %(brand_id)s, %(brand_name)s, %(spec)s, %(store_id)s,
                 %(pos_id)s, 4)
            """,
            {
                "out_id": out_id,
                "cid": ids[0],
                "goods_id": child.get("goodsId") or 0,
                "goods_name": str(child.get("goodsName") or "")[:200],
                "brand_id": child.get("goodsBrandId") or 0,
                "brand_name": str(child.get("goodsBrandName") or "")[:100],
                "spec": str(child.get("goodsSpec") or "")[:200],
                "store_id": store_i,
                "pos_id": pos_i,
            },
        )
    try:
        execute(
            """
            INSERT INTO exp_outin_depot_log
                (addTime, deleteStatus, of_id, log_info, store_id, store_position_id)
            VALUES
                (NOW(), 0, %(of_id)s, %(info)s, %(store_id)s, %(pos_id)s)
            """,
            {
                "of_id": out_id,
                "info": log_suffix[:500],
                "store_id": store_i,
                "pos_id": pos_i,
            },
        )
    except Exception:
        pass
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_TEST_DONE},
        to_status=ST_RETURN,
        log_suffix=log_suffix,
        staff_user_id=staff_user_id,
    )
    return (True, "样品归还成功！") if ok else (ok, msg)


@transaction.atomic
def sample_ship_back(
    *,
    order_id: int,
    child_ids: Any,
    express_no: str = "",
    express_name: str = "",
    store_position_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """对齐 Java addExpress：子行→50(已完成)，清空仓位；全部完成后主单→50。"""
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    if len(ids) != 1:
        return False, "样品寄回请只勾选一行"
    no = (express_no or "").strip()
    name = (express_name or "").strip()
    spos = str(store_position_id or "").strip()
    cid = ids[0]
    gotc = _child_treasury(cid)
    if gotc and gotc.get("storePosId") not in (None, "", 0, "0"):
        confirm = spos or str(gotc.get("storePosId"))
        if str(gotc.get("storePosId")) != str(confirm):
            return False, "样本仓库位置不正确!"
        spos = confirm
    extra_parts = [", is_sure = 1", ", in_status = 1"]
    params: dict[str, Any] = {}
    if no:
        extra_parts.append(", expressNo = %(eno)s")
        params["eno"] = no[:80]
    if name:
        extra_parts.append(", express_name = %(ename)s")
        params["ename"] = name[:80]
    log_suffix = "样品寄回"
    if name or no:
        log_suffix = f"样品寄回,{name} 物流单号为：{no}".strip(" ,")
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_RETURN},
        to_status=ST_DONE,
        log_suffix=log_suffix,
        extra_sql="".join(extra_parts),
        extra_params=params or None,
        staff_user_id=staff_user_id,
        bump_main="done",
    )
    if not ok:
        return ok, msg
    if gotc:
        try:
            pos_id = int(gotc.get("storePosId") or 0)
        except (TypeError, ValueError):
            pos_id = 0
        if pos_id:
            _clear_store_position(pos_id)
        try:
            execute(
                """
                UPDATE exp_goods_out_treasury_child
                SET store_id = NULL, store_position_id = NULL, got_status = 3
                WHERE id = %(id)s
                """,
                {"id": gotc["id"]},
            )
        except Exception:
            pass
        try:
            execute(
                """
                INSERT INTO exp_outin_depot_log
                    (addTime, deleteStatus, of_id, log_info)
                VALUES (NOW(), 0, %(of_id)s, '样品寄回')
                """,
                {"of_id": gotc.get("outId")},
            )
        except Exception:
            pass
    return True, "样品寄回成功！"


@transaction.atomic
def sample_retain(
    *,
    order_id: int,
    child_ids: Any,
    scrap: bool = False,
    is_position: str | int = "0",
    store_pos_id: str = "",
    new_store_pos_id: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    """
    对齐 Java inTreasury/saveInTreasury type=3/4：
    - 报废：清空仓位，子行→50
    - 留存：清空原样品库仓位；isPosition=1 时写入留存库 newStorePosId(position_status=2)
    - 全部子行完成后主单→50
    """
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    if len(ids) != 1:
        return False, "样品留存/报废请只勾选一行"
    cid = ids[0]
    child = fetch_one(
        """
        SELECT
            id, order_id AS childOrderId, order_status AS orderStatus,
            goods_id AS goodsId, goods_name AS goodsName,
            goods_brand_id AS goodsBrandId, goods_brand_name AS goodsBrandName,
            goods_spec AS goodsSpec
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": cid},
    )
    if not child:
        return False, "子单行不存在"
    try:
        cst = int(child.get("orderStatus") or -1)
    except (TypeError, ValueError):
        cst = -1
    if cst != ST_RETURN:
        return False, "仅样品归还状态可留存/报废"

    gotc = _child_treasury(cid)
    old_pos = str(store_pos_id or "").strip()
    if gotc and gotc.get("storePosId") not in (None, "", 0, "0"):
        confirm_old = old_pos or str(gotc.get("storePosId"))
        if str(gotc.get("storePosId")) != str(confirm_old):
            return False, "样本仓库位置不正确!"
        old_pos = confirm_old

    label = "样品报废" if scrap else "样品留存"
    loginfo = ""
    need_pos = str(is_position or "0").strip() in ("1", "true", "True")
    new_pos_row: dict[str, Any] | None = None
    new_pos_i = 0

    if not scrap and need_pos:
        new_pos = str(new_store_pos_id or "").strip()
        if "_" in new_pos:
            new_pos = new_pos.split("_", 1)[-1].strip()
        if not new_pos.isdigit():
            return False, "请选择留存仓库位置"
        new_pos_i = int(new_pos)
        new_pos_row = fetch_one(
            """
            SELECT
                t.id, t.sample_store_id AS storeId, t.goods_brand_id AS goodsBrandId,
                t.number, b.block AS blockName, s.sample_store_name AS storeName, s.type AS storeType
            FROM sample_goods_store_position t
            LEFT JOIN sample_goods_store_block b ON t.sample_block_id = b.id
            LEFT JOIN sample_goods_storehouse s ON t.sample_store_id = s.id
            WHERE t.id = %(id)s AND IFNULL(t.deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": new_pos_i},
        )
        if not new_pos_row:
            return False, "留存仓库位置不存在"
        try:
            stype = int(new_pos_row.get("storeType") or 0)
        except (TypeError, ValueError):
            stype = 0
        if stype == 1:
            return False, "请选择样品留存仓库位置"
        try:
            occupied = int(new_pos_row.get("goodsBrandId") or 0)
        except (TypeError, ValueError):
            occupied = 0
        if occupied:
            return False, "请确认留存仓库位置为空闲!"

    if scrap:
        if old_pos.isdigit():
            _clear_store_position(int(old_pos))
        if gotc:
            try:
                execute(
                    """
                    UPDATE exp_goods_out_treasury_child
                    SET store_id = NULL, store_position_id = NULL, got_status = 5
                    WHERE id = %(id)s
                    """,
                    {"id": gotc["id"]},
                )
            except Exception:
                pass
            try:
                execute(
                    """
                    INSERT INTO exp_outin_depot_log
                        (addTime, deleteStatus, of_id, log_info)
                    VALUES (NOW(), 0, %(of_id)s, '样品报废')
                    """,
                    {"of_id": gotc.get("outId")},
                )
            except Exception:
                pass
        log_suffix = "样品报废"
    else:
        # 先清原样品库仓位
        if old_pos.isdigit():
            _clear_store_position(int(old_pos))
        if gotc:
            try:
                execute(
                    """
                    UPDATE exp_goods_out_treasury_child
                    SET store_id = NULL, store_position_id = NULL, got_status = 2
                    WHERE id = %(id)s
                    """,
                    {"id": gotc["id"]},
                )
            except Exception:
                pass
        if need_pos and new_pos_row:
            pos = new_pos_row
            pos_i = new_pos_i
            store_i = int(pos.get("storeId") or 0)
            slot = f"{pos.get('blockName') or ''}-{pos.get('number') or ''}".strip("-")
            store_name = str(pos.get("storeName") or "")
            loginfo = f",仓库位置{store_name}; {slot}"
            execute(
                """
                UPDATE sample_goods_store_position
                SET goods_brand_id = %(brand_id)s,
                    goods_brand_name = %(brand_name)s,
                    goods_spec = %(spec)s,
                    goods_id = %(goods_id)s,
                    position_status = 2,
                    sample_name = %(sample_name)s
                WHERE id = %(id)s
                """,
                {
                    "id": pos_i,
                    "brand_id": child.get("goodsBrandId") or 0,
                    "brand_name": str(child.get("goodsBrandName") or "")[:100],
                    "spec": str(child.get("goodsSpec") or "")[:200],
                    "goods_id": child.get("goodsId") or 0,
                    "sample_name": str(child.get("goodsName") or "")[:200],
                },
            )
            out_id = gotc.get("outId") if gotc else None
            if gotc:
                execute(
                    """
                    UPDATE exp_goods_out_treasury_child
                    SET store_id = %(sid)s, store_position_id = %(pid)s, got_status = 4
                    WHERE id = %(id)s
                    """,
                    {"sid": store_i, "pid": pos_i, "id": gotc["id"]},
                )
            else:
                out_num = f"YP{datetime.now().strftime('%Y%m%d%H%M%S')}{cid}"
                out_id = execute_insert(
                    """
                    INSERT INTO exp_goods_out_treasury
                        (addTime, deleteStatus, out_num, order_id, store_id, status,
                         in_out_type, ftype, inTreasury_user, sj_out_time)
                    VALUES
                        (NOW(), 0, %(out_num)s, %(oid)s, %(store_id)s, 1,
                         1, 1, NULL, NOW())
                    """,
                    {"out_num": out_num, "oid": order_id, "store_id": store_i},
                )
                execute_insert(
                    """
                    INSERT INTO exp_goods_out_treasury_child
                        (addTime, deleteStatus, out_id, order_child_id, goods_id, goods_name,
                         goods_brand_id, goods_brand_name, goods_spec, store_id,
                         store_position_id, got_status)
                    VALUES
                        (NOW(), 0, %(out_id)s, %(cid)s, %(goods_id)s, %(goods_name)s,
                         %(brand_id)s, %(brand_name)s, %(spec)s, %(store_id)s,
                         %(pos_id)s, 4)
                    """,
                    {
                        "out_id": out_id,
                        "cid": cid,
                        "goods_id": child.get("goodsId") or 0,
                        "goods_name": str(child.get("goodsName") or "")[:200],
                        "brand_id": child.get("goodsBrandId") or 0,
                        "brand_name": str(child.get("goodsBrandName") or "")[:100],
                        "spec": str(child.get("goodsSpec") or "")[:200],
                        "store_id": store_i,
                        "pos_id": pos_i,
                    },
                )
            try:
                execute(
                    """
                    INSERT INTO exp_outin_depot_log
                        (addTime, deleteStatus, of_id, log_info, store_id, store_position_id)
                    VALUES
                        (NOW(), 0, %(of_id)s, %(info)s, %(store_id)s, %(pos_id)s)
                    """,
                    {
                        "of_id": out_id,
                        "info": f"样品留存{loginfo}"[:500],
                        "store_id": store_i,
                        "pos_id": pos_i,
                    },
                )
            except Exception:
                pass
            log_suffix = f"样品留存{loginfo}"
        else:
            if gotc:
                try:
                    execute(
                        """
                        INSERT INTO exp_outin_depot_log
                            (addTime, deleteStatus, of_id, log_info)
                        VALUES (NOW(), 0, %(of_id)s, '样品留存, 仓库位置无')
                        """,
                        {"of_id": gotc.get("outId")},
                    )
                except Exception:
                    pass
            log_suffix = "样品留存, 仓库位置无"

    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_RETURN},
        to_status=ST_DONE,
        log_suffix=log_suffix,
        extra_sql=", is_sure = 1, in_status = 1",
        staff_user_id=staff_user_id,
        bump_main="done",
    )
    if not ok:
        return ok, msg
    return True, f"{label}成功"


@transaction.atomic
def add_video_meeting(
    *,
    order_id: int,
    child_ids: Any,
    meeting_num: str,
    setting_time: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    ids = _parse_ids(child_ids)
    num = (meeting_num or "").strip()
    if not num:
        return False, "请填写会议号"
    if not ids:
        return False, "请选择子单行"
    ok_n = 0
    stime = (setting_time or "").strip()[:19]
    for cid in ids:
        n = execute(
            """
            UPDATE experiment_order_child
            SET is_meeting = 1, meeting_num = %(num)s
            WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
            """,
            {"num": num[:100], "id": cid},
        )
        if n:
            try:
                execute_insert(
                    """
                    INSERT INTO experiment_video
                        (addTime, deleteStatus, child_id, meeting_num, setting_time)
                    VALUES (NOW(), 0, %(cid)s, %(num)s, NULLIF(%(st)s, ''))
                    """,
                    {"cid": cid, "num": num[:100], "st": stime},
                )
            except Exception:
                try:
                    execute_insert(
                        """
                        INSERT INTO experiment_video (addTime, deleteStatus, child_id, meeting_num)
                        VALUES (NOW(), 0, %(cid)s, %(num)s)
                        """,
                        {"cid": cid, "num": num[:100]},
                    )
                except Exception:
                    pass
            _write_log(
                order_id,
                f"预约云视频 会议号:{num} child={cid}",
                user_id=staff_user_id,
            )
            ok_n += 1
    if ok_n <= 0:
        return False, "操作失败"
    return True, "预约成功"


@transaction.atomic
def confirm_children(
    *,
    order_id: int,
    child_ids: Any,
    mark: str = "",
    staff_user_id: str | int | None = None,
) -> tuple[bool, str]:
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择要确认的子单行"
    # 对齐 Java confirm.ajax：备注必填
    if not str(mark or "").strip():
        return False, "请填写确认备注"
    ok_n = 0
    for cid in ids:
        child = fetch_one(
            """
            SELECT id, order_id AS childOrderId, order_status AS orderStatus, is_confirm AS isConfirm
            FROM experiment_order_child WHERE id = %(id)s LIMIT 1
            """,
            {"id": cid},
        )
        if not child:
            continue
        try:
            cst = int(child.get("orderStatus") or 0)
            conf = int(child.get("isConfirm") or 0)
        except (TypeError, ValueError):
            continue
        if cst < ST_TEST_DONE or conf == 1:
            continue
        execute(
            """
            UPDATE experiment_order_child
            SET is_confirm = 1, mark = %(mark)s
            WHERE id = %(id)s
            """,
            {"mark": (mark or "")[:500], "id": cid},
        )
        _write_log(
            order_id,
            f"{child.get('childOrderId') or cid}用户确认",
            user_id=staff_user_id,
        )
        ok_n += 1
    if ok_n <= 0:
        return False, "没有可确认的子单行"
    # 全部确认则主单 is_confirm=1（不等于已完成）
    children = list_children_for_order(order_id)
    if children and all(int(c.get("isConfirm") or 0) == 1 for c in children):
        try:
            execute(
                "UPDATE experiment_order SET is_confirm = 1, finishTime = NOW() WHERE id = %(id)s",
                {"id": order_id},
            )
        except Exception:
            execute(
                "UPDATE experiment_order SET is_confirm = 1 WHERE id = %(id)s",
                {"id": order_id},
            )
    return True, "确认成功"


@transaction.atomic
def retest_apply(*, order_id: int, child_ids: Any) -> tuple[bool, str]:
    """
    对齐 Java agreeretestapplication：
    - 样品归还(41) → 样品到货(36)，下一步样品领用
    - 测试完成(39) → 样品领用(37)，下一步开始测试
    """
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    ok_n = 0
    for cid in ids:
        child = fetch_one(
            """
            SELECT id, order_id AS childOrderId, order_status AS orderStatus
            FROM experiment_order_child
            WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
            LIMIT 1
            """,
            {"id": cid},
        )
        if not child:
            continue
        try:
            cst = int(child.get("orderStatus") or -1)
        except (TypeError, ValueError):
            continue
        if cst == ST_RETURN:
            to_st = ST_ARRIVE
            label = "样品复测-回到样品到货"
        elif cst == ST_TEST_DONE:
            to_st = ST_PICK
            label = "样品复测-回到样品领用"
        else:
            continue
        n = execute(
            "UPDATE experiment_order_child SET order_status = %(st)s WHERE id = %(id)s",
            {"st": to_st, "id": cid},
        )
        if n:
            _write_log(order_id, f"{child.get('childOrderId') or cid}{label}")
            ok_n += 1
            # 主单状态回落到复测后应有的节点
            execute(
                """
                UPDATE experiment_order
                SET order_status = %(st)s
                WHERE id = %(id)s AND IFNULL(order_status, 0) > %(st)s
                """,
                {"st": to_st, "id": order_id},
            )
    if ok_n <= 0:
        return False, "没有可复测的子单行（需测试完成或样品归还）"
    return True, "复测成功"
