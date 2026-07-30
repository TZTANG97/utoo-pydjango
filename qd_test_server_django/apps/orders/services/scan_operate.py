"""小程序扫码操作 — 对齐 Java WxController.scanCodeOperate / isFlag / confirmsave。"""
from __future__ import annotations

from typing import Any

from apps.admin_experiment.repositories import sample_flow as flow
from apps.core.db_utils import execute, fetch_one


def _parse_token(raw: Any, *, prefixes: tuple[str, ...] = ()) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    # 仓位二维码：id;name;pos
    if ";" in text:
        text = text.split(";", 1)[0].strip()
    for p in prefixes:
        if text.startswith(p):
            return text[len(p) :].strip()
    if "_" in text:
        head, tail = text.split("_", 1)
        if head.lower() in {x.rstrip("_").lower() for x in prefixes} or not head.isdigit():
            return tail.strip()
    return text


def _parse_child_id(raw: Any) -> int:
    token = _parse_token(raw, prefixes=("childId_", "childid_"))
    try:
        return int(token)
    except (TypeError, ValueError):
        return 0


def _parse_pos_id(raw: Any) -> str:
    return _parse_token(raw, prefixes=("storePosId_", "newStorePosId_", "storeposid_"))


def _parse_line_id(raw: Any) -> str:
    return _parse_token(raw, prefixes=("lineId_", "lineid_"))


def _resolve_child(child_id: int) -> tuple[dict[str, Any] | None, int]:
    """返回 (child_row, purchase_order_pk type=9/10)。"""
    if child_id <= 0:
        return None, 0
    child = fetch_one(
        """
        SELECT
            id, order_id AS childOrderId, order_status AS orderStatus,
            order_form_id AS ofId, is_confirm AS isConfirm,
            is_meeting AS isMeeting, is_sure AS isSure
        FROM experiment_order_child
        WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": child_id},
    )
    if not child:
        return None, 0

    def _ok_purchase(oid: int) -> int:
        if oid <= 0:
            return 0
        row = fetch_one(
            """
            SELECT id, order_type AS orderType
            FROM experiment_order
            WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"id": oid},
        )
        if row and str(row.get("orderType") or "") in ("9", "10"):
            return int(row["id"])
        return 0

    # 优先采购关联表（小程序扫码挂在子订单/分包子订单上）
    link = fetch_one(
        """
        SELECT purchase_order_id AS oid
        FROM exp_qd_purchase_order_child
        WHERE order_child_id = %(cid)s
        LIMIT 1
        """,
        {"cid": child_id},
    )
    if link and link.get("oid"):
        oid = _ok_purchase(int(link["oid"]))
        if oid:
            return child, oid

    of_id = child.get("ofId")
    try:
        of_i = int(of_id or 0)
    except (TypeError, ValueError):
        of_i = 0
    oid = _ok_purchase(of_i)
    if oid:
        return child, oid
    return child, 0


def _parent_ok(order_id: int) -> tuple[bool, str]:
    row = fetch_one(
        """
        SELECT id, order_status AS orderStatus, order_type AS orderType,
               is_online AS isOnline, reverso_context AS reversoContext
        FROM experiment_order
        WHERE id = %(id)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": order_id},
    )
    if not row:
        return False, "订单不存在"
    try:
        st = int(row.get("orderStatus") or 0)
    except (TypeError, ValueError):
        st = 0
    if st < 30:
        return False, "订单未审核，不可操作"
    if str(row.get("orderType") or "") not in ("9", "10"):
        return False, "仅实验子订单/分包子订单支持扫码操作"
    return True, ""


def _already_msg(status: int, op_type: str) -> str:
    labels = {
        "1": "样品已入库",
        "2": "样品已领用",
        "3": "已开始测试",
        "4": "已测试完成",
        "5": "样品已归还",
        "6": "样品已寄回",
        "7": "样品已留存/报废",
    }
    # 粗略：状态已超过该操作期望源状态
    return labels.get(op_type, "当前状态不可操作")


def scan_code_operate(
    *,
    type: str | int,
    child_id: Any,
    store_pos_id: Any = "",
    new_store_pos_id: Any = "",
    is_position: Any = "0",
    line_id: Any = "",
    express_no: str = "",
    express_name: str = "",
    meeting_num: str = "",
    setting_time: str = "",
    finish_time: Any = "",
    time_type: Any = "",
    key: Any = "1",
) -> tuple[bool, str]:
    """对齐 Java /wx/scanCodeOperate.ajax；type=1..7。"""
    op = str(type or "").strip()
    cid = _parse_child_id(child_id)
    if not cid:
        return False, "请扫描样品二维码"
    child, order_id = _resolve_child(cid)
    if not child or not order_id:
        return False, "子订单不存在"
    ok_p, msg_p = _parent_ok(order_id)
    if not ok_p:
        return False, msg_p

    try:
        cst = int(child.get("orderStatus") or -1)
    except (TypeError, ValueError):
        cst = -1

    pos = _parse_pos_id(store_pos_id) if str(is_position) in ("1", "true", "True") or store_pos_id else ""
    if str(is_position) in ("0", "false", "False", "") and not store_pos_id:
        pos = ""
    elif store_pos_id and not pos:
        pos = _parse_pos_id(store_pos_id)

    # 无 isPosition 时若传了 storePosId 仍尝试用仓位
    if not pos and store_pos_id:
        pos = _parse_pos_id(store_pos_id)

    use_pos = str(is_position) in ("1", "true", "True") or bool(pos)

    if op == "1":
        if cst not in (0, 1, 2, flow.ST_PROCESSED):
            return False, _already_msg(cst, op)
        return flow.sample_arrive(
            order_id=order_id,
            child_ids=[cid],
            store_id="",
            store_position_id=pos if use_pos else "",
        )

    if op == "2":
        if cst != flow.ST_ARRIVE:
            return False, _already_msg(cst, op)
        meeting = (meeting_num or "").strip()
        if meeting:
            flow.add_video_meeting(order_id=order_id, child_ids=[cid], meeting_num=meeting)
        ok, msg = flow.sample_pick(order_id=order_id, child_ids=[cid])
        if ok and (finish_time not in (None, "") or time_type not in (None, "")):
            try:
                execute(
                    """
                    UPDATE experiment_order_child
                    SET finish_time = IFNULL(%(ft)s, finish_time),
                        time_type = IFNULL(%(tt)s, time_type)
                    WHERE id = %(id)s
                    """,
                    {
                        "id": cid,
                        "ft": finish_time if finish_time not in (None, "") else None,
                        "tt": time_type if time_type not in (None, "") else None,
                    },
                )
            except Exception:
                pass
        return ok, msg if ok else msg

    if op == "3":
        if cst != flow.ST_PICK:
            return False, _already_msg(cst, op)
        lid = _parse_line_id(line_id)
        return flow.test_start(order_id=order_id, child_ids=[cid], line_id=lid)

    if op == "4":
        if cst != flow.ST_TESTING:
            return False, _already_msg(cst, op)
        return flow.test_end(order_id=order_id, child_ids=[cid])

    if op == "5":
        if cst != flow.ST_TEST_DONE:
            return False, _already_msg(cst, op)
        return flow.sample_return(order_id=order_id, child_ids=[cid])

    if op == "6":
        if cst != flow.ST_RETURN:
            return False, _already_msg(cst, op)
        if not str(express_no or "").strip():
            return False, "请输入快递单号"
        if not str(express_name or "").strip():
            return False, "请输入快递公司名称"
        return flow.sample_ship_back(
            order_id=order_id,
            child_ids=[cid],
            express_no=str(express_no or ""),
            express_name=str(express_name or ""),
        )

    if op == "7":
        if cst != flow.ST_RETURN:
            return False, _already_msg(cst, op)
        scrap = str(key or "1").strip() == "2"
        return flow.sample_retain(order_id=order_id, child_ids=[cid], scrap=scrap)

    return False, "不支持的操作类型"


def is_flag(*, child_id: Any) -> tuple[bool, str]:
    """对齐 Java /wx/isFlag.ajax：测试完成且未确认。"""
    cid = _parse_child_id(child_id)
    if not cid:
        # isFlag 常传纯数字
        try:
            cid = int(str(child_id).strip())
        except (TypeError, ValueError):
            cid = 0
    if not cid:
        return False, "参数错误"
    child, order_id = _resolve_child(cid)
    if not child:
        return False, "子订单不存在"
    if order_id:
        ok_p, msg_p = _parent_ok(order_id)
        if not ok_p:
            return False, msg_p
    try:
        st = int(child.get("orderStatus") or 0)
        conf = int(child.get("isConfirm") or 0)
    except (TypeError, ValueError):
        return False, "状态异常"
    if st < flow.ST_TEST_DONE:
        return False, "测试尚未完成，不可确认"
    if conf == 1:
        return False, "该子订单已确认!"
    return True, "有确认权限!"


def confirm_save(
    *,
    child_id: Any,
    mark: str = "",
    accessory_ids: Any = "",
) -> tuple[bool, str]:
    """对齐 Java experimentChildOrder/confirmsave.ajax。"""
    cid = _parse_child_id(child_id)
    if not cid:
        try:
            cid = int(str(child_id).strip())
        except (TypeError, ValueError):
            cid = 0
    if not cid:
        return False, "参数错误"
    child, order_id = _resolve_child(cid)
    if not child or not order_id:
        return False, "子订单不存在"
    note = (mark or "").strip() or "用户确认"
    # 挂附件
    ids = flow._parse_ids(accessory_ids)
    for aid in ids:
        try:
            execute(
                """
                UPDATE accessory
                SET child_of_id = %(cid)s
                WHERE id = %(id)s
                """,
                {"cid": cid, "id": aid},
            )
        except Exception:
            try:
                execute(
                    """
                    UPDATE accessory
                    SET child_of_id = %(cid)s
                    WHERE id = %(id)s
                    """,
                    {"cid": cid, "id": aid},
                )
            except Exception:
                pass
    ok, msg = flow.confirm_children(order_id=order_id, child_ids=[cid], mark=note)
    if ok:
        return True, "确认成功！"
    return False, msg
