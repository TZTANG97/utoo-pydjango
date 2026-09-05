from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.orders.services.consult_check import is_service_consult


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def is_service_consult_view(request: Request):
    oid = str(request.query_params.get("id") or "").strip()
    found, msg = is_service_consult(oid)
    if found:
        return Response(api_ok(message=msg))
    return Response(api_fail(400, msg))
