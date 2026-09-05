from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.orders.services import actions as order_actions


@forward_order_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def write_evaluate(request: Request, user=None):
    body = request.data if isinstance(request.data, dict) else {}
    oid = body.get("id")
    star = body.get("star", 5)
    content = str(body.get("content") or "")
    try:
        order_id = int(oid)
        star_n = int(star)
    except (TypeError, ValueError):
        return Response(api_fail(400, "参数错误"))
    if star_n < 1 or star_n > 5:
        star_n = 5
    ok_flag, msg = order_actions.write_evaluate(
        user_id=int(user["user_id"]),
        order_id=order_id,
        star=star_n,
        content=content,
    )
    if not ok_flag:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))
