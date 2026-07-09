from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.orders.services import retest_apply as retest_svc


def _param(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_order_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def add_retest_application(request: Request, user=None):
    ok_flag, msg = retest_svc.add_retest_application(
        user_id=int(user["user_id"]),
        order_id=_param(request, "orderId"),
        mark=_param(request, "mark"),
        remeasurement_require=_param(request, "remeasurement_require"),
    )
    if ok_flag:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
