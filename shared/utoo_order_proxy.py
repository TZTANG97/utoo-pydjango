"""愉兔实验订单中台 HTTP 转发（gateway / utoo_biz 共用）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from django.conf import settings
from django.http import HttpResponse
from rest_framework.response import Response

# 资源别名 → platform/order 路径
UTOO_ORDER_ENDPOINTS = {
    "experiment-orders": "/api/experimentOrder/list_dpt.ajax",
    "experiment-sub-orders": "/api/experimentSubOrder/list_dpt.ajax",
    "exp-sub-purchase-orders": "/api/expSubPurchaseOrder/list_dpt.ajax",
    "experiment-order-detail": "/api/experimentOrder/orderdetail.ajax",
    # 青岛「实验分包订单」：对齐 Java experimentSubOrder/list_dpt → experiment_order type=8
    "subcontract-orders": "/api/experimentSubOrder/list_dpt.ajax",
    "admin-experiment-orders": "/api/adminExperiment/order/list.ajax",
    "admin-experiment-order-detail": "/api/adminExperiment/order/detail.ajax",
    "orders": "/api/adminExperiment/order/list.ajax",
    "order-detail": "/api/adminExperiment/order/detail.ajax",
    "order-status-options": "/api/adminExperiment/order/statusOptions.ajax",
    "order-submit-audit": "/api/adminExperiment/order/submitAudit.ajax",
    "order-withdraw-audit": "/api/adminExperiment/order/withdrawAudit.ajax",
    "order-audit": "/api/adminExperiment/order/audit.ajax",
    "order-cancel": "/api/adminExperiment/order/cancel.ajax",
    "order-update-basic": "/api/adminExperiment/order/updateBasic.ajax",
    "order-update-msg": "/api/adminExperiment/order/updateMsg.ajax",
    "order-create-sub": "/api/adminExperiment/order/createSubOrder.ajax",
    "order-export": "/api/adminExperiment/order/export.ajax",
    "order-submit-exp": "/api/adminExperiment/order/submitExpOrder.ajax",
    "order-more-info": "/api/adminExperiment/order/moreInfo.ajax",
    "order-list-welcome": "/api/adminExperiment/order/listWelcome.ajax",
    "child-order-list-welcome": "/api/experimentChildOrder/list_dpt_welcome.ajax",
    "order-save-reference-price": "/api/adminExperiment/order/saveReferencePrice.ajax",
    "order-update-time-type": "/api/adminExperiment/order/updateTimeType.ajax",
    "order-upload-sub-invoice": "/api/adminExperiment/order/uploadSubInvoice.ajax",
    "order-upload-file": "/api/experimentOrder/uploadData.ajax",
    "order-upload-file-alt": "/api/adminExperiment/order/uploadFile.ajax",
    "order-delete-file": "/api/adminExperiment/order/deleteFile.ajax",
    "order-download-file": "/api/adminExperiment/order/downloadFile.ajax",
    "order-cost-settle": "/api/adminExperiment/order/costSettle.ajax",
    "order-save-receive-bill": "/api/adminExperiment/order/saveReceiveBill.ajax",
    "order-save-invoice-bill": "/api/adminExperiment/order/saveInvoiceBill.ajax",
    "order-confirm-pay": "/api/adminExperiment/order/confirmPay.ajax",
    "order-generate-appointment": "/api/adminExperiment/order/generateAppointment.ajax",
    "order-confirm-customer": "/api/adminExperiment/order/confirmCustomer.ajax",
    "order-amount-pay": "/api/adminExperiment/order/amountPay.ajax",
    "order-share-ratio": "/api/adminExperiment/order/shareRatio.ajax",
    "order-add-related": "/api/adminExperiment/order/addRelated.ajax",
    "order-del-related": "/api/adminExperiment/order/delRelated.ajax",
    "order-save-finish": "/api/adminExperiment/order/saveFinish.ajax",
    "order-confirm-ordered": "/api/adminExperiment/order/confirmOrdered.ajax",
    "order-sub-pay": "/api/adminExperiment/order/subPay.ajax",
    "order-upload-sub-pay": "/api/adminExperiment/order/uploadSubPay.ajax",
    "order-add-video": "/api/adminExperiment/order/addVideo.ajax",
    "grab-orders": "/api/adminExperiment/grab/list.ajax",
    "grab-competition": "/api/adminExperiment/grab/competition.ajax",
    "sample-arrive": "/api/adminExperiment/order/sampleArrive.ajax",
    "sample-pick": "/api/adminExperiment/order/samplePick.ajax",
    "test-start": "/api/adminExperiment/order/testStart.ajax",
    "test-end": "/api/adminExperiment/order/testEnd.ajax",
    "sample-return": "/api/adminExperiment/order/sampleReturn.ajax",
    "sample-ship": "/api/adminExperiment/order/sampleShip.ajax",
    "sample-retain": "/api/adminExperiment/order/sampleRetain.ajax",
    "confirm-done": "/api/adminExperiment/order/confirmDone.ajax",
    "retest": "/api/adminExperiment/order/retest.ajax",
    "retest-apply": "/api/retestapplication/addretestapplication.ajax",
    "sample-attribute-states": "/api/ordersampleinfomation/getAttributeStateList.ajax",
    "manage-list": "/api/adminExperiment/manage/list.ajax",
    "manage-get": "/api/adminExperiment/manage/get.ajax",
    "manage-save": "/api/adminExperiment/manage/save.ajax",
    "manage-del": "/api/adminExperiment/manage/del.ajax",
    "manage-update-status": "/api/adminExperiment/manage/updateStatus.ajax",
    "manage-options": "/api/adminExperiment/manage/options.ajax",
    "manage-pt-types": "/api/adminExperiment/manage/queryPtTypeAll.ajax",
    "project-list": "/api/adminExperiment/project/list.ajax",
    "project-get": "/api/adminExperiment/project/get.ajax",
    "project-save": "/api/adminExperiment/project/save.ajax",
    "project-del": "/api/adminExperiment/project/del.ajax",
    "goods-list": "/api/adminExperiment/goods/list.ajax",
    "goods-get": "/api/adminExperiment/goods/get.ajax",
    "goods-save": "/api/adminExperiment/goods/save.ajax",
    "goods-del": "/api/adminExperiment/goods/del.ajax",
    "brand-list": "/api/adminExperiment/brand/list.ajax",
    "brand-get": "/api/adminExperiment/brand/get.ajax",
    "brand-save": "/api/adminExperiment/brand/save.ajax",
    "brand-del": "/api/adminExperiment/brand/del.ajax",
    "brand-options": "/api/adminExperiment/brand/options.ajax",
    "sample-attr-list": "/api/adminExperiment/sampleAttr/list.ajax",
    "sample-attr-get": "/api/adminExperiment/sampleAttr/get.ajax",
    "sample-attr-save": "/api/adminExperiment/sampleAttr/save.ajax",
    "sample-attr-del": "/api/adminExperiment/sampleAttr/del.ajax",
    "sample-attr-update-status": "/api/adminExperiment/sampleAttr/updateStatus.ajax",
    "sample-attr-options": "/api/adminExperiment/sampleAttr/options.ajax",
}

FORWARDED_HEADERS = (
    "Authorization",
    "token",
    "X-Channel",
    "X-Request-ID",
    "Idempotency-Key",
    "X-Utoo-List-Scope",
    "X-Utoo-Audit-Validated",
)


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def mint_utoo_access_token(authorization: str | None, *, token_header: str | None = None) -> str | None:
    """青岛 mall JWT → 愉兔中台 access token；已是 access 则原样返回。"""
    raw = _extract_bearer(authorization) or (token_header or "").strip()
    if not raw:
        return None

    utoo_secret = getattr(settings, "UTOO_JWT_SECRET_KEY", "") or getattr(settings, "JWT_SECRET", "") or settings.SECRET_KEY

    try:
        utoo_claims = jwt.decode(
            raw,
            utoo_secret,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
        if utoo_claims.get("type") == "access" and utoo_claims.get("user_id"):
            return raw
    except jwt.PyJWTError:
        pass

    mall_secret = getattr(settings, "MALL_JWT_SECRET", "") or getattr(settings, "JWT_SECRET", "") or settings.SECRET_KEY
    issuer = getattr(settings, "MALL_JWT_ISSUER", "") or getattr(settings, "JWT_ISSUER", "qd-mall-identity")
    claims = None
    for attempt in (
        {"issuer": issuer, "options": {"require": ["exp", "sub"], "verify_iss": True}},
        {"options": {"require": ["exp", "sub"], "verify_iss": False}},
    ):
        try:
            claims = jwt.decode(raw, mall_secret, algorithms=["HS256"], **attempt)
            break
        except jwt.PyJWTError:
            continue
    if not claims:
        return raw

    user_id = str(claims.get("sub") or claims.get("user_id") or "").strip()
    if not user_id:
        return raw

    now = datetime.now(timezone.utc)
    ttl = int(getattr(settings, "UTOO_JWT_TTL_SECONDS", 1800))
    payload = {
        "user_id": user_id,
        "user_name": claims.get("user_name") or "",
        "true_name": claims.get("true_name") or claims.get("user_name") or "",
        "user_type": str(claims.get("type") or claims.get("user_type") or "0"),
        "dept_id": claims.get("dept_id") or "",
        "role_ids": claims.get("role_ids") or [],
        "account_kind": "sy_user",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
    }
    token = jwt.encode(payload, utoo_secret, algorithm="HS256")
    return token.decode("utf-8") if isinstance(token, bytes) else token


def pick_order_mid_base_url(*candidates: str) -> str:
    """显式配置才算有 order 中台；空串表示未配（调用方应 503，禁止 silent twin）。"""
    for raw in candidates:
        val = (raw or "").strip().rstrip("/")
        if val:
            return val
    return ""


def order_mid_configured() -> bool:
    return bool(_order_mid_base_url())


def _order_mid_base_url() -> str:
    return pick_order_mid_base_url(
        getattr(settings, "UTOO_ORDER_MID_SERVICE_URL", "") or "",
        getattr(settings, "UTOO_ORDER_SERVICE_URL", "") or "",
        getattr(settings, "SVC_ORDER_URL", "") or "",
    )


def _default_channel_for_path(path: str) -> str:
    if "/adminExperiment/" in path or path.startswith("/api/adminExperiment"):
        return "admin"
    return "mall_qd"


def _build_order_mid_headers(request, *, channel: str | None = None, path: str = "") -> dict[str, str]:
    headers = {name: request.headers[name] for name in FORWARDED_HEADERS if name in request.headers}
    headers.setdefault(
        "X-Channel",
        channel or _default_channel_for_path(path or getattr(request, "path", "") or ""),
    )
    headers.setdefault("X-Request-ID", uuid.uuid4().hex)
    if request.content_type:
        headers["Content-Type"] = request.content_type

    utoo_token = mint_utoo_access_token(
        request.headers.get("Authorization"),
        token_header=request.headers.get("token"),
    )
    if utoo_token:
        headers["Authorization"] = f"Bearer {utoo_token}"
        headers["token"] = utoo_token
    return headers


def _order_mid_timeout(path: str, *, resource: str | None = None) -> float:
    timeout = float(getattr(settings, "UTOO_ORDER_PROXY_TIMEOUT_SECONDS", 15))
    heavy = {
        "order-upload-file",
        "order-upload-file-alt",
        "order-download-file",
        "order-export",
        "order-upload-sub-invoice",
    }
    if resource in heavy:
        return max(timeout, 120.0)
    path_l = path.lower()
    if any(k in path_l for k in ("upload", "download", "export")):
        return max(timeout, 120.0)
    return timeout


def proxy_order_mid_path(request, path: str, *, channel: str | None = None, extra_headers: dict[str, str] | None = None):
    """按 platform/order 原始 .ajax 路径透明转发（utoo_biz / 网关兜底共用）。"""
    normalized = path if path.startswith("/") else f"/{path}"
    if not normalized.startswith("/api/"):
        normalized = f"/api/{normalized.lstrip('/')}"

    headers = _build_order_mid_headers(request, channel=channel, path=normalized)
    if extra_headers:
        headers.update(extra_headers)
    base_url = _order_mid_base_url()
    if not base_url:
        return Response(
            {
                "code": "utoo_order_unconfigured",
                "message": "订单中台未配置（UTOO_ORDER_MID_SERVICE_URL / UTOO_ORDER_SERVICE_URL / SVC_ORDER_URL）",
            },
            status=503,
        )
    timeout = _order_mid_timeout(normalized)

    try:
        upstream = httpx.request(
            request.method,
            f"{base_url}{normalized}",
            params=request.query_params,
            content=request.body or None,
            headers=headers,
            timeout=timeout,
            trust_env=False,
        )
    except httpx.HTTPError:
        return Response(
            {"code": "utoo_order_unavailable", "message": "愉兔订单中台不可用（请先启动 platform/order :18082）"},
            status=503,
        )

    content_type = upstream.headers.get("Content-Type", "application/json")
    response = HttpResponse(upstream.content, status=upstream.status_code, content_type=content_type)
    disposition = upstream.headers.get("Content-Disposition")
    if disposition:
        response["Content-Disposition"] = disposition
    return response


def proxy_utoo_order_request(request, resource: str):
    target_path = UTOO_ORDER_ENDPOINTS.get(resource)
    if not target_path:
        return Response({"code": "unknown_order_resource", "message": "不支持的愉兔订单资源"}, status=404)
    return proxy_order_mid_path(request, target_path)
