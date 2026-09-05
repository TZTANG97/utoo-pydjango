"""评价客户 — 对齐 Java eveluateCompany/saveEveluate.ajax。"""
from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_experiment.helpers import merge_payload, to_int
from apps.auth_pc.views import get_current_user_from_request
from apps.core.db_utils import execute_insert, fetch_one
from apps.core.responses import ajax_fail, ajax_ok


def _user_display(user: dict | None) -> tuple[str, str]:
    if not user:
        return "", ""
    uid = str(user.get("user_id") or user.get("id") or "")
    name = str(user.get("true_name") or user.get("user_name") or user.get("username") or "")
    return uid, name


def _save_eveluate_row(
    *,
    of_id: int,
    content: str,
    point: float,
    of_no: str = "",
    user: dict | None = None,
) -> tuple[bool, str]:
    of = fetch_one(
        """
        SELECT t.id, t.order_id AS orderId, t.customer_name AS companyId, q.name AS companyName
        FROM experiment_order t
        LEFT JOIN qd_user_company q ON t.customer_name = q.id
        WHERE t.id = %(id)s AND IFNULL(t.deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"id": of_id},
    )
    if not of:
        return False, "订单不存在"
    uid, uname = _user_display(user)
    try:
        execute_insert(
            """
            INSERT INTO qd_eveluate_company
                (customer_id, customer_name, evaluate_user_id, evaluate_user_name,
                 eveluate_point, msg, add_time, of_no, of_id)
            VALUES
                (%(cid)s, %(cname)s, %(uid)s, %(uname)s,
                 %(point)s, %(msg)s, NOW(), %(of_no)s, %(of_id)s)
            """,
            {
                "cid": of.get("companyId"),
                "cname": (of.get("companyName") or "")[:40],
                "uid": uid[:40],
                "uname": uname[:40],
                "point": point,
                "msg": content,
                "of_no": (of_no or str(of.get("orderId") or ""))[:255],
                "of_id": of_id,
            },
        )
    except Exception:
        return False, "保存评价失败!"
    return True, "保存评价成功!"


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def save_eveluate(request: Request):
    data = merge_payload(request)
    of_id = to_int(data.get("ofId") or data.get("of_id") or data.get("id")) or 0
    content = str(data.get("content") or data.get("msg") or "").strip()
    point_raw = data.get("point") or data.get("eveluatePoint") or data.get("star")
    if not of_id or not content or point_raw in (None, ""):
        return Response(ajax_fail("参数错误"))
    try:
        point = float(point_raw)
    except (TypeError, ValueError):
        return Response(ajax_fail("评分无效"))
    ok_flag, msg = _save_eveluate_row(
        of_id=of_id,
        content=content,
        point=point,
        user=get_current_user_from_request(request),
    )
    return Response(ajax_ok(res_msg=msg) if ok_flag else ajax_fail(msg))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def save_eveluate_new(request: Request):
    """saveEveluateNew.ajax — 按订单编号评价。"""
    data = merge_payload(request)
    of_num = str(data.get("ofNum") or data.get("of_no") or data.get("order_id") or "").strip()
    content = str(data.get("content") or data.get("msg") or "").strip()
    point_raw = data.get("point") or data.get("eveluatePoint") or data.get("star")
    if not of_num or not content or point_raw in (None, ""):
        return Response(ajax_fail("参数错误"))
    try:
        point = float(point_raw)
    except (TypeError, ValueError):
        return Response(ajax_fail("评分无效"))
    row = fetch_one(
        """
        SELECT id FROM experiment_order
        WHERE order_id = %(oid)s AND IFNULL(deleteStatus, 0) = 0
        LIMIT 1
        """,
        {"oid": of_num},
    )
    if not row:
        return Response(ajax_fail("订单不存在"))
    ok_flag, msg = _save_eveluate_row(
        of_id=int(row["id"]),
        content=content,
        point=point,
        of_no=of_num,
        user=get_current_user_from_request(request),
    )
    return Response(ajax_ok(res_msg=msg) if ok_flag else ajax_fail(msg))
