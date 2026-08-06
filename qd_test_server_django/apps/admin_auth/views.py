import logging

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_auth.services import login as login_service
from apps.admin_auth.services import menu as menu_service
from apps.admin_auth.services import welcome as welcome_service
from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.core.responses import ajax_fail, ajax_ok

logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or request.META.get("REMOTE_ADDR") or ""


def _login_payload(request: Request) -> tuple[str, str]:
    data = request.data if isinstance(request.data, dict) else {}
    q = request.query_params
    login_name = (
        data.get("loginName")
        or data.get("userName")
        or data.get("name")
        or q.get("loginName")
        or q.get("userName")
        or ""
    ).strip()
    password = data.get("password") or q.get("password") or ""
    return login_name, password


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def user_login(request: Request):
    login_name, password = _login_payload(request)
    if not login_name or not password:
        return Response(ajax_fail("用户名或密码不能为空"))

    try:
        payload, err = login_service.authenticate_staff(login_name, password)
        if err:
            return Response(ajax_fail(err))
        row = staff_repo.find_sy_user_by_login_name(login_name)
        if row:
            staff_repo.update_login_success(str(row["id"]), _client_ip(request))
        return Response(ajax_ok(obj=payload, res_msg="登录成功"))
    except Exception as exc:
        logger.exception("admin login failed: %s", exc)
        return Response(ajax_fail(f"登录失败：{exc}"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_encryption(_request: Request):
    """Java 兼容占位：新 Vue 管理端开发期可传明文密码。"""
    return Response(ajax_ok(obj={"modulus": ""}, res_msg="ok"))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def main(request: Request, user=None):
    menus = menu_service.select_menus_top(str(user.get("user_id")))
    return ajax_response(
        True,
        res_msg="获取菜单和用户名成功!",
        obj={"menus": menus, "userName": user.get("true_name") or user.get("user_name")},
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def usercenter(_request: Request, user=None):
    row = staff_repo.find_sy_user_by_login_name(user.get("user_name") or "")
    if row:
        return ajax_response(True, obj=staff_repo.serialize_sy_user(row))
    return ajax_response(True, obj=user)


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def welcome(request: Request, user=None):
    row = staff_repo.find_sy_user_by_login_name(user.get("user_name") or "")
    payload_user = {**user}
    if row:
        payload_user.update(
            {
                "true_name": row.get("true_name"),
                "type": row.get("type"),
                "utoo_type": row.get("utoo_type"),
                "email": row.get("email"),
                "mobile_phone_number": row.get("mobile_phone_number"),
                "dept_id": row.get("dept_id"),
                # welcome 计数以 sy_users.id 为准
                "user_id": str(row.get("id") or user.get("user_id") or ""),
            }
        )
    body = getattr(request, "data", None) or {}
    chart_year = request.query_params.get("year") or (
        body.get("year") if isinstance(body, dict) else None
    )
    order_type = request.query_params.get("order_type") or (
        body.get("order_type") if isinstance(body, dict) else None
    ) or (
        body.get("orderType") if isinstance(body, dict) else None
    )
    try:
        cy = int(chart_year) if chart_year not in (None, "") else None
    except (TypeError, ValueError):
        cy = None
    return ajax_response(
        True,
        obj=welcome_service.build_welcome_payload(
            payload_user,
            chart_year=cy,
            order_type_filter=str(order_type or ""),
        ),
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def sys_logs(request: Request, user=None):
    del user
    from apps.admin_core.datatable import datatable_response, parse_datatable

    params = parse_datatable(request)
    keyword = str(params.get("userName") or params.get("keyword") or "").strip()
    add_time = str(params.get("addTime") or "").strip()
    rows, total = welcome_service.list_sys_logs_page(
        offset=params["offset"],
        limit=params["limit"],
        keyword=keyword,
        add_time=add_time,
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )
