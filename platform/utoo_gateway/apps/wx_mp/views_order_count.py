"""/api/wx/getOrderCount.ajax"""
from __future__ import annotations

import logging

from django.db import DatabaseError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.views import get_current_user_from_request
from apps.core.responses import ajax_fail, ajax_ok
from apps.wx_mp.repositories import order_count as order_count_repo

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_order_count(request: Request):
    current = get_current_user_from_request(request)
    if not current:
        return Response(ajax_fail("用户未登录"))
    if current.get("account_kind") == "exp_user":
        # 客户端个人中心不用该统计；返回全 0 避免前端报错
        return Response(
            ajax_ok(
                {
                    "orderCount": 0,
                    "suborderCount": 0,
                    "orderchildCount": 0,
                    "suborderchildCount": 0,
                    "orderCountAll": 0,
                    "orderCountByManage": 0,
                    "orderCountm": 0,
                    "suborderCountm": 0,
                    "orderchildCountm": 0,
                    "suborderchildCountm": 0,
                    "expsubChildpayListnum": 0,
                },
                "操作成功",
            )
        )

    user_id = str(current.get("user_id") or "")
    if not user_id:
        return Response(ajax_fail("用户未登录"))

    try:
        row = order_count_repo.load_sy_user(user_id)
        obj = order_count_repo.build_order_count_obj(user_id=user_id, user_row=row)
        return Response(ajax_ok(obj, "操作成功"))
    except DatabaseError as exc:
        logger.exception("getOrderCount db error: %s", exc)
        return Response(ajax_fail("数据库不可用"))
    except Exception as exc:
        logger.exception("getOrderCount failed: %s", exc)
        return Response(ajax_fail("查询订单统计失败"))
