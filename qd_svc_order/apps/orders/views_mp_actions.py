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

    accessory_id = data.get("accessoryId") or data.get("accessory_id") or data.get("fileList")
    if is_invoice:
        ok_flag, msg = order_repo.save_invoice_bill(
            order_id=oid,
            money=money,
            log_info=str(data.get("logInfo") or "录入开票"),
            accessory_id=accessory_id,
            bill_date=bill_date,
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
                accessory_id=accessory_id,
            )
    return _ok_or_fail(ok_flag, msg)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def amount_pay(request: Request):
    """bill/amountPay.ajax — 后台会员余额收款。"""
    data = merge_payload(request)
    oid = _order_pk(data)
    if not oid:
        return Response(ajax_fail("参数错误"))
    from apps.admin_experiment.services.split_money import save_member_balance_receive

    ok_flag, msg = save_member_balance_receive(
        order_id=oid,
        money=data.get("money") or data.get("amount"),
        exp_user_id=data.get("exp_userId")
        or data.get("expUserId")
        or data.get("customUserId")
        or "",
        staff_user_id="",
        bill_date=str(data.get("billDate") or data.get("bill_date") or ""),
        accessory_id=data.get("accessoryId") or data.get("accessory_id"),
    )
    return _ok_or_fail(ok_flag, msg)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def upload_bill(request: Request):
    """对齐 Java bill/uploadBill.ajax：收款/开票凭据上传。"""
    from apps.core.db_utils import scalar
    from apps.orders.services import accessory_upload as accessory_upload_svc

    uploaded = request.FILES.get("accfile") or request.FILES.get("orderdata") or request.FILES.get("file")
    if not uploaded:
        return Response(ajax_fail("文件为空"))
    data = merge_payload(request)
    oid = _order_pk(data) or to_int(data.get("id"))
    if not oid:
        return Response(ajax_fail("参数错误"))
    bill_type = str(data.get("billType") or data.get("type") or "0").strip()
    # Java：0收款 SK / 1开票 KP / 2付款 FK；命名序号按 qd_bill.type(1开票/2收款)
    if bill_type == "1":
        tag, qd_type = "KP", 1
    elif bill_type == "2":
        tag, qd_type = "FK", 2
    else:
        tag, qd_type = "SK", 2
    of = order_repo.get_order(oid) or {}
    order_no = str(of.get("orderId") or oid)
    try:
        cnt = int(
            scalar(
                "SELECT COUNT(1) FROM qd_bill WHERE exp_of_id = %(oid)s AND type = %(tp)s",
                {"oid": oid, "tp": qd_type},
                0,
            )
            or 0
        )
    except Exception:
        cnt = 0
    info_name = f"{order_no}{tag}{cnt + 1}"
    ok_flag, msg, obj = accessory_upload_svc.save_order_attachment(
        data=uploaded.read(),
        orig_name=uploaded.name or "upload",
        content_type=uploaded.content_type or "application/octet-stream",
        acc_type=qd_type,
        exp_of_id=oid,
        subdir="bill",
        info=info_name,
    )
    if not ok_flag:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(obj, res_msg=msg))


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
