from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import parse_ajax_params, pc_ajax_view
from qd_common.responses import api_ok
from apps.orders.services import company_lookup as company_svc


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def sel_company_name(request: Request, user=None):
    del user
    params = parse_ajax_params(request)
    q = request.query_params
    data = company_svc.sel_company_name_page(
        start=params["start"],
        length=params["length"],
        draw=params["draw"],
        keyword=str(q.get("keyword") or ""),
    )
    return Response(api_ok(data))
