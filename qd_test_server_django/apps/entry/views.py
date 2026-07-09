from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.auth_pc.views import get_current_user_from_request, is_exp_customer
from apps.core.entry_forward import forward_entry_first
from apps.core.pc_ajax import pc_ajax_view
from apps.core.responses import api_fail, api_ok
from apps.entry.services import EntryService


def _viewer_id(user: dict | None) -> int:
    if user and is_exp_customer(user) and user.get("user_id"):
        return int(user["user_id"])
    return 0


def _q(request: Request, name: str, default: str = "") -> str:
    q = request.query_params.get(name)
    if q is not None and str(q) != "":
        return str(q)
    body = request.data if isinstance(request.data, dict) else {}
    v = body.get(name)
    return str(v) if v is not None else default


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def comment_tree(request: Request, user=None):
    user = get_current_user_from_request(request)
    data = EntryService.comment_tree(
        viewer_id=_viewer_id(user),
        start=_q(request, "start", "0"),
        length=_q(request, "length", "10"),
        draw=_q(request, "draw", "1"),
        order_by=_q(request, "orderBy", "addTime"),
        order_type=_q(request, "orderType", "desc"),
    )
    return Response(api_ok(data, message="返回成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def publish_list(request: Request, user=None):
    data = EntryService.publish_list(
        user_id=int(user["user_id"]),
        start=_q(request, "start", "0"),
        length=_q(request, "length", "10"),
        draw=_q(request, "draw", "1"),
        order_by=_q(request, "orderBy", "addTime"),
        order_type=_q(request, "orderType", "desc"),
    )
    return Response(api_ok(data, message="返回成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def like_list(request: Request, user=None):
    fav_type = int(_q(request, "type", "1")) if _q(request, "type", "1").isdigit() else 1
    data = EntryService.like_list(
        user_id=int(user["user_id"]),
        fav_type=fav_type,
        start=_q(request, "start", "0"),
        length=_q(request, "length", "10"),
        draw=_q(request, "draw", "1"),
    )
    return Response(api_ok(data, message="返回成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view()
def comments_by_entry(request: Request, user=None):
    user = get_current_user_from_request(request)
    entry_id = _q(request, "entryId")
    if not entry_id or not entry_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    comments = EntryService.entry_comments(
        viewer_id=_viewer_id(user),
        entry_id=int(entry_id),
    )
    return Response(api_ok(comments, message="返回成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def entry_detail(request: Request, user=None):
    eid = _q(request, "id")
    if not eid or not eid.isdigit():
        return Response(api_fail(400, "参数错误"))
    data = EntryService.entry_detail(
        user_id=int(user["user_id"]),
        entry_id=int(eid),
    )
    if not data:
        return Response(api_fail(404, "帖子不存在"))
    return Response(api_ok(data, message="返回成功"))


@forward_entry_first
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def insert_entry(request: Request, user=None):
    body = request.data if isinstance(request.data, dict) else {}
    success, msg = EntryService.insert_entry(
        user_id=int(user["user_id"]),
        title=str(body.get("title") or ""),
        content=str(body.get("content") or ""),
        photo_ids=str(body.get("photoIds") or ""),
    )
    if not success:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def delete_entry(request: Request, user=None):
    eid = _q(request, "id")
    if not eid or not eid.isdigit():
        return Response(api_fail(400, "参数错误"))
    success, msg = EntryService.delete_entry(int(eid))
    if not success:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def update_comment(request: Request, user=None):
    cid = _q(request, "id")
    if not cid or not cid.isdigit():
        return Response(api_fail(400, "参数错误"))
    success, msg = EntryService.soft_delete_comment(int(cid))
    if not success:
        return Response(api_fail(400, msg))
    return Response(api_ok(message=msg))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def entry_is_like(request: Request, user=None):
    entry_id = _q(request, "entryId")
    if not entry_id or not entry_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    fav_type = int(_q(request, "type", "1")) if _q(request, "type", "1").isdigit() else 1
    data = EntryService.toggle_entry_favorite(
        user_id=int(user["user_id"]),
        entry_id=int(entry_id),
        is_flag=_q(request, "isFlag", "1"),
        fav_type=fav_type,
    )
    if not data:
        return Response(api_fail(404, "帖子不存在"))
    return Response(api_ok(data, message="操作成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def comment_like(request: Request, user=None):
    comment_id = _q(request, "commentId")
    if not comment_id or not comment_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    data = EntryService.toggle_comment_like(
        user_id=int(user["user_id"]),
        comment_id=int(comment_id),
        is_flag=_q(request, "isFlag", "1"),
    )
    if not data:
        return Response(api_fail(404, "评论不存在"))
    return Response(api_ok(data, message="操作成功"))


@forward_entry_first
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@pc_ajax_view(require_customer=True)
def insert_comment(request: Request, user=None):
    entry_id = _q(request, "entryId")
    if not entry_id or not entry_id.isdigit():
        return Response(api_fail(400, "参数错误"))
    success, msg, comment = EntryService.insert_comment(
        user_id=int(user["user_id"]),
        entry_id=int(entry_id),
        content=_q(request, "content"),
        parent_id=_q(request, "parentId"),
        top_level=_q(request, "topLevel"),
    )
    if not success:
        return Response(api_fail(400, msg))
    return Response(api_ok(comment, message=msg))
