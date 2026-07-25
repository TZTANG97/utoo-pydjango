from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import ajax_fail, ajax_ok, api_fail, api_ok
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


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def xcx_test_class_detail(request: Request):
    """小程序实验详情 — 对齐 /pc/xcxtestClassDetail.ajax，Ajax {res,resMsg,obj}。"""
    cid = str(request.query_params.get("id") or "")
    if not cid.isdigit():
        return Response(ajax_fail("参数错误"))
    data = experiment_svc.test_class_detail(int(cid))
    if not data:
        return Response(ajax_fail("实验不存在"))
    return Response(ajax_ok(data, "获取成功!"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_xcx_banner(request: Request):
    """愉兔小程序封面 — 对齐 Java getXcxBanner.ajax（platform_type=2）。"""
    del request
    banner = banner_svc.pick_random_cover_banner(platform_type="2")
    return Response(ajax_ok({"banner": banner}, "查询成功"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_tuzhe_banner(request: Request):
    """途哲小程序封面 — 对齐 Java getTuZheBanner.ajax（platform_type=3）。"""
    del request
    banner = banner_svc.pick_random_cover_banner(platform_type="3")
    return Response(ajax_ok({"banner": banner}, "查询成功"))
