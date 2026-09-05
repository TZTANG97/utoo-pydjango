from __future__ import annotations

import inspect
import logging
from functools import wraps

from django.db import DatabaseError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import is_sy_staff
from apps.auth_support.helpers import get_current_user_from_request
from qd_common.responses import ajax_fail, ajax_ok

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
                # 把常见列名/SQL 错误透出，避免一律显示「数据库不可用」难排查
                detail = str(exc).strip()
                if "Unknown column" in detail or "1054" in detail:
                    return Response(ajax_fail(f"数据库字段异常：{detail}"))
                return Response(ajax_fail("数据库不可用，请检查 DB 配置与连接"))
            except Exception as exc:
                logger.exception("%s failed: %s", fn.__name__, exc)
                return Response(ajax_fail(f"操作失败：{exc}"))

        return wrapper

    return decorator


def ok(obj=None, res_msg: str = "操作成功"):
    return Response(ajax_ok(obj=obj, res_msg=res_msg))


def fail(msg: str = "操作失败", obj=None):
    return Response(ajax_fail(msg, obj=obj))
