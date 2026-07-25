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
ST_SHIP_BACK = 42
ST_RETAIN = 43
ST_SCRAP = 44

ACTION_LABEL = {
    ST_ARRIVE: "样品到货",
    ST_PICK: "样品领用",
    ST_TESTING: "开始测试",
    ST_TEST_DONE: "测试完成",
    ST_RETURN: "样品归还",
    ST_SHIP_BACK: "样品寄回",
    ST_RETAIN: "样品留存",
    ST_SCRAP: "样品报废",
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


def _write_log(order_id: int, info: str) -> None:
    try:
        execute(
            """
            INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info)
            VALUES (NOW(), 0, %(oid)s, %(info)s)
            """,
            {"oid": order_id, "info": (info or "")[:500]},
        )
    except Exception:
        execute(
            """
            INSERT INTO experiment_order_log (addTime, deleteStatus, of_id, log_info)
            VALUES (NOW(), 0, %(oid)s, %(info)s)
            """,
            {"oid": order_id, "info": (info or "")[:500]},
        )


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
) -> tuple[bool, str]:
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
        # 归属校验：直连或采购关联
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
        _write_log(order_id, f"{child.get('childOrderId') or cid}{log_suffix}")
        ok_n += 1
    if ok_n <= 0:
        return False, "没有可操作的子单行（状态不符或不属于本单）"
    _bump_main_status(order_id, to_status)
    return True, "操作成功"


@transaction.atomic
def sample_arrive(
    *,
    order_id: int,
    child_ids: Any,
    store_id: str = "",
    store_position_id: str = "",
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
    )
    if ok and sid and spos:
        return True, "样品入库成功！"
    return ok, msg


@transaction.atomic
def sample_pick(*, order_id: int, child_ids: Any) -> tuple[bool, str]:
    """对齐 Java：若订单开启云视频，领用前须已预约会议。"""
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
    if is_video == 1:
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
            try:
                meet = int(child.get("isMeeting") or 0)
            except (TypeError, ValueError):
                meet = 0
            if meet != 1:
                return False, f"子单 {child.get('childOrderId') or cid} 请先预约云视频"
    return _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_ARRIVE},
        to_status=ST_PICK,
        log_suffix="样品领用",
    )


@transaction.atomic
def test_start(*, order_id: int, child_ids: Any, line_id: str = "") -> tuple[bool, str]:
    lid = str(line_id or "").strip()
    if "_" in lid:
        lid = lid.split("_", 1)[-1].strip()
    extra = ""
    params: dict[str, Any] = {}
    if lid:
        extra = ", line_id = %(line_id)s"
        params["line_id"] = lid[:64]
    return _set_children_status(
        order_id=order_id,
        child_ids=_parse_ids(child_ids),
        expect_from={ST_PICK},
        to_status=ST_TESTING,
        log_suffix="开始测试",
        extra_sql=extra,
        extra_params=params or None,
    )


@transaction.atomic
def test_end(*, order_id: int, child_ids: Any) -> tuple[bool, str]:
    return _set_children_status(
        order_id=order_id,
        child_ids=_parse_ids(child_ids),
        expect_from={ST_TESTING},
        to_status=ST_TEST_DONE,
        log_suffix="测试完成",
    )


@transaction.atomic
def sample_return(*, order_id: int, child_ids: Any) -> tuple[bool, str]:
    return _set_children_status(
        order_id=order_id,
        child_ids=_parse_ids(child_ids),
        expect_from={ST_TEST_DONE},
        to_status=ST_RETURN,
        log_suffix="样品归还",
    )


@transaction.atomic
def sample_ship_back(
    *,
    order_id: int,
    child_ids: Any,
    express_no: str = "",
    express_name: str = "",
) -> tuple[bool, str]:
    extra = ""
    params: dict[str, Any] = {}
    no = (express_no or "").strip()
    name = (express_name or "").strip()
    if no or name:
        tag = f"[快递:{name} {no}]".strip()
        extra = ", mark = CONCAT(IFNULL(mark,''), %(ex)s)"
        params["ex"] = tag
    return _set_children_status(
        order_id=order_id,
        child_ids=_parse_ids(child_ids),
        expect_from={ST_RETURN},
        to_status=ST_SHIP_BACK,
        log_suffix="样品寄回",
        extra_sql=extra,
        extra_params=params or None,
    )


@transaction.atomic
def sample_retain(*, order_id: int, child_ids: Any, scrap: bool = False) -> tuple[bool, str]:
    to_st = ST_SCRAP if scrap else ST_RETAIN
    label = "样品报废" if scrap else "样品留存"
    return _set_children_status(
        order_id=order_id,
        child_ids=_parse_ids(child_ids),
        expect_from={ST_RETURN},
        to_status=to_st,
        log_suffix=label,
    )


@transaction.atomic
def add_video_meeting(*, order_id: int, child_ids: Any, meeting_num: str) -> tuple[bool, str]:
    ids = _parse_ids(child_ids)
    num = (meeting_num or "").strip()
    if not num:
        return False, "请填写会议号"
    if not ids:
        return False, "请选择子单行"
    ok_n = 0
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
            _write_log(order_id, f"预约云视频 会议号:{num} child={cid}")
            ok_n += 1
    if ok_n <= 0:
        return False, "操作失败"
    return True, "预约成功"


@transaction.atomic
def confirm_children(*, order_id: int, child_ids: Any, mark: str = "") -> tuple[bool, str]:
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
        _write_log(order_id, f"{child.get('childOrderId') or cid}用户确认")
        ok_n += 1
    if ok_n <= 0:
        return False, "没有可确认的子单行"
    # 全部确认则主单 is_confirm=1
    children = list_children_for_order(order_id)
    if children and all(int(c.get("isConfirm") or 0) == 1 for c in children):
        execute(
            "UPDATE experiment_order SET is_confirm = 1, finishTime = NOW() WHERE id = %(id)s",
            {"id": order_id},
        )
    return True, "确认成功"


@transaction.atomic
def retest_apply(*, order_id: int, child_ids: Any) -> tuple[bool, str]:
    """简化：记录日志并将选中行回到测试中，便于复测流程。"""
    ids = _parse_ids(child_ids)
    if not ids:
        return False, "请选择子单行"
    ok, msg = _set_children_status(
        order_id=order_id,
        child_ids=ids,
        expect_from={ST_TEST_DONE, ST_RETURN},
        to_status=ST_TESTING,
        log_suffix="样品复测-重新测试",
    )
    return ok, msg if ok else msg
