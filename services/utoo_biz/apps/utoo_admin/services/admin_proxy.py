"""阶段 C：管理端 welcome / billing / 资金·数字化 → 中台或 internal。"""
from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from apps.utoo_admin.clients.mid_registry import asset_mid_configured, base_url_for, service_label
from shared.utoo_admin_routes import AdminMidTarget, resolve_admin_path
from shared.utoo_mid_proxy import proxy_mid_path


def forward_admin_request(request: Request, path: str):
    decision = resolve_admin_path(path, asset_mid_configured=asset_mid_configured())
    if decision.target == AdminMidTarget.BIZ_LOCAL:
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
