from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.core.services import banner as banner_svc
from apps.orders.services import catalog as catalog_svc
from apps.orders.services import experiment as experiment_svc


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def index_class_list(request: Request):
    data = catalog_svc.build_index_class_list()
    return Response(api_ok(data, message="获取成功!"))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def banner_list(request: Request):
    data = banner_svc.list_pc_banners()
    if not data:
        return Response(api_fail(404, "暂无轮播图"))
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sel_third_class_list(request: Request):
    q = request.query_params
    data = catalog_svc.sel_third_class_list(
        start=str(q.get("start") or "0"),
        length=str(q.get("length") or "10"),
        draw=str(q.get("draw") or "1"),
        class_id=str(q.get("classId") or ""),
    )
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sel_fir_and_sec_class_list(request: Request):
    data = catalog_svc.sel_fir_and_sec_class_list()
    return Response(api_ok(data, message="获取成功!"))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sel_third_class_by_keyword_list(request: Request):
    q = request.query_params
    data = catalog_svc.sel_third_class_by_keyword(
        start=str(q.get("start") or "0"),
        length=str(q.get("length") or "10"),
        draw=str(q.get("draw") or "1"),
        key_word=str(q.get("keyWord") or q.get("keywords") or ""),
    )
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def index_exp_list(request: Request):
    data = experiment_svc.build_index_exp_list()
    return Response(api_ok(data, message="获取成功!"))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sel_exp_list(request: Request):
    q = request.query_params
    data = experiment_svc.sel_exp_list(
        start=str(q.get("start") or "0"),
        length=str(q.get("length") or "10"),
        draw=str(q.get("draw") or "1"),
        class_id=str(q.get("classId") or q.get("class_id") or ""),
        key_word=str(q.get("keyWord") or q.get("keywords") or ""),
    )
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def test_class_detail(request: Request):
    cid = str(request.query_params.get("id") or "")
    if not cid.isdigit():
        return Response(api_fail(400, "参数错误"))
    data = experiment_svc.test_class_detail(int(cid))
    if not data:
        return Response(api_fail(404, "实验不存在"))
    return Response(api_ok(data, message="获取成功!"))
