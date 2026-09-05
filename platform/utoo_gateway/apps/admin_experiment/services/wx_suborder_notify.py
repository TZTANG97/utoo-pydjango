"""实验子订单详情相关微信模板通知（对齐 ExperimentSubOrderController）。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from apps.admin_experiment.services import wx_template as wx
from apps.core.db_utils import fetch_one

logger = logging.getLogger(__name__)

CHILD_DETAIL = (
    "/staffB/judge_user/judge_user?package_name=staff&path_name=child_detail&id="
)
ORDER_DETAIL = (
    "/staffB/judge_user/judge_user?package_name=pagesB&path_name=order_detail&id="
)
TEST_ORDER_DETAIL = "test/test_order_detail/test_order_detail?id="
PAY_DETAIL = (
    "pageB/check_pending_test_sub_child_order_detail/"
    "check_pending_test_sub_child_order_detail?flag=1&id="
)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _staff_true_name(user_id: str | int | None) -> str:
    uid = str(user_id or "").strip()
    if not uid:
        return ""
    row = fetch_one(
        """
        SELECT true_name AS trueName, user_name AS userName
        FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1
        """,
        {"id": uid},
    )
    if not row:
        return ""
    return str(row.get("trueName") or row.get("userName") or "")


def _staff_utgzh(user_id: str | int | None) -> str:
    uid = str(user_id or "").strip()
    if not uid:
        return ""
    row = fetch_one(
        """
        SELECT utgzh_openid AS openid
        FROM sy_users WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR) LIMIT 1
        """,
        {"id": uid},
    )
    return str((row or {}).get("openid") or "").strip()


def _load_order_ctx(order_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            t.id, t.order_id AS orderId, t.order_type AS orderType,
            t.parent_id AS parentId, t.totalPrice AS totalPrice,
            t.add_user_id AS addUserId,
            t.sale_manager AS saleManagerId,
            t.test_manager AS testManagerId,
            t.customer_name AS customerId,
            t.custom_user_id AS customUserId,
            p.order_type AS parentOrderType,
            p.custom_user_id AS parentCustomUserId,
            p.customer_name AS parentCustomerId
        FROM experiment_order t
        LEFT JOIN experiment_order p ON t.parent_id = p.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": order_id},
    )


def _customer_by_id(user_id: Any) -> dict[str, Any] | None:
    uid = str(user_id or "").strip()
    if not uid:
        return None
    row = fetch_one(
        """
        SELECT id, mobile, trueName, wx_openid AS wxOpenid,
               IFNULL(is_accept_message, 0) AS isAcceptMessage
        FROM exp_user
        WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR)
        LIMIT 1
        """,
        {"id": uid},
    )
    if row:
        return row
    return fetch_one(
        """
        SELECT id, mobile, trueName, wx_openid AS wxOpenid, 0 AS isAcceptMessage
        FROM `user`
        WHERE CAST(id AS CHAR) = CAST(%(id)s AS CHAR)
        LIMIT 1
        """,
        {"id": uid},
    )


def _customer_by_mobile(mobile: str) -> dict[str, Any] | None:
    m = (mobile or "").strip()
    if not m:
        return None
    row = fetch_one(
        """
        SELECT id, mobile, trueName, wx_openid AS wxOpenid,
               IFNULL(is_accept_message, 0) AS isAcceptMessage
        FROM exp_user WHERE mobile = %(m)s LIMIT 1
        """,
        {"m": m},
    )
    if row:
        return row
    return fetch_one(
        """
        SELECT id, mobile, trueName, wx_openid AS wxOpenid, 0 AS isAcceptMessage
        FROM `user` WHERE mobile = %(m)s LIMIT 1
        """,
        {"m": m},
    )


def _company(company_id: Any) -> dict[str, Any] | None:
    cid = str(company_id or "").strip()
    if not cid or not cid.isdigit():
        return None
    return fetch_one(
        """
        SELECT id, name, contract_phone AS contractPhone
        FROM qd_user_company WHERE id = %(id)s LIMIT 1
        """,
        {"id": int(cid)},
    )


def _accepts_message(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    try:
        return int(user.get("isAcceptMessage") or 0) == 0
    except (TypeError, ValueError):
        return True


def _resolve_customer_openid(ctx: dict[str, Any]) -> tuple[str, str]:
    """
    返回 (openid, hint)。
    优先父单/本单 custom_user；否则公司联系人手机号对应用户。
    """
    custom_id = ctx.get("parentCustomUserId") or ctx.get("customUserId")
    user = _customer_by_id(custom_id)
    if user and _accepts_message(user):
        return str(user.get("wxOpenid") or "").strip(), "custom"
    company = _company(ctx.get("parentCustomerId") or ctx.get("customerId"))
    if company:
        cu = _customer_by_mobile(str(company.get("contractPhone") or ""))
        if cu and _accepts_message(cu):
            return str(cu.get("wxOpenid") or "").strip(), "company"
        # Java 公司分支部分场景未校验 is_accept_message，仍取 openid
        if cu:
            return str(cu.get("wxOpenid") or "").strip(), "company"
    return "", ""


def _manager_openid(ctx: dict[str, Any]) -> str:
    ot = str(ctx.get("orderType") or "")
    if ot == "10":
        return _staff_utgzh(ctx.get("saleManagerId"))
    if ot == "9":
        return _staff_utgzh(ctx.get("testManagerId"))
    return ""


def _amount_str(val: Any) -> str:
    if val is None:
        return "0"
    try:
        return format(val, "f").rstrip("0").rstrip(".") if hasattr(val, "as_tuple") else str(val)
    except Exception:
        return str(val)


def notify_audit_result(
    *,
    order_id: int,
    passed: bool,
    staff_user_id: str | int | None = None,
) -> None:
    """审核通过/驳回 → 制单员 utgzh。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        openid = _staff_utgzh(ctx.get("addUserId"))
        auditor = _staff_true_name(staff_user_id) or "系统"
        page = CHILD_DETAIL + str(ctx["id"])
        if passed:
            wx.send_exam_result(
                openid,
                first="您的订单审核通过",
                order_no=str(ctx.get("orderId") or ""),
                time_str=_now_str(),
                auditor=auditor,
                result="审核通过",
                remark="订单已审核完成，可进行后续操作",
                page_path=page,
            )
        else:
            wx.send_exam_result(
                openid,
                first="您的订单未通过审核",
                order_no=str(ctx.get("orderId") or ""),
                time_str=_now_str(),
                auditor=auditor,
                result="审核驳回",
                remark="订单已驳回，请修改后重新上传",
                page_path=page,
            )
    except Exception as exc:
        logger.warning("notify_audit_result failed: %s", exc)


def notify_submit_audit(*, order_id: int) -> None:
    """提交审核 → 销售主管。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        openid = _staff_utgzh(ctx.get("saleManagerId"))
        if not openid:
            return
        custom = _customer_by_id(ctx.get("parentCustomUserId") or ctx.get("customUserId"))
        company = _company(ctx.get("customerId") or ctx.get("parentCustomerId"))
        if custom:
            customer = str(custom.get("mobile") or "")
        elif company:
            customer = str(company.get("name") or "")
        else:
            customer = ""
        wx.send_order_apply(
            openid,
            first="您有订单待审核",
            order_no=str(ctx.get("orderId") or ""),
            customer=customer,
            time_str=_now_str(),
            amount=_amount_str(ctx.get("totalPrice")),
            page_path=CHILD_DETAIL + str(ctx["id"]),
        )
    except Exception as exc:
        logger.warning("notify_submit_audit failed: %s", exc)


def notify_sample_arrive(
    *,
    order_id: int,
    staff_user_id: str | int | None = None,
) -> None:
    """样品到货 → 客户到货通知 + 测试员待测通知。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        operator = _staff_true_name(staff_user_id) or "系统"
        order_no = str(ctx.get("orderId") or "")
        now = _now_str()

        custom_id = ctx.get("parentCustomUserId") or ctx.get("customUserId")
        custom = _customer_by_id(custom_id)
        if custom and _accepts_message(custom):
            wx.send_sample_detection(
                str(custom.get("wxOpenid") or ""),
                first="您有实验订单样品到货",
                order_no=order_no,
                status="正常",
                operator=operator,
                time_str=now,
                page_path=TEST_ORDER_DETAIL + str(ctx["id"]),
            )
        else:
            company = _company(ctx.get("customerId") or ctx.get("parentCustomerId"))
            if company:
                cu = _customer_by_mobile(str(company.get("contractPhone") or ""))
                if cu:
                    wx.send_sample_detection(
                        str(cu.get("wxOpenid") or ""),
                        first="您有实验订单样品到货",
                        order_no=order_no,
                        status="正常",
                        operator=operator,
                        time_str=now,
                        page_path=CHILD_DETAIL + str(ctx["id"]),
                    )

        # 测试人员：取本子单下第一条有测试员的子行
        tester = fetch_one(
            """
            SELECT test_user_id AS testUserId
            FROM experiment_order_child
            WHERE order_form_id = %(oid)s
              AND IFNULL(delete_status, 2) <> 1
              AND IFNULL(test_user_id, '') <> ''
              AND CAST(test_user_id AS CHAR) <> '22'
            ORDER BY id ASC
            LIMIT 1
            """,
            {"oid": order_id},
        )
        if not tester:
            tester = fetch_one(
                """
                SELECT c.test_user_id AS testUserId
                FROM exp_qd_purchase_order_child p
                JOIN experiment_order_child c ON p.order_child_id = c.id
                WHERE p.purchase_order_id = %(oid)s
                  AND IFNULL(c.delete_status, 2) <> 1
                  AND IFNULL(c.test_user_id, '') <> ''
                  AND CAST(c.test_user_id AS CHAR) <> '22'
                ORDER BY c.id ASC
                LIMIT 1
                """,
                {"oid": order_id},
            )
        test_openid = _staff_utgzh((tester or {}).get("testUserId"))
        if test_openid:
            wx.send_sample_apply(
                test_openid,
                first="您有实验订单样品待测试",
                order_no=order_no,
                status="待测试",
                time_str=now,
                remark=None,
                page_path=CHILD_DETAIL + str(ctx["id"]),
            )
    except Exception as exc:
        logger.warning("notify_sample_arrive failed: %s", exc)


def notify_test_start(*, order_id: int) -> None:
    """开始测试 → 客户(父单 type 6/8) + 实验室主管。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        order_no = str(ctx.get("orderId") or "")
        now = _now_str()
        page = ORDER_DETAIL + str(ctx["id"])
        pot = str(ctx.get("parentOrderType") or "")
        if pot in ("6", "8"):
            openid, _ = _resolve_customer_openid(ctx)
            if openid:
                wx.send_sample_apply(
                    openid,
                    first="您的订单开始测试",
                    order_no=order_no,
                    status="测试中",
                    time_str=now,
                    remark="订单已开始测试，可查看信息详情",
                    page_path=page,
                )
        mgr = _manager_openid(ctx)
        if mgr:
            wx.send_sample_apply(
                mgr,
                first="您的订单开始测试",
                order_no=order_no,
                status="测试中",
                time_str=now,
                remark="订单已开始测试，可查看信息详情",
                page_path=page,
            )
    except Exception as exc:
        logger.warning("notify_test_start failed: %s", exc)


def notify_test_end(*, order_id: int) -> None:
    """测试完成 → 客户(父单 type 6/8) + 实验室主管。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        order_no = str(ctx.get("orderId") or "")
        now = _now_str()
        page = ORDER_DETAIL + str(ctx["id"])
        pot = str(ctx.get("parentOrderType") or "")
        if pot in ("6", "8"):
            openid, _ = _resolve_customer_openid(ctx)
            if openid:
                wx.send_sample_apply(
                    openid,
                    first="您有订单测试完成",
                    order_no=order_no,
                    status="测试完成",
                    time_str=now,
                    remark=None,
                    page_path=page,
                )
        mgr = _manager_openid(ctx)
        if mgr:
            wx.send_sample_apply(
                mgr,
                first="您有订单测试完成",
                order_no=order_no,
                status="测试完成",
                time_str=now,
                remark=None,
                page_path=page,
            )
    except Exception as exc:
        logger.warning("notify_test_end failed: %s", exc)


def notify_sample_pick_video(
    *,
    order_id: int,
    child_ids: list[int],
) -> None:
    """样品领用且存在会议号 → 云视频会议模板。"""
    try:
        if not child_ids:
            return
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        children = []
        for cid in child_ids:
            row = fetch_one(
                """
                SELECT id, goods_name AS goodsName, meeting_num AS meetingNum
                FROM experiment_order_child
                WHERE id = %(id)s AND IFNULL(delete_status, 2) <> 1
                LIMIT 1
                """,
                {"id": cid},
            )
            if row and str(row.get("meetingNum") or "").strip():
                children.append(row)
        if not children:
            return
        child = children[0]
        meeting_num = str(child.get("meetingNum") or "").strip()
        goods_name = str(child.get("goodsName") or "")[:20]
        now = _now_str()
        first = "测试即将开始，请尽快进入会议房间号查看"

        # 客户
        custom_id = ctx.get("parentCustomUserId") or ctx.get("customUserId")
        custom = _customer_by_id(custom_id)
        if custom and _accepts_message(custom):
            wx.send_video(
                str(custom.get("wxOpenid") or ""),
                first=first,
                time_str=now,
                goods_name=goods_name,
                meeting_num=meeting_num,
            )
        else:
            company = _company(ctx.get("parentCustomerId") or ctx.get("customerId"))
            if company:
                cu = _customer_by_mobile(str(company.get("contractPhone") or ""))
                if cu:
                    wx.send_video(
                        str(cu.get("wxOpenid") or ""),
                        first=first,
                        time_str=now,
                        goods_name=goods_name,
                        meeting_num=meeting_num,
                    )
        mgr = _manager_openid(ctx)
        if mgr:
            wx.send_video(
                mgr,
                first=first,
                time_str=now,
                goods_name=goods_name,
                meeting_num=meeting_num,
            )
    except Exception as exc:
        logger.warning("notify_sample_pick_video failed: %s", exc)


def notify_sample_ship(
    *,
    order_id: int,
    express_name: str,
    express_no: str,
) -> None:
    """样品寄回 → 客户 + 实验室主管。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        order_no = str(ctx.get("orderId") or "")
        now = _now_str()
        page = ORDER_DETAIL + str(ctx["id"])
        openid, _ = _resolve_customer_openid(ctx)
        if openid:
            wx.send_sample_send(
                openid,
                first="测试样品已寄送",
                order_no=order_no,
                express_name=express_name,
                express_no=express_no,
                time_str=now,
                keyword5="测试样品已寄送",
                page_path=page,
            )
        mgr = _manager_openid(ctx)
        if mgr:
            wx.send_sample_send(
                mgr,
                first="测试样品已寄送",
                order_no=order_no,
                express_name=express_name,
                express_no=express_no,
                time_str=now,
                keyword5="测试样品已寄送",
                page_path=page,
            )
    except Exception as exc:
        logger.warning("notify_sample_ship failed: %s", exc)


def notify_pay_flow(
    *,
    order_id: int,
    pay_type: str,
    staff_user_id: str | int | None = None,
) -> None:
    """付款申请/通过/驳回（type 1/2/3）。"""
    try:
        ctx = _load_order_ctx(order_id)
        if not ctx:
            return
        t = str(pay_type or "").strip()
        order_no = str(ctx.get("orderId") or "")
        now = _now_str()
        page = f"{PAY_DETAIL}{ctx['id']}&orderId={order_no}"
        operator = _staff_true_name(staff_user_id) or "系统"
        if t == "1":
            openid = _staff_utgzh(ctx.get("saleManagerId"))
            wx.send_pay_review(
                openid,
                template_id=wx.ORDER_REVIEW,
                first="您有付款待审核的实验分包子订单",
                keyword1=order_no,
                keyword2=operator,
                keyword3=now,
                keyword4=_amount_str(ctx.get("totalPrice")),
                keyword5="请尽快登录系统进行审核",
                remark="",
                page_path=page,
            )
        elif t == "2":
            openid = _staff_utgzh(ctx.get("addUserId"))
            wx.send_pay_review(
                openid,
                template_id=wx.ORDER_REVIEW_RESULT,
                first="您有付款申请已审核通过",
                keyword1=order_no,
                keyword2=now,
                keyword3="订单审核通过",
                keyword4=operator,
                keyword5=None,
                remark="订单已审核完成，可进行后续操作",
                page_path=page,
            )
        elif t == "3":
            openid = _staff_utgzh(ctx.get("addUserId"))
            wx.send_pay_review(
                openid,
                template_id=wx.ORDER_REVIEW_RESULT,
                first="您有付款申请已驳回",
                keyword1=order_no,
                keyword2=now,
                keyword3="订单审核驳回",
                keyword4=operator,
                keyword5=None,
                remark="订单审核驳回，请确认后再次提交",
                page_path=page,
            )
    except Exception as exc:
        logger.warning("notify_pay_flow failed: %s", exc)
