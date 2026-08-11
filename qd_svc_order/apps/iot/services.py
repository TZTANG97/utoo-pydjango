"""IOT 绑定 / 回调 / 代理查数 业务。"""
from __future__ import annotations

import json
import logging
from typing import Any

from apps.admin_experiment.repositories import sample_flow as sample_flow_repo
from apps.iot import iot_client, repository as repo
from apps.iot.iot_client import IotClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, message: str, *, code: str = "FAIL", http_status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


def _staff_id(user: dict | None) -> str:
    if not isinstance(user, dict):
        return ""
    return str(user.get("user_id") or user.get("id") or user.get("userId") or "").strip()


def _extract_task_id(resp: dict[str, Any]) -> str:
    if not isinstance(resp, dict):
        return ""
    for key in ("taskId", "iotTaskId", "id"):
        v = resp.get(key)
        if v not in (None, ""):
            return str(v)
    data = resp.get("data")
    if isinstance(data, dict):
        for key in ("taskId", "iotTaskId", "id"):
            v = data.get(key)
            if v not in (None, ""):
                return str(v)
    return ""


def _register_payload(
    *,
    order_id: str,
    child_id: int,
    device_id: str,
    child: dict[str, Any],
    order: dict[str, Any] | None,
) -> dict[str, Any]:
    project = str(
        child.get("projectName")
        or child.get("goodsName")
        or (order or {}).get("projectName")
        or (order or {}).get("goodsName")
        or ""
    )
    sample = str(child.get("sampleId") or child.get("goodsName") or "")[:500]
    callback = ""
    # 可选：由环境拼回调；IOT 也可用自身 UTOO_CALLBACK_URL
    base_cb = str(getattr(settings, "IOT_UTOO_CALLBACK_URL", "") or "").strip()
    if base_cb:
        callback = base_cb
    return {
        "source": "utoo",
        "externalId": f"utoo:{order_id}:{child_id}",
        "orderId": order_id,
        "childId": child_id,
        "deviceId": device_id,
        "projectName": project[:255],
        "sampleSummary": sample,
        "callbackUrl": callback or None,
    }


def bind_device(
    *,
    order_id: str,
    child_id: int,
    device_id: str,
    remark: str = "",
    user: dict | None = None,
) -> dict[str, Any]:
    repo.ensure_schema()
    oid = str(order_id or "").strip()
    did = str(device_id or "").strip()
    if not oid or not child_id or not did:
        raise ServiceError("参数错误：orderId/childId/deviceId 必填")

    child = repo.get_child(int(child_id))
    if not child:
        raise ServiceError("子单行不存在")

    # sample_flow 归属校验用 order_form_id；order_id 列若为数字 FK 也可作回退
    order_pk = repo.resolve_order_pk(child)

    order = repo.load_order_brief(order_pk=order_pk, business_order_id=oid)
    if order and not oid:
        oid = str(order.get("orderId") or oid)
    if order and order.get("orderId"):
        oid = str(order.get("orderId"))

    existing = repo.get_binding_by_child(int(child_id))
    if existing and str(existing.get("bind_status") or "") in ("running", "finished"):
        st = str(existing.get("bind_status"))
        if st == "running":
            raise ServiceError("测试中禁止换绑，请先结束或解绑", code="STATUS_CONFLICT", http_status=409)

    repo.upsert_bind(
        order_id=oid,
        child_id=int(child_id),
        order_pk_id=order_pk,
        device_id=did,
        bound_by=_staff_id(user),
        remark=remark or "bind",
    )

    sync_status = "failed"
    task_id = ""
    sync_msg = ""
    try:
        resp = iot_client.register_task(
            _register_payload(
                order_id=oid,
                child_id=int(child_id),
                device_id=did,
                child=child,
                order=order,
            )
        )
        task_id = _extract_task_id(resp)
        sync_status = "ok"
        sync_msg = "register_ok"
    except IotClientError as exc:
        sync_msg = str(exc)[:200]
        logger.warning("IOT register failed child=%s: %s", child_id, exc)

    repo.update_task_sync(
        int(child_id),
        task_id=task_id or None,
        sync_status=sync_status,
        last_event=sync_msg,
    )
    bind = repo.get_binding_by_child(int(child_id))
    out = repo.serialize_bind(bind) or {}
    out["registerMessage"] = sync_msg
    return out


def unbind_device(*, order_id: str = "", child_id: int, user: dict | None = None) -> dict[str, Any]:
    repo.ensure_schema()
    bind = repo.get_binding_by_child(int(child_id))
    if not bind:
        raise ServiceError("未找到绑定", code="BIND_NOT_FOUND", http_status=404)
    if str(bind.get("bind_status") or "") == "running":
        raise ServiceError("测试中禁止解绑", code="STATUS_CONFLICT", http_status=409)

    task_id = str(bind.get("iot_task_id") or "").strip()
    if task_id:
        try:
            iot_client.cancel_task(
                {
                    "taskId": task_id,
                    "orderId": bind.get("order_id"),
                    "childId": child_id,
                    "deviceId": bind.get("iot_device_id"),
                }
            )
        except IotClientError as exc:
            logger.warning("IOT cancel failed child=%s: %s", child_id, exc)

    repo.mark_unbound(int(child_id))
    return repo.serialize_bind(repo.get_binding_by_child(int(child_id))) or {}


def get_binding(*, order_id: str = "", child_id: int) -> dict[str, Any] | None:
    repo.ensure_schema()
    return repo.serialize_bind(repo.get_binding_by_child(int(child_id)))


def resync_device(*, order_id: str = "", child_id: int, user: dict | None = None) -> dict[str, Any]:
    repo.ensure_schema()
    bind = repo.get_binding_by_child(int(child_id))
    if not bind or str(bind.get("bind_status") or "") == "unbound":
        raise ServiceError("未找到有效绑定", code="BIND_NOT_FOUND", http_status=404)
    child = repo.get_child(int(child_id))
    if not child:
        raise ServiceError("子单行不存在")
    oid = str(order_id or bind.get("order_id") or "").strip()
    did = str(bind.get("iot_device_id") or "").strip()
    order = repo.load_order_brief(
        order_pk=bind.get("order_pk_id"),
        business_order_id=oid,
    )
    sync_status = "failed"
    task_id = ""
    sync_msg = ""
    try:
        resp = iot_client.register_task(
            _register_payload(
                order_id=oid,
                child_id=int(child_id),
                device_id=did,
                child=child,
                order=order,
            )
        )
        task_id = _extract_task_id(resp) or str(bind.get("iot_task_id") or "")
        sync_status = "ok"
        sync_msg = "resync_ok"
    except IotClientError as exc:
        sync_msg = str(exc)[:200]
        logger.warning("IOT resync failed child=%s: %s", child_id, exc)
    repo.update_task_sync(
        int(child_id),
        task_id=task_id or None,
        sync_status=sync_status,
        last_event=sync_msg,
    )
    out = repo.serialize_bind(repo.get_binding_by_child(int(child_id))) or {}
    out["registerMessage"] = sync_msg
    return out


def _locate_bind(payload: dict[str, Any]) -> dict[str, Any] | None:
    task_id = str(payload.get("iotTaskId") or payload.get("taskId") or "").strip()
    if task_id:
        bind = repo.get_binding_by_task(task_id)
        if bind:
            return bind
    utoo = payload.get("utoo") if isinstance(payload.get("utoo"), dict) else {}
    child_id = utoo.get("childId") or payload.get("childId")
    if child_id not in (None, ""):
        try:
            bind = repo.get_binding_by_child(int(child_id))
            if bind:
                return bind
        except (TypeError, ValueError):
            pass
    order_id = str(utoo.get("orderId") or payload.get("orderId") or "").strip()
    device_id = str(payload.get("deviceId") or "").strip()
    if order_id and device_id:
        return repo.get_binding_by_order_device(order_id, device_id)
    return None


def _normalize_event(event: str) -> str:
    e = str(event or "").strip().lower()
    if e in ("experiment.started", "started", "start"):
        return "started"
    if e in ("experiment.finished", "finished", "finish", "end"):
        return "finished"
    if e in ("experiment.aborted", "aborted", "abort"):
        return "aborted"
    return e


def handle_experiment_event(payload: dict[str, Any]) -> dict[str, Any]:
    """处理 IOT 回调；返回 body + http_status。"""
    repo.ensure_schema()
    event_raw = str(payload.get("event") or "")
    event = _normalize_event(event_raw)
    event_id = str(payload.get("eventId") or "").strip()
    summary = f"{event_raw}:{payload.get('iotTaskId') or ''}:{payload.get('deviceId') or ''}"[:512]

    duplicated = False
    if event_id:
        inserted = repo.try_insert_callback_event(event_id, summary)
        if not inserted:
            duplicated = True
            bind = _locate_bind(payload)
            line_status = None
            if bind:
                child = repo.get_child(int(bind["child_id"]))
                if child:
                    try:
                        line_status = int(child.get("orderStatus") or 0)
                    except (TypeError, ValueError):
                        line_status = None
            return {
                "ok": True,
                "duplicated": True,
                "lineStatus": line_status,
                "http_status": 200,
            }

    bind = _locate_bind(payload)
    if not bind or str(bind.get("bind_status") or "") == "unbound":
        raise ServiceError("未找到绑定", code="BIND_NOT_FOUND", http_status=404)

    child_id = int(bind["child_id"])
    child = repo.get_child(child_id)
    if not child:
        raise ServiceError("子单行不存在", code="BIND_NOT_FOUND", http_status=404)

    order_pk = bind.get("order_pk_id")
    if order_pk in (None, "", 0, "0"):
        order_pk = repo.resolve_order_pk(child)
    try:
        order_pk_int = int(order_pk) if order_pk not in (None, "") else 0
    except (TypeError, ValueError):
        order_pk_int = 0
    if not order_pk_int:
        raise ServiceError("无法解析订单主键", code="BIND_NOT_FOUND", http_status=404)

    device_id = str(payload.get("deviceId") or bind.get("iot_device_id") or "")
    run_id = str(payload.get("iotRunId") or payload.get("runId") or "").strip() or None
    data_ref = payload.get("dataRef")
    task_id = str(payload.get("iotTaskId") or payload.get("taskId") or "").strip() or None
    line_status = None

    if event == "started":
        line_id = str(child.get("lineId") or "").strip()
        if not line_id:
            line_id = f"IOT-{device_id}"[:64]
            repo.update_child_line_id(child_id, line_id)
        ok, msg = sample_flow_repo.test_start(
            order_id=order_pk_int,
            child_ids=[child_id],
            line_id=line_id,
            staff_user_id="iot",
        )
        if not ok:
            raise ServiceError(msg or "状态冲突", code="STATUS_CONFLICT", http_status=409)
        repo.update_from_callback(
            child_id,
            bind_status="running",
            event=event_raw or "experiment.started",
            run_id=run_id,
            data_ref=data_ref,
            task_id=task_id,
        )
        line_status = sample_flow_repo.ST_TESTING
    elif event == "finished":
        ok, msg = sample_flow_repo.test_end(
            order_id=order_pk_int,
            child_ids=[child_id],
            staff_user_id="iot",
        )
        if not ok:
            raise ServiceError(msg or "状态冲突", code="STATUS_CONFLICT", http_status=409)
        repo.update_from_callback(
            child_id,
            bind_status="finished",
            event=event_raw or "experiment.finished",
            run_id=run_id,
            data_ref=data_ref,
            task_id=task_id,
        )
        line_status = sample_flow_repo.ST_TEST_DONE
    elif event == "aborted":
        # 中止：尽量结束测试；失败只记绑定状态
        ok, msg = sample_flow_repo.test_end(
            order_id=order_pk_int,
            child_ids=[child_id],
            staff_user_id="iot",
        )
        repo.update_from_callback(
            child_id,
            bind_status="aborted",
            event=event_raw or "experiment.aborted",
            run_id=run_id,
            data_ref=data_ref,
            task_id=task_id,
        )
        child2 = repo.get_child(child_id)
        try:
            line_status = int((child2 or {}).get("orderStatus") or 0)
        except (TypeError, ValueError):
            line_status = None
        if not ok:
            logger.warning("aborted test_end soft-fail child=%s: %s", child_id, msg)
    else:
        raise ServiceError(f"未知事件: {event_raw}", code="FAIL", http_status=400)

    return {
        "ok": True,
        "duplicated": duplicated,
        "lineStatus": line_status,
        "http_status": 200,
    }


def get_experiment_data(
    *,
    user: dict,
    order_id: str = "",
    child_id: int | None = None,
    include_series: bool = False,
) -> dict[str, Any]:
    from apps.orders.repositories import orders as order_repo

    repo.ensure_schema()
    uid = int(user.get("user_id") or user.get("id") or 0)
    if not uid:
        raise ServiceError("未登录", code="UNAUTHORIZED", http_status=401)
    _, mobile = order_repo.user_context(uid)

    bind = None
    if child_id:
        bind = repo.get_binding_by_child(int(child_id))
    if not bind and order_id:
        # 取该单最新一条非 unbound
        from apps.core.db_utils import fetch_one

        bind = fetch_one(
            """
            SELECT * FROM experiment_order_iot_bind
            WHERE order_id = %(oid)s AND bind_status <> 'unbound'
            ORDER BY id DESC LIMIT 1
            """,
            {"oid": str(order_id)},
        )
    if not bind:
        raise ServiceError("未找到绑定", code="BIND_NOT_FOUND", http_status=404)

    order_pk = bind.get("order_pk_id")
    business_id = str(bind.get("order_id") or order_id or "")
    try:
        order_pk_int = int(order_pk) if order_pk not in (None, "") else None
    except (TypeError, ValueError):
        order_pk_int = None

    if not repo.user_owns_order(
        user_id=uid,
        mobile=mobile or "",
        order_pk=order_pk_int,
        business_order_id=business_id,
    ):
        raise ServiceError("无权查看该订单", code="FORBIDDEN", http_status=403)

    run_id = str(bind.get("iot_run_id") or "").strip()
    if not run_id and bind.get("iot_data_ref"):
        ref = bind.get("iot_data_ref")
        try:
            parsed = json.loads(ref) if isinstance(ref, str) else ref
            if isinstance(parsed, dict):
                run_id = str(parsed.get("id") or parsed.get("runId") or "").strip()
        except Exception:
            pass
    if not run_id:
        raise ServiceError("尚无试验运行数据", code="RUN_NOT_READY", http_status=404)

    try:
        data = iot_client.get_run(run_id, include_series=include_series)
    except IotClientError as exc:
        raise ServiceError(str(exc), code="IOT_UPSTREAM", http_status=502) from exc

    return {
        "orderId": business_id,
        "childId": bind.get("child_id"),
        "iotRunId": run_id,
        "iotDataRef": bind.get("iot_data_ref"),
        "bindStatus": bind.get("bind_status"),
        "run": data,
    }
