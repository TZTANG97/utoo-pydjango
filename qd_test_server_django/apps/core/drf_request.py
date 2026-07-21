"""把 Django HttpRequest 提升为 DRF Request（供 forward_*_first 在 api_view 外侧使用）。"""
from __future__ import annotations

from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response


def as_drf_request(request) -> Request:
    if isinstance(request, Request):
        return request
    return Request(request)


def as_django_response(resp):
    """forward_* 在 @api_view 外侧返回时，DRF Response 无 renderer，转 JsonResponse。"""
    if isinstance(resp, Response):
        return JsonResponse(resp.data, status=resp.status_code, safe=False)
    return resp
