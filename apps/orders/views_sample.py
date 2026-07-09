from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.orders.services import sample_info as sample_svc


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def attribute_state_list(request: Request, user=None):
    data = sample_svc.list_attribute_states()
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def stability_list(request: Request, user=None):
    data = sample_svc.list_stability()
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def sample_attribute_manage_list(request: Request, user=None):
    sid = str(request.query_params.get("special_id") or "")
    if not sid.isdigit():
        return Response(api_fail(400, "参数错误"))
    tree = sample_svc.sample_attribute_manage_tree(special_id=int(sid))
    if tree is None:
        return Response(api_ok(None))
    return Response(api_ok(tree))
