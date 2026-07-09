from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.payments.services.editor_upload import upload_editor_image


def _legacy_upload_ok(payload: dict, message: str = "上传成功") -> dict:
    return {
        "res": True,
        "resMsg": message,
        "obj": payload,
        "code": 0,
        "message": message,
        "data": payload,
        **payload,
    }


def _legacy_upload_fail(message: str) -> dict:
    return {
        "res": False,
        "resMsg": message,
        "obj": None,
        "code": 1,
        "message": message,
        "data": None,
    }


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def swf_upload(request: Request):
    uploaded = request.FILES.get("file") or request.FILES.get("imgFile")
    if not uploaded:
        return Response(_legacy_upload_fail("请选择图片文件"))
    ok_flag, msg, data = upload_editor_image(
        data=uploaded.read(),
        filename_hint=uploaded.name or "",
        content_type=uploaded.content_type or "",
    )
    if ok_flag:
        return Response(_legacy_upload_ok(data, msg))
    return Response(_legacy_upload_fail(msg))
