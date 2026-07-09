from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.invoice_forward import forward_invoice_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.invoices.services import InvoiceService


@forward_invoice_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def invoice_detail(request: Request, user=None):
    qid = str(request.query_params.get("id") or "").strip()
    if not qid:
        return Response(
            api_ok(
                {
                    "files": [],
                    "obj": {},
                    "ofList": [],
                    "ids": "",
                    "isSqfp": False,
                    "logs": [],
                }
            )
        )
    if not qid.isdigit():
        return Response(api_fail(400, "参数错误"))
    data = InvoiceService.get_invoice_apply_detail(
        user_id=int(user["user_id"]),
        apply_id=int(qid),
    )
    if data is None:
        return Response(api_fail(404, "发票申请不存在"))
    return Response(api_ok(data))
