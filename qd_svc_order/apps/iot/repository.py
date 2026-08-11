"""IOT 绑定表 / 幂等表仓储（MySQL，ensure_schema IF NOT EXISTS）。"""
from __future__ import annotations

import json
import logging
from typing import Any

from apps.core.db_utils import execute, execute_insert, fetch_all, fetch_one

logger = logging.getLogger(__name__)

_SCHEMA_READY = False


def ensure_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    execute(
        """
        CREATE TABLE IF NOT EXISTS experiment_order_iot_bind (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            order_id VARCHAR(64) NOT NULL COMMENT '业务单号',
            child_id BIGINT NOT NULL COMMENT '产品行 id',
            order_pk_id BIGINT NULL COMMENT 'experiment_order.id',
            iot_device_id VARCHAR(128) NOT NULL DEFAULT '',
            bind_status VARCHAR(32) NOT NULL DEFAULT 'bound',
            iot_task_id VARCHAR(128) NULL,
            iot_task_sync_status VARCHAR(32) NULL DEFAULT '',
            iot_run_id VARCHAR(128) NULL,
            iot_data_ref TEXT NULL,
            last_event VARCHAR(64) NULL,
            last_sync_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            bound_by VARCHAR(64) NULL,
            iot_operator_user_id VARCHAR(64) NULL DEFAULT '',
            iot_operator_name VARCHAR(128) NULL DEFAULT '',
            UNIQUE KEY uk_child_id (child_id),
            KEY idx_order_id (order_id),
            KEY idx_device (iot_device_id),
            KEY idx_task (iot_task_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS iot_callback_event (
            event_id VARCHAR(128) NOT NULL PRIMARY KEY,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payload_summary VARCHAR(512) NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    for col, ddl in (
        ("iot_operator_user_id", "VARCHAR(64) NULL DEFAULT ''"),
        ("iot_operator_name", "VARCHAR(128) NULL DEFAULT ''"),
    ):
        try:
            execute(f"ALTER TABLE experiment_order_iot_bind ADD COLUMN {col} {ddl}")
        except Exception:
            pass
    _SCHEMA_READY = True


def get_child(child_id: int) -> dict[str, Any] | None:
    return fetch_one(
        """
        SELECT
            c.id,
            c.order_id AS orderIdCol,
            c.order_form_id AS orderFormId,
            c.line_id AS lineId,
            c.order_status AS orderStatus,
            c.goods_name AS goodsName,
            c.experiment_project_name AS projectName,
            c.sample_id AS sampleId
        FROM experiment_order_child c
        WHERE c.id = %(id)s AND IFNULL(c.delete_status, 2) <> 1
        LIMIT 1
        """,
        {"id": child_id},
    )


def resolve_order_pk(child: dict[str, Any] | None) -> int | None:
    """sample_flow 使用 experiment_order.id；优先 order_form_id，其次数字 order_id。"""
    if not child:
        return None
    for key in ("orderFormId", "order_form_id"):
        raw = child.get(key)
        if raw not in (None, "", 0, "0"):
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    for key in ("orderIdCol", "order_id"):
        raw = child.get(key)
        if raw not in (None, ""):
            text = str(raw).strip()
            if text.isdigit():
                return int(text)
    return None


def load_order_brief(order_pk: int | None = None, business_order_id: str = "") -> dict[str, Any] | None:
    # 主单无 goods_name/project_name；品名在 experiment_order_child
    if order_pk:
        row = fetch_one(
            """
            SELECT id, order_id AS orderId, custom_user_id AS customUserId, mobile
            FROM experiment_order
            WHERE id = %(id)s
            LIMIT 1
            """,
            {"id": order_pk},
        )
        if row:
            return row
    oid = str(business_order_id or "").strip()
    if not oid:
        return None
    return fetch_one(
        """
        SELECT id, order_id AS orderId, custom_user_id AS customUserId, mobile
        FROM experiment_order
        WHERE order_id = %(oid)s
        LIMIT 1
        """,
        {"oid": oid},
    )


def get_binding_by_child(child_id: int) -> dict[str, Any] | None:
    ensure_schema()
    return fetch_one(
        """
        SELECT *
        FROM experiment_order_iot_bind
        WHERE child_id = %(cid)s
        LIMIT 1
        """,
        {"cid": child_id},
    )


def get_binding_by_task(iot_task_id: str) -> dict[str, Any] | None:
    ensure_schema()
    tid = str(iot_task_id or "").strip()
    if not tid:
        return None
    return fetch_one(
        """
        SELECT *
        FROM experiment_order_iot_bind
        WHERE iot_task_id = %(tid)s
        ORDER BY id DESC
        LIMIT 1
        """,
        {"tid": tid},
    )


def get_binding_by_order_device(order_id: str, device_id: str) -> dict[str, Any] | None:
    ensure_schema()
    return fetch_one(
        """
        SELECT *
        FROM experiment_order_iot_bind
        WHERE order_id = %(oid)s AND iot_device_id = %(did)s
          AND bind_status <> 'unbound'
        ORDER BY id DESC
        LIMIT 1
        """,
        {"oid": str(order_id), "did": str(device_id)},
    )


def upsert_bind(
    *,
    order_id: str,
    child_id: int,
    order_pk_id: int | None,
    device_id: str,
    bound_by: str = "",
    remark: str = "",
    iot_operator_user_id: str = "",
    iot_operator_name: str = "",
) -> int:
    ensure_schema()
    existing = get_binding_by_child(child_id)
    if existing:
        execute(
            """
            UPDATE experiment_order_iot_bind
            SET order_id = %(oid)s,
                order_pk_id = %(pk)s,
                iot_device_id = %(did)s,
                bind_status = 'bound',
                iot_task_sync_status = '',
                last_event = %(ev)s,
                bound_by = %(by)s,
                iot_operator_user_id = %(op_uid)s,
                iot_operator_name = %(op_name)s,
                updated_at = NOW()
            WHERE child_id = %(cid)s
            """,
            {
                "oid": order_id,
                "pk": order_pk_id,
                "did": device_id,
                "ev": (remark or "bind")[:64],
                "by": (bound_by or "")[:64],
                "op_uid": (iot_operator_user_id or "")[:64],
                "op_name": (iot_operator_name or "")[:128],
                "cid": child_id,
            },
        )
        return int(existing["id"])
    return execute_insert(
        """
        INSERT INTO experiment_order_iot_bind
            (order_id, child_id, order_pk_id, iot_device_id, bind_status,
             iot_task_sync_status, last_event, bound_by,
             iot_operator_user_id, iot_operator_name, created_at, updated_at)
        VALUES
            (%(oid)s, %(cid)s, %(pk)s, %(did)s, 'bound',
             '', %(ev)s, %(by)s,
             %(op_uid)s, %(op_name)s, NOW(), NOW())
        """,
        {
            "oid": order_id,
            "cid": child_id,
            "pk": order_pk_id,
            "did": device_id,
            "ev": (remark or "bind")[:64],
            "by": (bound_by or "")[:64],
            "op_uid": (iot_operator_user_id or "")[:64],
            "op_name": (iot_operator_name or "")[:128],
        },
    )


def update_task_sync(
    child_id: int,
    *,
    task_id: str | None = None,
    sync_status: str,
    last_event: str = "",
) -> None:
    ensure_schema()
    execute(
        """
        UPDATE experiment_order_iot_bind
        SET iot_task_id = COALESCE(%(tid)s, iot_task_id),
            iot_task_sync_status = %(st)s,
            last_event = IF(%(ev)s = '', last_event, %(ev)s),
            last_sync_at = NOW(),
            updated_at = NOW()
        WHERE child_id = %(cid)s
        """,
        {
            "tid": task_id,
            "st": sync_status,
            "ev": (last_event or "")[:64],
            "cid": child_id,
        },
    )


def mark_unbound(child_id: int) -> None:
    ensure_schema()
    execute(
        """
        UPDATE experiment_order_iot_bind
        SET bind_status = 'unbound',
            last_event = 'unbind',
            updated_at = NOW()
        WHERE child_id = %(cid)s
        """,
        {"cid": child_id},
    )


def update_from_callback(
    child_id: int,
    *,
    bind_status: str,
    event: str,
    run_id: str | None = None,
    data_ref: Any = None,
    task_id: str | None = None,
) -> None:
    ensure_schema()
    ref_text = None
    if data_ref is not None:
        if isinstance(data_ref, (dict, list)):
            ref_text = json.dumps(data_ref, ensure_ascii=False)
        else:
            ref_text = str(data_ref)
    execute(
        """
        UPDATE experiment_order_iot_bind
        SET bind_status = %(bs)s,
            last_event = %(ev)s,
            iot_run_id = COALESCE(%(rid)s, iot_run_id),
            iot_data_ref = COALESCE(%(ref)s, iot_data_ref),
            iot_task_id = COALESCE(%(tid)s, iot_task_id),
            last_sync_at = NOW(),
            updated_at = NOW()
        WHERE child_id = %(cid)s
        """,
        {
            "bs": bind_status,
            "ev": (event or "")[:64],
            "rid": run_id,
            "ref": ref_text,
            "tid": task_id,
            "cid": child_id,
        },
    )


def try_insert_callback_event(event_id: str, summary: str = "") -> bool:
    """插入幂等事件；已存在返回 False。"""
    ensure_schema()
    eid = str(event_id or "").strip()
    if not eid:
        return True
    existing = fetch_one(
        "SELECT event_id FROM iot_callback_event WHERE event_id = %(id)s LIMIT 1",
        {"id": eid},
    )
    if existing:
        return False
    try:
        execute(
            """
            INSERT INTO iot_callback_event (event_id, created_at, payload_summary)
            VALUES (%(id)s, NOW(), %(sum)s)
            """,
            {"id": eid, "sum": (summary or "")[:512]},
        )
        return True
    except Exception:
        # 并发下唯一键冲突视为重复
        again = fetch_one(
            "SELECT event_id FROM iot_callback_event WHERE event_id = %(id)s LIMIT 1",
            {"id": eid},
        )
        return not bool(again)


def update_child_line_id(child_id: int, line_id: str) -> None:
    execute(
        "UPDATE experiment_order_child SET line_id = %(lid)s WHERE id = %(id)s",
        {"lid": (line_id or "")[:64], "id": child_id},
    )


def user_owns_order(*, user_id: int, mobile: str, order_pk: int | None, business_order_id: str = "") -> bool:
    """对齐 myExperimentOrderList：custom_user_id / mobile。"""
    params: dict[str, Any] = {
        "user_id": user_id,
        "user_id_str": str(user_id),
        "mobile": mobile or "",
    }
    where_id = ""
    if order_pk:
        where_id = "t.id = %(pk)s"
        params["pk"] = order_pk
    elif business_order_id:
        where_id = "t.order_id = %(oid)s"
        params["oid"] = str(business_order_id)
    else:
        return False
    row = fetch_one(
        f"""
        SELECT t.id
        FROM experiment_order t
        LEFT JOIN qd_user_company quc ON t.company_id = quc.id
        WHERE {where_id}
          AND (
            t.custom_user_id = %(user_id)s
            OR CAST(t.custom_user_id AS CHAR) = %(user_id_str)s
            OR quc.contract_phone = %(mobile)s
            OR t.mobile = %(mobile)s
          )
        LIMIT 1
        """,
        params,
    )
    return bool(row)


def serialize_bind(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row.get("id"),
        "orderId": row.get("order_id"),
        "childId": row.get("child_id"),
        "orderPkId": row.get("order_pk_id"),
        "iotDeviceId": row.get("iot_device_id"),
        "bindStatus": row.get("bind_status"),
        "iotTaskId": row.get("iot_task_id"),
        "iotTaskSyncStatus": row.get("iot_task_sync_status"),
        "iotRunId": row.get("iot_run_id"),
        "iotDataRef": row.get("iot_data_ref"),
        "lastEvent": row.get("last_event"),
        "lastSyncAt": row.get("last_sync_at"),
        "boundBy": row.get("bound_by"),
        "iotOperatorUserId": row.get("iot_operator_user_id") or "",
        "iotOperatorName": row.get("iot_operator_name") or "",
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
    }
