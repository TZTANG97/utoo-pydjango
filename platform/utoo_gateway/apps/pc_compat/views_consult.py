from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.views import is_exp_customer
from apps.core.db_utils import fetch_one
from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import ajax_fail, ajax_ok, api_fail, api_ok
from apps.orders.services import consult as consult_svc
from apps.orders.services import consult_list as consult_list_svc
from apps.orders.services import reorder as reorder_svc
from apps.orders.services import accessory_ops as accessory_ops_svc


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


def _resolve_consult_user_id(user: dict | None) -> int | None:
    """实验预约 user_id 为 exp_user 数字 id；员工 sy_user 按手机号映射。"""
    if not user:
        return None
    raw = user.get("user_id")
    if is_exp_customer(user):
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    sy_id = str(raw or "")
    mobile = str(user.get("mobile") or user.get("user_name") or "").strip()
    if not mobile and sy_id:
        row = fetch_one(
            """
            SELECT mobile_phone_number AS mobile
            FROM sy_users WHERE id = %(id)s LIMIT 1
            """,
            {"id": sy_id},
        )
        mobile = str((row or {}).get("mobile") or "").strip()
    if mobile:
        eu = fetch_one(
            """
            SELECT id FROM exp_user
            WHERE mobile = %(m)s AND IFNULL(deleteStatus, 0) = 0
            LIMIT 1
            """,
            {"m": mobile},
        )
        if eu and eu.get("id") is not None:
            return int(eu["id"])
    return 0


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_login=True, ajax_auth=True)
def service_consult_add(request: Request, user=None):
    """小程序实验预约 — 对齐 Java AjaxRes；员工/客户均可提交。"""
    class_id = _param(request, "class_id")
    if not class_id.isdigit():
        return Response(ajax_fail("请选择实验分类"))
    user_id = _resolve_consult_user_id(user)
    if user_id is None:
        return Response(ajax_fail("用户未登录或登录已失效，请重新登录"))
    ok_flag, msg, _ = consult_svc.create_consult(
        user_id=user_id,
        user_name=_param(request, "userName"),
        mobile=_param(request, "mobile"),
        company_name=_param(request, "company_name"),
        content=_param(request, "content"),
        class_id=int(class_id),
        recycle=_param(request, "recycle", "false"),
        address=_param(request, "address"),
        addressee_name=_param(request, "addresseeName"),
        addressee_mobile=_param(request, "addresseeMobile"),
        is_video=_param(request, "is_video", "false"),
        is_arrive=_param(request, "is_arrive", "false"),
        is_on=_param(request, "is_on", "false"),
        sample_information_list=_param(request, "sampleInformationList"),
        order_list=_param(request, "order_list"),
    )
    if not ok_flag:
        return Response(ajax_fail(msg))
    return Response(ajax_ok(res_msg=msg or "预约成功"))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def exp_make_list(request: Request, user=None):
    data = consult_list_svc.exp_make_list()
    return Response(api_ok(data, message="获取成功!"))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def my_exp_make_list(request: Request, user=None):
    data = consult_list_svc.my_exp_make_list(
        user_id=int(user["user_id"]),
        start=_param(request, "start", "0"),
        length=_param(request, "length", "10"),
        draw=_param(request, "draw", "1"),
        startime=_param(request, "startime"),
        endtime=_param(request, "endtime"),
    )
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def my_exp_make_status_list(request: Request, user=None):
    data = consult_list_svc.exp_user_log_list(int(user["user_id"]))
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def save_service_consult(request: Request, user=None):
    oid = _param(request, "id")
    if not oid or not oid.isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg = reorder_svc.save_service_consult_from_order(
        user_id=int(user["user_id"]),
        order_id=int(oid),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def cancel_consult(request: Request, user=None):
    cid = _param(request, "id")
    if not cid or not cid.strip().isdigit():
        return Response(api_fail(400, "参数不能为空！"))
    ok_flag, msg = consult_list_svc.cancel_consult(
        user_id=int(user["user_id"]),
        consult_id=int(cid),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_login=True)
def print_yyd(request: Request, user=None):
    """打印预约单 — 员工/客户均可；返回 Java AjaxRes（res/obj）。"""
    oid = _param(request, "id")
    if not oid or not oid.strip().isdigit():
        return Response(ajax_fail("参数错误"))
    try:
        uid = int(user.get("user_id")) if user else 0
    except (TypeError, ValueError):
        uid = 0
    ok_flag, msg, data = accessory_ops_svc.print_yyd_url(
        user_id=uid,
        order_id=int(oid),
    )
    if ok_flag:
        return Response(ajax_ok(obj=data, res_msg=msg or "获取成功"))
    return Response(ajax_fail(msg or "获取失败"))
