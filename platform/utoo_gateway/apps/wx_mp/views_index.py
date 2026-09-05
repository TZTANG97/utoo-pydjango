"""小程序 /api/index/* — 对齐 Java IndexViewController。"""
from __future__ import annotations

import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.db_utils import fetch_all
from apps.core.responses import ajax_fail, ajax_ok
from shared.utoo_user_roles import build_user_roles

logger = logging.getLogger(__name__)


def _fetch_type_rows() -> list[dict]:
    return fetch_all(
        """
        SELECT sut.type_name AS name, utr.name AS roleName
        FROM sy_user_type sut
        LEFT JOIN user_type_role utr ON utr.id = sut.role_id
        ORDER BY utr.id
        """
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def user_roles(request: Request):
    del request
    try:
        obj = build_user_roles(fetch_rows=_fetch_type_rows)
        return Response(ajax_ok(obj, "操作成功"))
    except DatabaseError as exc:
        logger.exception("userRoles db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
