import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.services.profile import UserProfileService
from apps.auth_pc.views import get_current_user_from_request, is_exp_customer
from apps.core.responses import api_fail, api_ok
from apps.core.svc_proxy import forward_auth, svc_auth_enabled

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_user_basic_info(request: Request):
    if svc_auth_enabled():
        return forward_auth(request, "/api/auth/basic-info")
    current = get_current_user_from_request(request)
    if not is_exp_customer(current):
        return Response(api_fail(401, "用户未登录"))
    try:
        data = UserProfileService.get_basic_info(int(current["user_id"]))
        return Response(api_ok(data, message="获取用户基本信息成功!"))
    except DatabaseError as exc:
        logger.exception("getUserBasicInfo db error: %s", exc)
        return Response(api_fail(503, "数据库不可用"))
    except Exception as exc:
        logger.exception("getUserBasicInfo failed: %s", exc)
        return Response(api_fail(500, f"获取用户基本信息失败：{exc}"))
