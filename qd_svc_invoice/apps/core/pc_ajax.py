import inspect
import logging
from functools import wraps

from django.db import DatabaseError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_support.helpers import get_current_user_from_request, is_exp_customer
from qd_common.responses import api_fail, api_ok

logger = logging.getLogger(__name__)


def parse_ajax_params(request: Request) -> dict:
    q = request.query_params
    body = request.data if isinstance(request.data, dict) else {}
    return {
        "start": str(q.get("start") or body.get("start") or "0"),
        "length": str(q.get("length") or body.get("length") or "10"),
        "draw": str(q.get("draw") or body.get("draw") or "1"),
        "type": str(q.get("type") or body.get("type") or "0"),
        "keywords": str(q.get("keywords") or body.get("keywords") or ""),
        "order_id": str(q.get("order_id") or body.get("order_id") or ""),
    }


def pc_ajax_view(*, require_login: bool = False, require_customer: bool = False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(request: Request, *args, **kwargs):
            user = get_current_user_from_request(request)
            if require_login and not user:
                return Response(api_fail(401, "用户未登录"))
            if require_customer and not is_exp_customer(user):
                return Response(api_fail(401, "用户未登录或登录已失效，请重新登录"))
            try:
                if "user" in inspect.signature(fn).parameters:
                    return fn(request, user=user, *args, **kwargs)
                return fn(request, *args, **kwargs)
            except DatabaseError as exc:
                logger.exception("%s db error: %s", fn.__name__, exc)
                return Response(api_fail(503, "数据库不可用，请检查 DB 配置与连接"))
            except Exception as exc:
                logger.exception("%s failed: %s", fn.__name__, exc)
                return Response(api_fail(500, f"操作失败：{exc}"))

        return wrapper

    return decorator
