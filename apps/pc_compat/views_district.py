from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_ok
from apps.core.services import district as district_svc


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def query_pro_city_co(request: Request, user=None):
    super_id = str(request.query_params.get("superId") or "")
    data = district_svc.list_by_super_id(super_id)
    return Response(api_ok(data))


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def query_pro_city_co1(request: Request):
    data = district_svc.provinces_cities_tree()
    return Response(api_ok(data))
