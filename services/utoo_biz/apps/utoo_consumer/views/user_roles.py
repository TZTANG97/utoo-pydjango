"""utoo_biz：userRoles 本地实现（禁止回落 gateway _internal）。"""
from __future__ import annotations

from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from shared.utoo_user_roles import build_user_roles


def _ajax_ok(obj=None, res_msg: str = "操作成功") -> dict:
    return {"res": True, "resMsg": res_msg, "obj": obj}


def _ajax_fail(res_msg: str = "操作失败") -> dict:
    return {"res": False, "resMsg": res_msg, "obj": None}


def _fetch_type_rows() -> list[dict]:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT sut.type_name AS name, utr.name AS roleName
            FROM sy_user_type sut
            LEFT JOIN user_type_role utr ON utr.id = sut.role_id
            ORDER BY utr.id
            """
        )
        if not cur.description:
            return []
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def user_roles(request: Request):
    del request
    try:
        obj = build_user_roles(fetch_rows=_fetch_type_rows)
        return Response(_ajax_ok(obj))
    except Exception as exc:
        # 库挂时仍返回静态枚举，避免前端白屏
        obj = build_user_roles(fetch_rows=None)
        return Response(_ajax_ok(obj, res_msg=f"操作成功(静态枚举:{exc})"))
