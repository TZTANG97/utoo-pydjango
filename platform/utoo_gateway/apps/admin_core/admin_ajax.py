import inspect
import logging
from functools import wraps

from django.db import DatabaseError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_core.permissions import is_sy_staff
from apps.auth_pc.views import get_current_user_from_request
from apps.core.responses import ajax_fail, ajax_ok

logger = logging.getLogger(__name__)


def admin_ajax_view(*, require_staff: bool = True):
    def decorator(fn):
        @wraps(fn)
        def wrapper(request: Request, *args, **kwargs):
            user = get_current_user_from_request(request)
            if require_staff and not is_sy_staff(user):
                return Response(ajax_fail("用户未登录或登录已失效，请重新登录"))
            try:
                if "user" in inspect.signature(fn).parameters:
                    return fn(request, user=user, *args, **kwargs)
                return fn(request, *args, **kwargs)
            except DatabaseError as exc:
                logger.exception("%s db error: %s", fn.__name__, exc)
                return Response(ajax_fail("数据库不可用，请检查 DB 配置与连接"))
            except Exception as exc:
                logger.exception("%s failed: %s", fn.__name__, exc)
                return Response(ajax_fail(f"操作失败：{exc}"))

        return wrapper

    return decorator


def ajax_response(res: bool, *, res_msg: str = "", obj=None) -> Response:
    if res:
        return Response(ajax_ok(obj=obj, res_msg=res_msg or "操作成功"))
    return Response(ajax_fail(res_msg or "操作失败", obj=obj))
