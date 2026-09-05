import logging

from django.db import DatabaseError
from django.http import HttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.order_forward import forward_order_first
from apps.core.responses import api_fail
from apps.orders.services.file_download import content_disposition, load_accessory_bytes

logger = logging.getLogger(__name__)


@forward_order_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def download_file(request: Request):
    """附件下载：优先转发 order（已挂 /api/pc/downloadFile）；未配 SVC 时本地取流。"""
    raw_id = str(request.query_params.get("id") or "").strip()
    if not raw_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    name_hint = str(request.query_params.get("name") or "").strip()
    try:
        data, filename = load_accessory_bytes(int(raw_id), name_hint=name_hint)
    except DatabaseError as exc:
        logger.exception("downloadFile db error: %s", exc)
        return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
    if not data:
        return Response(api_fail(404, "文件不存在"))
    response = HttpResponse(data, content_type="application/octet-stream")
    response["Content-Disposition"] = content_disposition(filename or "download")
    return response
