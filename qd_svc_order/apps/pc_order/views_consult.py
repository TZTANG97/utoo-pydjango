from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import pc_ajax_view
from qd_common.responses import api_fail, api_ok
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


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def service_consult_add(request: Request, user=None):
    class_id = _param(request, "class_id")
    if not class_id.isdigit():
        return Response(api_fail(400, "请选择实验分类"))
    ok_flag, msg, _ = consult_svc.create_consult(
        user_id=int(user["user_id"]),
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
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def exp_make_list(request: Request, user=None):
    data = consult_list_svc.exp_make_list()
    return Response(api_ok(data, message="获取成功!"))


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


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def my_exp_make_status_list(request: Request, user=None):
    data = consult_list_svc.exp_user_log_list(int(user["user_id"]))
    return Response(api_ok(data))


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


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def print_yyd(request: Request, user=None):
    oid = _param(request, "id")
    if not oid or not oid.strip().isdigit():
        return Response(api_fail(400, "参数错误"))
    ok_flag, msg, data = accessory_ops_svc.print_yyd_url(
        user_id=int(user["user_id"]),
        order_id=int(oid),
    )
    if ok_flag:
        return Response(api_ok(data))
    return Response(api_fail(400, msg))
