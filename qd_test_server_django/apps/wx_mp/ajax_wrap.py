"""将 pc_compat 的 {code,message,data} 响应转为小程序 Ajax {res,resMsg,obj}。"""
from __future__ import annotations

import json
from functools import wraps

from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def to_ajax_body(data) -> dict:
    if not isinstance(data, dict):
        return {
            "res": True,
            "resMsg": "操作成功",
            "obj": data,
            "code": 0,
            "message": "操作成功",
            "data": data,
        }
    if "res" in data:
        ok = bool(data.get("res"))
        msg = data.get("resMsg") or data.get("message") or ("操作成功" if ok else "操作失败")
        obj = data.get("obj") if "obj" in data else data.get("data")
        return {
            "res": ok,
            "resMsg": msg,
            "obj": obj,
            "code": data.get("code", 0 if ok else 1),
            "message": msg,
            "data": obj,
        }
    code = data.get("code", 0)
    ok = code == 0
    msg = data.get("message") or ("操作成功" if ok else "操作失败")
    obj = data.get("data")
    return {
        "res": ok,
        "resMsg": msg,
        "obj": obj,
        "code": code,
        "message": msg,
        "data": obj,
    }


def _extract_body(resp) -> tuple[object | None, int]:
    data = getattr(resp, "data", None)
    status = getattr(resp, "status_code", 200)
    if data is not None:
        return data, status
    if isinstance(resp, (JsonResponse, HttpResponse)) and resp.content:
        try:
            return json.loads(resp.content.decode("utf-8")), status
        except (TypeError, ValueError, UnicodeDecodeError):
            return None, status
    return None, status


def wrap_as_ajax(view_func, *, pc_path: str):
    """
    包装 pc_compat 视图挂到 /api/wx/：
    - 调用前把 path 改成 /api/pc/...，以便 SVC_ORDER 转发命中上游
    - 响应体转为 Ajax {res,resMsg,obj}
    """

    @api_view(["GET", "POST"])
    @authentication_classes([])
    @permission_classes([AllowAny])
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        django_request = getattr(request, "_request", request)
        old_path = django_request.path
        old_path_info = django_request.path_info
        django_request.path = pc_path
        django_request.path_info = pc_path
        try:
            resp = view_func(django_request, *args, **kwargs)
        finally:
            django_request.path = old_path
            django_request.path_info = old_path_info
        data, status = _extract_body(resp)
        if data is not None:
            return Response(to_ajax_body(data), status=status)
        return resp

    return wrapper
