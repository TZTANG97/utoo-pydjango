"""小程序订单详情写操作 — Java ajax 路径薄封装。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import merge_payload, to_int
from apps.admin_experiment.repositories import orders as order_repo
from apps.admin_experiment.repositories import sample_flow as sample_flow_repo
from apps.orders.services import staff_child_detail as child_detail_svc
from apps.orders.services import staff_sale_detail as sale_detail_svc
from qd_common.responses import ajax_fail, ajax_ok


def _order_pk(data: dict) -> int:
    return to_int(data.get("id") or data.get("ofId") or data.get("of_id") or data.get("orderId")) or 0


def _audit_pass(data: dict) -> bool:
    """MP 传 type=1 通过 / type=2 驳回；也兼容 pass。"""
    if "type" in data and data.get("type") is not None and str(data.get("type")) != "":
        return str(data.get("type")) in ("1", "true", "True", "yes")
    pass_raw = data.get("pass")
    if pass_raw is None:
        pass_raw = data.get("auditPass")
    if isinstance(pass_raw, str):
        return pass_raw.lower() in ("1", "true", "yes", "y")
    if pass_raw is None:
        return True
    return bool(pass_raw)


def _ok_or_fail(ok_flag: bool, msg: str) -> Response:
    return Response(ajax_ok(res_msg=msg) if ok_flag else ajax_fail(msg))


def _do_cancel(data: dict) -> Response:
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.cancel_order(
        order_id=oid,
        remark=str(data.get("remark") or data.get("mark") or data.get("type") or "").strip(),
    )
    return _ok_or_fail(ok_flag, msg)


def _do_submit_audit(data: dict) -> Response:
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.submit_audit(order_id=oid)
    return _ok_or_fail(ok_flag, msg)


def _do_withdraw(data: dict) -> Response:
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.withdraw_audit(order_id=oid)
    return _ok_or_fail(ok_flag, msg)


def _do_audit(data: dict) -> Response:
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.audit_order(
        order_id=oid,
        pass_=_audit_pass(data),
        remark=str(data.get("remark") or data.get("mark") or "").strip(),
    )
    return _ok_or_fail(ok_flag, msg)


# ---------- experimentOrder / experimentSubOrder ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def custome_operate_cancel(request: Request):
    return _do_cancel(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def submit_audit_exp(request: Request):
    return _do_submit_audit(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_status_withdraw(request: Request):
    """取消审核申请 — updateStatus.ajax"""
    return _do_withdraw(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def audit_order_mp(request: Request):
    return _do_audit(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def cost_settle_sure(request: Request):
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.cost_settle_sure(order_id=oid)
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_share_ratio_mp(request: Request):
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.update_share_ratio(
        order_id=oid,
        user_scale_info=str(data.get("user_scale_info") or data.get("userScaleInfo") or ""),
        salecb_user_scale_info=str(
            data.get("salecb_user_scale_info") or data.get("salecbUserScaleInfo") or ""
        ),
        scale_info=str(data.get("scale_info") or data.get("scaleInfo") or ""),
    )
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def make_front_order(request: Request):
    """saleOrder/makeFrontOrder.ajax — 已和客户沟通确认。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.confirm_customer_order(order_id=oid)
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_bill_data(request: Request):
    """bill/addBillData.ajax — type2: 1开票 2收款。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    type2 = str(data.get("type2") or data.get("type") or "").strip()
    money = data.get("money") or data.get("amount")
    bill_date = str(data.get("billDate") or data.get("bill_date") or "")
    # type2=1 或 type=1 → 开票；其余按收款
    is_invoice = type2 in ("1",) or str(data.get("type") or "") == "1"
    if is_invoice and str(data.get("type2") or "") == "2":
        is_invoice = False
    if str(data.get("type2") or "") == "1":
        is_invoice = True
    elif str(data.get("type2") or "") == "2":
        is_invoice = False

    if is_invoice:
        ok_flag, msg = order_repo.save_invoice_bill(
            order_id=oid,
            money=money,
            log_info=str(data.get("logInfo") or "录入开票"),
        )
    else:
        row = order_repo.get_order(oid) or {}
        if str(row.get("orderType") or "") == "9" and row.get("canUploadPay"):
            ok_flag, msg = order_repo.upload_sub_pay_bill(
                order_id=oid,
                money=money,
                staff_user_id="",
                log_info=str(data.get("logInfo") or "上传付款信息"),
            )
        else:
            from apps.admin_experiment.services.split_money import save_receive_bill

            ok_flag, msg = save_receive_bill(
                order_id=oid,
                money=money,
                staff_user_id="",
                log_info=str(data.get("logInfo") or "录入收款"),
                bill_date=bill_date,
            )
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def sub_order_detail(request: Request):
    """experimentSubOrder/orderdetail.ajax — 复用主单员工详情。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    body = sale_detail_svc.order_detail_dpt(order_id=oid)
    if not body.get("of"):
        return Response(ajax_fail("订单不存在"))
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def sub_edit_page(request: Request):
    """experimentSubOrder/editPage.ajax — 分包订单编辑页数据。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    body = sale_detail_svc.sub_edit_page(order_id=oid)
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


# ---------- experimentChildOrder ----------


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_cancel_operate(request: Request):
    return _do_cancel(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_submit_audit(request: Request):
    return _do_submit_audit(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_update_status(request: Request):
    return _do_withdraw(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_audit_order(request: Request):
    return _do_audit(merge_payload(request))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_sel_goods_list(request: Request):
    data = merge_payload(request)
    return Response(
        child_detail_svc.sel_goods_list_dpt(
            of_id=str(data.get("ofId") or data.get("of_id") or data.get("id") or ""),
            order_status=str(data.get("orderStatus") or data.get("order_status") or ""),
            is_meeting=str(data.get("is_meeting") or data.get("isMeeting") or ""),
            start=str(data.get("start") or "0"),
            length=str(data.get("length") or "10"),
            draw=str(data.get("draw") or "1"),
        )
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_add_video_info(request: Request):
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = sample_flow_repo.add_video_meeting(
        order_id=oid,
        child_ids=data.get("childids") or data.get("childIds") or data.get("child_ids"),
        meeting_num=str(data.get("meeting_num") or data.get("meetingNum") or ""),
    )
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_edit_page_xcx(request: Request):
    data = merge_payload(request)
    oid = _order_pk(data)
    body = child_detail_svc.edit_page_xcx(order_id=oid)
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_edit_page(request: Request):
    """expSubPurchaseOrder/editPage.ajax"""
    data = merge_payload(request)
    oid = _order_pk(data)
    body = child_detail_svc.edit_page_xcx(order_id=oid)
    return Response(ajax_ok(obj=body, res_msg="获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_add_order_data(request: Request):
    """确认已下单 — addOrderData.ajax"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.confirm_ordered(order_id=oid)
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_pay(request: Request):
    """付款申请/审核 — pay.ajax；type 1申请 2通过 3驳回。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    ok_flag, msg = order_repo.update_sub_pay(
        order_id=oid,
        pay_type=data.get("type") or data.get("payType") or "",
    )
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def child_update_order_status(request: Request):
    """厂家已发货等 — updateOrderStatus.ajax（默认 45）。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    target = to_int(data.get("orderStatus") or data.get("order_status") or 45) or 45
    ok_flag, msg = order_repo.update_sub_order_status(order_id=oid, order_status=target)
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def sub_get_order_status(request: Request):
    """编辑前状态检查 — experimentSubOrder/getOrderStatus.ajax。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    row = order_repo.get_order(oid)
    if not row:
        return Response(ajax_fail("订单不存在"))
    if row.get("canEdit"):
        return Response(ajax_ok(obj={"canEdit": True}, res_msg="可编辑"))
    return Response(ajax_fail("当前状态不可编辑"))
