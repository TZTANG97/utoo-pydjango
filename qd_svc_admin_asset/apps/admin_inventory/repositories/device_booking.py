from __future__ import annotations

from datetime import datetime
from typing import Any

from apps.admin_inventory.helpers import page_clause
from apps.core.db_utils import fetch_all, fetch_one, scalar
from apps.core.services.sysconfig import get_config_row, image_web_server

# 测试状态圆点：0离线 1待机(绿) 2运行中(黄) 3禁用(红)
DOT_LABEL = {0: "离线", 1: "待机", 2: "运行中", 3: "禁用"}


def _norm(v: Any) -> str:
    s = str(v or "").strip()
    return "" if s in ("", "0", "null", "None") else s


def _photo_url(photo_id: Any) -> str:
    if not photo_id:
        return ""
    try:
        pid = int(photo_id)
    except (TypeError, ValueError):
        return ""
    acc = fetch_one("SELECT path, name FROM accessory WHERE id = %(id)s LIMIT 1", {"id": pid})
    if not acc:
        return ""
    path = str(acc.get("path") or "").strip().strip("/")
    name = str(acc.get("name") or "").strip()
    if not path or not name:
        return ""
    base = image_web_server(get_config_row())
    if not base:
        return f"/{path}/{name}"
    return f"{base}/{path}/{name}"


def _compute_dot(line_id: int, status: Any) -> int:
    """对齐 Java ExperimentLogController.list 中的 dot 计算。"""
    st = str(status if status is not None else "")
    if st in ("", "2", "0", "None"):
        return 3
    dot = 1 if st == "1" else 3
    now = datetime.now()
    logs = fetch_all(
        """
        SELECT start_time AS startTime, end_time AS endTime
        FROM experiment_log
        WHERE IFNULL(deleteStatus, 0) = 0 AND line_id = %(line_id)s
        ORDER BY addTime DESC
        LIMIT 50
        """,
        {"line_id": line_id},
    )
    for log in logs:
        start = log.get("startTime")
        if not start:
            break
        if isinstance(start, str):
            try:
                start = datetime.strptime(start[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        end = log.get("endTime")
        if isinstance(end, str) and end:
            try:
                end = datetime.strptime(end[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                end = None
        if start <= now and end is None:
            return 2
        if end is not None and start <= now < end:
            return 2
    return dot


def list_device_bookings(
    *,
    lab_num: str = "",
    lab_name: str = "",
    line_num: str = "",
    class_id: str = "",
    status: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    # Java: t.deleteStatus=0 and m.deleteStatus=0
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0 AND IFNULL(m.deleteStatus, 0) = 0"
    params: dict[str, Any] = {}
    lab_num = _norm(lab_num)
    lab_name = _norm(lab_name)
    line_num = _norm(line_num)
    class_id = _norm(class_id)
    status = _norm(status)
    if lab_num:
        where += " AND l.lab_num LIKE %(lab_num)s"
        params["lab_num"] = f"%{lab_num}%"
    if lab_name:
        where += " AND l.lab_name LIKE %(lab_name)s"
        params["lab_name"] = f"%{lab_name}%"
    if line_num:
        where += " AND t.line_num LIKE %(line_num)s"
        params["line_num"] = f"%{line_num}%"
    if class_id:
        where += " AND t.class_id = %(class_id)s"
        params["class_id"] = class_id
    if status:
        where += " AND t.status = %(status)s"
        params["status"] = status

    total = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM experiment_line t
            INNER JOIN experiment_manage m ON t.class_id = m.id
            LEFT JOIN experiment_lab l ON t.lab_id = l.id
            {where}
            """,
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.line_num AS lineNum, t.lab_id AS labId,
            t.class_id AS classId, t.status, t.line_status AS lineStatus,
            t.run_num AS runNum,
            m.name AS className, m.manage_main_photo_id AS manageMainPhotoId,
            l.lab_num AS labNum, l.lab_name AS labName, l.country
        FROM experiment_line t
        INNER JOIN experiment_manage m ON t.class_id = m.id
        LEFT JOIN experiment_lab l ON t.lab_id = l.id
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        lid = int(row.get("id") or 0)
        dot = _compute_dot(lid, row.get("status"))
        row["dot"] = dot
        row["dotLabel"] = DOT_LABEL.get(dot, "-")
        row["statusLabel"] = "启用" if str(row.get("status")) == "1" else "禁用"
        row["photoUrl"] = _photo_url(row.get("manageMainPhotoId"))
        # 兼容 Java 字段
        row["line_num"] = row.get("lineNum")
        row["class_id"] = row.get("classId")
    return rows, total


def get_device_booking(line_id: int) -> dict[str, Any] | None:
    row = fetch_one(
        """
        SELECT
            t.id, t.addTime, t.line_num AS lineNum, t.lab_id AS labId,
            t.class_id AS classId, t.status, t.line_status AS lineStatus,
            t.run_num AS runNum,
            m.name AS className, m.manage_main_photo_id AS manageMainPhotoId,
            l.lab_num AS labNum, l.lab_name AS labName, l.country, l.lab_userid AS labUserid,
            country_d.dis_name AS countryName
        FROM experiment_line t
        LEFT JOIN experiment_manage m ON t.class_id = m.id
        LEFT JOIN experiment_lab l ON t.lab_id = l.id
        LEFT JOIN sy_district country_d ON l.country = country_d.id
        WHERE t.id = %(id)s
        LIMIT 1
        """,
        {"id": line_id},
    )
    if not row:
        return None
    names = []
    for uid in str(row.get("labUserid") or "").split(","):
        uid = uid.strip()
        if not uid:
            continue
        u = fetch_one(
            "SELECT user_name AS userName, true_name AS trueName FROM sy_users WHERE id = %(id)s LIMIT 1",
            {"id": uid},
        )
        if u:
            names.append(str(u.get("userName") or u.get("trueName") or uid))
    row["labUserName"] = "，".join(names) if names else ""
    dot = _compute_dot(line_id, row.get("status"))
    row["dot"] = dot
    row["dotLabel"] = DOT_LABEL.get(dot, "-")
    row["statusLabel"] = "启用" if str(row.get("status")) == "1" else "禁用"
    row["photoUrl"] = _photo_url(row.get("manageMainPhotoId"))
    add = row.get("addTime")
    row["addTimeStr"] = str(add).replace("T", " ")[:19] if add else ""
    return row


def list_booking_logs(line_id: int, *, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0 AND t.line_id = %(line_id)s"
    params: dict[str, Any] = {"line_id": line_id}
    total = int(scalar(f"SELECT COUNT(*) FROM experiment_log t {where}", params) or 0)
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT
            t.id, t.addTime, t.line_id AS lineId, t.order_child_id AS orderChildId,
            t.start_time AS startTime, t.end_time AS endTime, t.status
        FROM experiment_log t
        {where}
        ORDER BY t.addTime DESC
        {clause}
        """,
        {**params, **page_params},
    )
    for row in rows:
        child_id = row.get("orderChildId")
        row["orderId"] = ""
        row["userName"] = ""
        if child_id:
            child = fetch_one(
                """
                SELECT c.test_user_id AS testUserId,
                       c.order_id AS childOrderSn,
                       c.order_form_id AS formId,
                       eo.order_id AS parentOrderSn, eo.id AS parentId
                FROM experiment_order_child c
                LEFT JOIN experiment_order eo ON c.order_form_id = eo.id
                WHERE c.id = %(id)s
                LIMIT 1
                """,
                {"id": child_id},
            )
            if child:
                # Java: getPurchaseOrdersByParentId 取第一个采购单号；无则退回子单 order_id
                order_sn = str(child.get("childOrderSn") or "")
                parent_id = child.get("parentId")
                if parent_id:
                    sub = fetch_one(
                        """
                        SELECT order_id AS orderSn
                        FROM experiment_order
                        WHERE parent_id = %(pid)s
                        ORDER BY id ASC
                        LIMIT 1
                        """,
                        {"pid": parent_id},
                    )
                    if sub and sub.get("orderSn"):
                        order_sn = str(sub["orderSn"])
                    elif child.get("parentOrderSn"):
                        order_sn = str(child["parentOrderSn"])
                row["orderId"] = order_sn
                row["order_id"] = order_sn
                uid = child.get("testUserId")
                if uid:
                    u = fetch_one(
                        "SELECT user_name AS userName FROM sy_users WHERE id = %(id)s LIMIT 1",
                        {"id": uid},
                    )
                    if u:
                        row["userName"] = str(u.get("userName") or "")
                        row["user_name"] = row["userName"]
        st = row.get("startTime")
        et = row.get("endTime")
        row["startTime"] = str(st).replace("T", " ")[:19] if st else ""
        row["endTime"] = str(et).replace("T", " ")[:19] if et else ""
        row["start_time"] = row["startTime"]
        row["end_time"] = row["endTime"]
    return rows, total


def list_lab_options() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, lab_num AS labNum, lab_name AS labName
        FROM experiment_lab
        WHERE IFNULL(deleteStatus, 0) = 0 AND IFNULL(status, 1) = 1
        ORDER BY lab_name ASC
        """
    )


def list_class_options() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, name AS className
        FROM experiment_manage
        WHERE IFNULL(deleteStatus, 0) = 0
        ORDER BY name ASC
        """
    )


def list_line_options() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, line_num AS lineNum
        FROM experiment_line
        WHERE IFNULL(deleteStatus, 0) = 0 AND IFNULL(status, 1) = 1
        ORDER BY line_num ASC
        """
    )


def list_sel_lines(
    *,
    line_num: str = "",
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    """小程序 selLineList：返回 id + line_num。"""
    where = "WHERE IFNULL(t.deleteStatus, 0) = 0 AND IFNULL(t.status, 1) = 1"
    params: dict[str, Any] = {}
    line_num = _norm(line_num)
    if line_num:
        where += " AND t.line_num LIKE %(line_num)s"
        params["line_num"] = f"%{line_num}%"
    total = int(
        scalar(
            f"SELECT COUNT(*) FROM experiment_line t {where}",
            params,
        )
        or 0
    )
    clause, page_params = page_clause(page, page_size)
    rows = fetch_all(
        f"""
        SELECT t.id, t.line_num AS line_num, t.line_num AS lineNum
        FROM experiment_line t
        {where}
        ORDER BY t.line_num ASC
        {clause}
        """,
        {**params, **page_params},
    )
    return rows or [], total
