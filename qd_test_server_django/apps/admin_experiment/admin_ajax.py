from __future__ import annotations

from rest_framework.response import Response

from apps.admin_core.admin_ajax import admin_ajax_view
from apps.core.responses import ajax_fail, ajax_ok


def ok(obj=None, res_msg: str = "操作成功"):
    return Response(ajax_ok(obj=obj, res_msg=res_msg))


def fail(msg: str = "操作失败", obj=None):
    return Response(ajax_fail(msg, obj=obj))


__all__ = ["admin_ajax_view", "ok", "fail"]
