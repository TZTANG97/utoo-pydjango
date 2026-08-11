"""IOT 绑定 / 回调 / 代理查数 业务。"""
from __future__ import annotations

import json
import logging
from typing import Any

from apps.admin_experiment.repositories import sample_flow as sample_flow_repo
from apps.core.db_utils import fetch_one
from apps.iot import iot_client, repository as repo
from apps.iot.iot_client import IotClientError
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

_IOT_AUTH_TTL = 7 * 24 * 3600  # 秒：落库后默认 7 天，避免进详情反复授权


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


def _save_iot_session(staff: str, sess: dict[str, Any]) -> None:
    repo.upsert_iot_auth_session(
        staff_user_id=staff,
        access_token=str(sess.get("accessToken") or ""),
        refresh_token=str(sess.get("refreshToken") or ""),
        iot_user_id=str(sess.get("userId") or ""),
        iot_user_name=str(sess.get("userName") or ""),
        iot_true_name=str(sess.get("trueName") or ""),
        iot_dept_id=str(sess.get("deptId") or ""),
        ttl_seconds=_IOT_AUTH_TTL,
    )


def _load_iot_session(staff: str) -> dict[str, Any] | None:
    sess = repo.get_iot_auth_session(staff)
    if not isinstance(sess, dict) or not sess.get("accessToken"):
        return None
    return sess


def _clear_iot_session(staff: str) -> None:
    if staff:
        repo.delete_iot_auth_session(staff)


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
    device_id: str = "",
    child: dict[str, Any],
    order: dict[str, Any] | None,
    operator_user_id: str = "",
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
    base_cb = str(getattr(settings, "IOT_UTOO_CALLBACK_URL", "") or "").strip()
    if base_cb:
        callback = base_cb
    payload: dict[str, Any] = {
        "source": "utoo",
        "externalId": f"utoo:{order_id}:{child_id}",
        "orderId": order_id,
        "childId": child_id,
        "projectName": project[:255],
        "sampleSummary": sample,
        "callbackUrl": callback or None,
        "operatorUserId": (operator_user_id or "")[:64] or None,
    }
    # 设备改由 IOT 分配；空字符串表示未分配
    did = str(device_id or "").strip()
    if did:
        payload["deviceId"] = did
    else:
        payload["deviceId"] = ""
    return payload


def auth_iot_login(*, username: str, password: str, user: dict | None = None) -> dict[str, Any]:
    """用 IOT 运维账号登录，会话落库（不落密码）。"""
    staff = _staff_id(user)
    if not staff:
        raise ServiceError("未登录 UTOO", code="UNAUTHORIZED", http_status=401)
    name = str(username or "").strip()
    pwd = str(password or "")
    if not name or not pwd:
        raise ServiceError("请输入 IOT 运维账号和密码", code="IOT_AUTH_REQUIRED")
    try:
        resp = iot_client.login_ops(username=name, password=pwd)
    except IotClientError as exc:
        raise ServiceError(f"IOT 登录失败: {exc}", code="IOT_AUTH_FAIL", http_status=401) from exc
    if int(resp.get("statusCode") or 0) != 200 or not resp.get("access_token"):
        raise ServiceError(
            str(resp.get("message") or "IOT 用户名或密码错误"),
            code="IOT_AUTH_FAIL",
            http_status=401,
        )
    iot_user = resp.get("user") if isinstance(resp.get("user"), dict) else {}
    sess = {
        "accessToken": str(resp.get("access_token")),
        "refreshToken": str(resp.get("refresh_token") or ""),
        "userId": str(iot_user.get("user_id") or ""),
        "userName": str(iot_user.get("user_name") or name),
        "trueName": str(iot_user.get("true_name") or iot_user.get("user_name") or name),
        "deptId": str(iot_user.get("dept_id") or ""),
    }
    _save_iot_session(staff, sess)
    return {
        "authorized": True,
        "iotUserId": sess["userId"],
        "iotUserName": sess["userName"],
        "iotTrueName": sess["trueName"],
        "expiresIn": _IOT_AUTH_TTL,
    }


def auth_iot_status(*, user: dict | None = None) -> dict[str, Any]:
    staff = _staff_id(user)
    if not staff:
        return {"authorized": False}
    sess = _load_iot_session(staff)
    if not sess:
        return {"authorized": False}
    return {
        "authorized": True,
        "iotUserId": sess.get("userId") or "",
        "iotUserName": sess.get("userName") or "",
        "iotTrueName": sess.get("trueName") or "",
    }


def auth_iot_logout(*, user: dict | None = None) -> dict[str, Any]:
    staff = _staff_id(user)
    _clear_iot_session(staff)
    return {"authorized": False}


def _require_iot_session(user: dict | None) -> dict[str, Any]:
    staff = _staff_id(user)
    if not staff:
        raise ServiceError("未登录 UTOO", code="UNAUTHORIZED", http_status=401)
    sess = _load_iot_session(staff)
    if not sess:
        raise ServiceError(
            "请先授权 IOT 运维账号",
            code="IOT_AUTH_REQUIRED",
            http_status=401,
        )
    return sess


def list_devices(*, q: str = "", limit: int = 200, user: dict | None = None) -> dict[str, Any]:
    """代理拉取 IOT 设备列表（按已授权 IOT 账号权限过滤）。"""
    sess = _require_iot_session(user)
    try:
        resp = iot_client.list_devices(
            q=q, limit=limit, access_token=str(sess.get("accessToken") or "")
        )
    except IotClientError as exc:
        if exc.status in (401, 403):
            _clear_iot_session(_staff_id(user))
            raise ServiceError(
                "IOT 授权已失效，请重新登录 IOT 账号",
                code="IOT_AUTH_REQUIRED",
                http_status=401,
            ) from exc
        raise ServiceError(f"拉取 IOT 设备失败: {exc}", code="IOT_DEVICES_FAIL") from exc
    items = resp.get("list") if isinstance(resp, dict) else None
    if not isinstance(items, list):
        data = resp.get("data") if isinstance(resp, dict) else None
        items = data if isinstance(data, list) else []
    return {
        "list": items,
        "total": len(items),
        "iotUserName": sess.get("userName") or "",
        "iotTrueName": sess.get("trueName") or "",
    }


def _binding_blocks_redispatch(bind: dict[str, Any] | None) -> bool:
    """IOT 已接收的有效任务禁止重建；仅 unbound/aborted 或下发失败可再创建/重试。"""
    if not bind:
        return False
    bs = str(bind.get("bind_status") or "").strip()
    if bs in ("unbound", "aborted"):
        return False
    sync = str(bind.get("iot_task_sync_status") or "").strip()
    if sync == "failed":
        return False
    if bs == "running":
        return True
    has_task = bool(str(bind.get("iot_task_id") or "").strip())
    if has_task:
        return True
    return bs in ("task_created", "bound", "device_assigned", "finished")


def create_task(
    *,
    order_id: str,
    child_id: int,
    remark: str = "",
    user: dict | None = None,
) -> dict[str, Any]:
    """创建 IOT 试验任务（不选设备）；设备在 IOT 侧分配。"""
    repo.ensure_schema()
    sess = _require_iot_session(user)
    oid = str(order_id or "").strip()
    if not oid or not child_id:
        raise ServiceError("参数错误：orderId/childId 必填")

    child = repo.get_child(int(child_id))
    if not child:
        raise ServiceError("子单行不存在")

    cur = _child_status(child)
    if cur < sample_flow_repo.ST_PICK:
        raise ServiceError(
            f"请先完成样品领用后再创建试验任务(当前状态 {cur})",
            code="STATUS_CONFLICT",
            http_status=409,
        )

    # 绑定表 order_id 保留当前页业务单号（type=9/10 子单号），勿被产品行 order_form_id 父单覆盖
    order = repo.load_order_brief(business_order_id=oid)
    if order and order.get("id") is not None:
        order_pk = int(order["id"])
    else:
        order_pk = repo.resolve_order_pk(child)
        if not order:
            order = repo.load_order_brief(order_pk=order_pk)

    existing = repo.get_binding_by_child(int(child_id))
    if existing and str(existing.get("bind_status") or "") == "running":
        raise ServiceError("测试中禁止重建任务", code="STATUS_CONFLICT", http_status=409)
    if _binding_blocks_redispatch(existing):
        raise ServiceError(
            "任务已下发且 IOT 已接收，请先在 UTOO 或 IOT 取消后再重新创建",
            code="TASK_ACTIVE",
            http_status=409,
        )

    op_uid = str(sess.get("userId") or "")
    op_name = str(sess.get("trueName") or sess.get("userName") or "")
    # 创建/重建一律不带设备：试验箱由 IOT 侧分配，避免沿用绑定表旧 device
    device_id = ""

    try:
        resp = iot_client.register_task(
            _register_payload(
                order_id=oid,
                child_id=int(child_id),
                device_id=device_id,
                child=child,
                order=order,
                operator_user_id=op_uid,
            )
        )
    except IotClientError as exc:
        logger.warning("IOT register failed child=%s: %s", child_id, exc)
        # 记录失败态便于重试，但不视为创建成功
        repo.upsert_bind(
            order_id=oid,
            child_id=int(child_id),
            order_pk_id=order_pk,
            device_id=device_id,
            bind_status="task_created",
            bound_by=_staff_id(user),
            remark=remark or "create_task_fail",
            iot_operator_user_id=op_uid,
            iot_operator_name=op_name,
        )
        repo.update_task_sync(
            int(child_id),
            task_id=None,
            sync_status="failed",
            last_event=str(exc)[:64],
        )
        raise ServiceError(
            f"IOT 任务下发失败: {exc}",
            code="IOT_REGISTER_FAIL",
            http_status=502,
        ) from exc

    task_id = _extract_task_id(resp)
    if not task_id:
        raise ServiceError("IOT 未返回 taskId", code="IOT_REGISTER_FAIL", http_status=502)

    repo.upsert_bind(
        order_id=oid,
        child_id=int(child_id),
        order_pk_id=order_pk,
        device_id=device_id,
        bind_status="task_created",
        bound_by=_staff_id(user),
        remark=remark or "create_task",
        iot_operator_user_id=op_uid,
        iot_operator_name=op_name,
    )
    repo.update_task_sync(
        int(child_id),
        task_id=task_id,
        sync_status="ok",
        last_event="register_ok",
    )
    bind = repo.get_binding_by_child(int(child_id))
    out = repo.serialize_bind(bind) or {}
    out["registerMessage"] = "register_ok"
    out["iotTaskId"] = task_id
    return out


def bind_device(
    *,
    order_id: str,
    child_id: int,
    device_id: str = "",
    remark: str = "",
    user: dict | None = None,
) -> dict[str, Any]:
    """兼容旧接口：忽略 deviceId，改为 create_task。"""
    return create_task(
        order_id=order_id,
        child_id=child_id,
        remark=remark or "bind_compat",
        user=user,
    )


def build_sso_jump(
    *,
    user: dict | None = None,
    task_id: str = "",
    redirect: str = "",
) -> dict[str, Any]:
    """用已授权 IOT JWT 换一次性 ticket，返回运维端免登跳转 URL。"""
    sess = _require_iot_session(user)
    access = str(sess.get("accessToken") or "").strip()
    if not access:
        raise ServiceError(
            "请先授权 IOT 运维账号",
            code="IOT_AUTH_REQUIRED",
            http_status=401,
        )
    try:
        resp = iot_client.create_sso_ticket(
            access_token=access,
            refresh_token=str(sess.get("refreshToken") or ""),
            user={
                "user_id": sess.get("userId") or "",
                "user_name": sess.get("userName") or "",
                "true_name": sess.get("trueName") or "",
                "user_type": "0",
                "dept_id": sess.get("deptId") or "",
            },
        )
    except IotClientError as exc:
        if exc.status in (401, 403):
            _clear_iot_session(_staff_id(user))
            raise ServiceError(
                "IOT 授权已失效，请重新登录 IOT 账号",
                code="IOT_AUTH_REQUIRED",
                http_status=401,
            ) from exc
        raise ServiceError(f"换取免登 ticket 失败: {exc}", code="IOT_SSO_FAIL") from exc

    ticket = str(resp.get("ticket") or (resp.get("data") or {}).get("ticket") or "").strip()
    if not ticket:
        raise ServiceError("IOT 未返回 ticket", code="IOT_SSO_FAIL")

    web = _resolve_iot_web_base()
    if not web:
        raise ServiceError("IOT_WEB_URL 未配置", code="CONFIG")

    tid = str(task_id or "").strip()
    redir = str(redirect or "").strip()
    if not redir:
        # vue-router 路径不含 /app 前缀（BASE_URL 已处理）
        redir = f"/main/utoo-tasks?taskId={tid}" if tid else "/main/utoo-tasks"
    from urllib.parse import quote

    jump = f"{web}/sso?ticket={quote(ticket)}&redirect={quote(redir)}"
    return {"jumpUrl": jump, "ticket": ticket, "redirect": redir}


def _resolve_iot_web_base() -> str:
    """运维前端根地址。UAT/正式 nginx 静态资源在 /app/，勿用裸域名。"""
    web = str(getattr(settings, "IOT_WEB_URL", "") or getattr(settings, "IOT_BASE_URL", "") or "").rstrip("/")
    if not web:
        return ""
    # 已是 /app 结尾，或本地 Vite，保持原样
    if web.endswith("/app") or "127.0.0.1" in web or "localhost" in web:
        return web
    # laidecloud 部署：根路径 /sso 会打到 FastAPI 404，必须走 /app/sso
    if "laidecloud.com" in web:
        return f"{web}/app"
    return web


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


def list_order_task_overview(*, order_id: str) -> dict[str, Any]:
    """一单多产品行 IOT 任务总览。"""
    repo.ensure_schema()
    oid = str(order_id or "").strip()
    if not oid:
        raise ServiceError("参数错误：orderId 必填")
    children = repo.list_children_by_business_order(oid)
    child_ids = [int(c["id"]) for c in children if c.get("id") is not None]
    bind_rows = repo.list_bindings_by_child_ids(child_ids)
    # 同一 child 只取最新（list 无序时再按 id）
    bind_by_child: dict[int, dict[str, Any]] = {}
    for row in sorted(bind_rows, key=lambda r: int(r.get("id") or 0)):
        try:
            bind_by_child[int(row["child_id"])] = row
        except (TypeError, ValueError, KeyError):
            continue
    items: list[dict[str, Any]] = []
    for child in children:
        cid = int(child["id"])
        raw_bind = bind_by_child.get(cid)
        bind = repo.serialize_bind(raw_bind)
        line_status = _child_status(child)
        bs = str((bind or {}).get("bindStatus") or "")
        sync = str((bind or {}).get("iotTaskSyncStatus") or "")
        # 已领用且无有效 IOT 任务（或已取消/失败）才可创建
        can_create = (
            line_status >= sample_flow_repo.ST_PICK
            and bs != "running"
            and not _binding_blocks_redispatch(raw_bind)
        )
        # 重新下发仅用于「IOT 未成功接收」的失败重试
        can_resync = sync == "failed" and bs not in ("running", "unbound")
        items.append(
            {
                "childId": cid,
                "childOrderId": child.get("childOrderId") or "",
                "goodsName": child.get("goodsName") or "",
                "projectName": child.get("projectName") or "",
                "lineStatus": line_status,
                "canCreate": can_create,
                "canResync": can_resync,
                "binding": bind,
            }
        )
    return {"orderId": oid, "total": len(items), "items": items}


def create_tasks_batch(
    *,
    order_id: str,
    child_ids: list[int] | None = None,
    remark: str = "",
    user: dict | None = None,
) -> dict[str, Any]:
    """批量创建试验任务；childIds 为空则对本单全部可创建产品行执行。"""
    _require_iot_session(user)
    oid = str(order_id or "").strip()
    if not oid:
        raise ServiceError("参数错误：orderId 必填")
    overview = list_order_task_overview(order_id=oid)
    wanted: set[int] | None = None
    if child_ids:
        wanted = {int(x) for x in child_ids if x is not None}
    targets: list[int] = []
    for row in overview.get("items") or []:
        cid = int(row["childId"])
        if wanted is not None and cid not in wanted:
            continue
        if wanted is None and not row.get("canCreate"):
            continue
        targets.append(cid)
    if wanted is not None and not targets:
        raise ServiceError("未选中有效产品行", code="NO_CHILD")
    if not targets:
        raise ServiceError("没有可创建试验任务的产品行（需已领用且非测试中）", code="NO_ELIGIBLE")

    items: list[dict[str, Any]] = []
    ok_n = 0
    for cid in targets:
        try:
            bind = create_task(
                order_id=oid,
                child_id=cid,
                remark=remark or "batch_create",
                user=user,
            )
            ok_n += 1
            items.append({"childId": cid, "ok": True, "bind": bind})
        except ServiceError as exc:
            items.append(
                {
                    "childId": cid,
                    "ok": False,
                    "code": exc.code,
                    "message": exc.message,
                }
            )
    return {
        "orderId": oid,
        "total": len(targets),
        "success": ok_n,
        "failed": len(targets) - ok_n,
        "items": items,
    }


def resync_tasks_batch(
    *,
    order_id: str,
    child_ids: list[int] | None = None,
    user: dict | None = None,
) -> dict[str, Any]:
    """批量重新下发；childIds 为空则对本单已有任务且可下发的产品行执行。"""
    _require_iot_session(user)
    oid = str(order_id or "").strip()
    if not oid:
        raise ServiceError("参数错误：orderId 必填")
    overview = list_order_task_overview(order_id=oid)
    wanted: set[int] | None = None
    if child_ids:
        wanted = {int(x) for x in child_ids if x is not None}
    targets: list[int] = []
    for row in overview.get("items") or []:
        cid = int(row["childId"])
        if wanted is not None and cid not in wanted:
            continue
        if wanted is None and not row.get("canResync"):
            continue
        targets.append(cid)
    if not targets:
        raise ServiceError("没有可重新下发的产品行", code="NO_ELIGIBLE")

    items: list[dict[str, Any]] = []
    ok_n = 0
    for cid in targets:
        try:
            bind = resync_device(order_id=oid, child_id=cid, user=user)
            ok_n += 1
            items.append({"childId": cid, "ok": True, "bind": bind})
        except ServiceError as exc:
            items.append(
                {
                    "childId": cid,
                    "ok": False,
                    "code": exc.code,
                    "message": exc.message,
                }
            )
    return {
        "orderId": oid,
        "total": len(targets),
        "success": ok_n,
        "failed": len(targets) - ok_n,
        "items": items,
    }


def resync_device(*, order_id: str = "", child_id: int, user: dict | None = None) -> dict[str, Any]:
    """仅对下发失败的任务重试注册；IOT 已接收的不可重发。"""
    repo.ensure_schema()
    _require_iot_session(user)
    bind = repo.get_binding_by_child(int(child_id))
    if not bind or str(bind.get("bind_status") or "") == "unbound":
        raise ServiceError("未找到有效任务绑定", code="BIND_NOT_FOUND", http_status=404)
    if str(bind.get("bind_status") or "") == "running":
        raise ServiceError("测试中禁止重新下发", code="STATUS_CONFLICT", http_status=409)
    sync = str(bind.get("iot_task_sync_status") or "").strip()
    if sync != "failed":
        raise ServiceError(
            "任务已下发且 IOT 已接收，请先在 UTOO 或 IOT 取消后再重新创建",
            code="TASK_ACTIVE",
            http_status=409,
        )
    child = repo.get_child(int(child_id))
    if not child:
        raise ServiceError("子单行不存在")
    oid = str(order_id or bind.get("order_id") or "").strip()
    # 失败重试也不带旧设备，由 IOT 重新分配
    did = ""
    order = repo.load_order_brief(
        order_pk=bind.get("order_pk_id"),
        business_order_id=oid,
    )
    try:
        resp = iot_client.register_task(
            _register_payload(
                order_id=oid,
                child_id=int(child_id),
                device_id=did,
                child=child,
                order=order,
                operator_user_id=str(bind.get("iot_operator_user_id") or ""),
            )
        )
    except IotClientError as exc:
        logger.warning("IOT resync failed child=%s: %s", child_id, exc)
        repo.update_task_sync(
            int(child_id),
            task_id=None,
            sync_status="failed",
            last_event=str(exc)[:64],
        )
        raise ServiceError(
            f"IOT 重新下发失败: {exc}",
            code="IOT_REGISTER_FAIL",
            http_status=502,
        ) from exc
    task_id = _extract_task_id(resp) or str(bind.get("iot_task_id") or "")
    if not task_id:
        raise ServiceError("IOT 未返回 taskId", code="IOT_REGISTER_FAIL", http_status=502)
    repo.update_task_sync(
        int(child_id),
        task_id=task_id,
        sync_status="ok",
        last_event="resync_ok",
    )
    out = repo.serialize_bind(repo.get_binding_by_child(int(child_id))) or {}
    out["registerMessage"] = "resync_ok"
    out["iotTaskId"] = task_id
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
    if e in (
        "experiment.cancelled",
        "cancelled",
        "cancel",
        "task.cancelled",
        "task_cancelled",
    ):
        return "cancelled"
    if e in ("device.assigned", "device_assigned", "deviceassigned", "assigned"):
        return "device_assigned"
    return e


def _child_status(child: dict[str, Any] | None) -> int:
    try:
        return int((child or {}).get("orderStatus") or 0)
    except (TypeError, ValueError):
        return 0


@transaction.atomic
def handle_experiment_event(payload: dict[str, Any]) -> dict[str, Any]:
    """处理 IOT 回调；先改状态成功再写 eventId 幂等，避免毒化重试。"""
    repo.ensure_schema()
    event_raw = str(payload.get("event") or "")
    event = _normalize_event(event_raw)
    event_id = str(payload.get("eventId") or "").strip()
    summary = f"{event_raw}:{payload.get('iotTaskId') or ''}:{payload.get('deviceId') or ''}"[:512]

    # 已成功处理过：直接幂等返回当前状态
    if event_id:
        existed = fetch_one(
            "SELECT event_id FROM iot_callback_event WHERE event_id = %(id)s LIMIT 1",
            {"id": event_id},
        )
        if existed:
            bind = _locate_bind(payload)
            line_status = None
            if bind:
                child = repo.get_child(int(bind["child_id"]))
                line_status = _child_status(child)
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
    cur = _child_status(child)

    if event == "device_assigned":
        did = str(payload.get("deviceId") or "").strip()
        if not did:
            raise ServiceError("deviceAssigned 缺少 deviceId", code="FAIL", http_status=400)
        repo.update_device_assigned(child_id, device_id=did)
        if task_id:
            repo.update_task_sync(
                child_id,
                task_id=task_id,
                sync_status="ok",
                last_event="device_assigned",
            )
        line_status = cur
    elif event == "started":
        # 已在测试中：幂等成功
        if cur == sample_flow_repo.ST_TESTING:
            repo.update_from_callback(
                child_id,
                bind_status="running",
                event=event_raw or "experiment.started",
                run_id=run_id,
                data_ref=data_ref,
                task_id=task_id,
            )
            line_status = sample_flow_repo.ST_TESTING
        else:
            # 到货未领用：自动领用到 37
            if cur == sample_flow_repo.ST_ARRIVE:
                ok_pick, msg_pick = sample_flow_repo.sample_pick(
                    order_id=order_pk_int,
                    child_ids=[child_id],
                    staff_user_id="iot",
                )
                if not ok_pick:
                    raise ServiceError(
                        msg_pick or "自动领用失败",
                        code="STATUS_CONFLICT",
                        http_status=409,
                    )
                child = repo.get_child(child_id) or child
                cur = _child_status(child)
            if cur != sample_flow_repo.ST_PICK and cur != sample_flow_repo.ST_TESTING:
                raise ServiceError(
                    f"子单状态不可开始测试(当前 {cur}，需要 37/38)",
                    code="STATUS_CONFLICT",
                    http_status=409,
                )
            if cur == sample_flow_repo.ST_PICK:
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
        if cur == sample_flow_repo.ST_TEST_DONE:
            repo.update_from_callback(
                child_id,
                bind_status="finished",
                event=event_raw or "experiment.finished",
                run_id=run_id,
                data_ref=data_ref,
                task_id=task_id,
            )
            line_status = sample_flow_repo.ST_TEST_DONE
        else:
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
        line_status = _child_status(child2)
        if not ok:
            logger.warning("aborted test_end soft-fail child=%s: %s", child_id, msg)
    elif event == "cancelled":
        # IOT 端取消：释放 UTOO 绑定，之后可重新创建下发
        if str(bind.get("bind_status") or "") == "running":
            raise ServiceError("测试中禁止取消", code="STATUS_CONFLICT", http_status=409)
        repo.update_from_callback(
            child_id,
            bind_status="unbound",
            event=event_raw or "experiment.cancelled",
            run_id=run_id,
            data_ref=data_ref,
            task_id=task_id,
        )
        child2 = repo.get_child(child_id)
        line_status = _child_status(child2)
    else:
        raise ServiceError(f"未知事件: {event_raw}", code="FAIL", http_status=400)

    # 状态成功后再记幂等，失败回滚不会毒化 eventId
    if event_id:
        inserted = repo.try_insert_callback_event(event_id, summary)
        if not inserted:
            # 并发双成功：仍返回 ok
            pass

    return {
        "ok": True,
        "duplicated": False,
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

    # C 端客户校验归属；员工(sy_user)联调/代查跳过
    from apps.auth_support.helpers import is_exp_customer

    if is_exp_customer(user) and not repo.user_owns_order(
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
