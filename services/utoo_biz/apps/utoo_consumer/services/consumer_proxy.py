"""阶段 B：C 端 / 小程序 / 登录 → 中台路由。"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from apps.utoo_consumer.clients.mid_registry import base_url_for, service_label
from shared.utoo_consumer_routes import MidTarget, resolve_consumer_path
from shared.utoo_mid_proxy import proxy_mid_path


def forward_consumer_request(request: Request, path: str):
    decision = resolve_consumer_path(path)
    if decision.target == MidTarget.BIZ_LOCAL:
        return Response(
            {
                "res": False,
                "resMsg": "该接口应由 utoo_biz 本地处理，禁止 _internal twin",
                "obj": None,
            },
            status=503,
        )
    return proxy_mid_path(
        request,
        decision.path,
        base_url=base_url_for(decision.target),
        channel=decision.channel,
        service_name=service_label(decision.target),
    )
