import logging

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.admin_auth.repositories import staff as staff_repo
from apps.admin_auth.services import login as login_service
from apps.admin_auth.services.menu_filter import filter_java_top_menus
from apps.admin_auth.services import menu_bff as menu_bff_service
from apps.admin_auth.services import welcome as welcome_service
from apps.admin_core.admin_ajax import admin_ajax_view, ajax_response
from apps.core.responses import ajax_fail, ajax_ok
from apps.core.svc_proxy import forward_identity, identity_get, svc_identity_enabled

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
    if svc_identity_enabled():
        request.META.setdefault("HTTP_X_CHANNEL", "admin")
        upstream = forward_identity(request, "/api/v1/identity/auth/login")
        if not isinstance(upstream, Response):
            return upstream
        body = upstream.data if isinstance(upstream.data, dict) else {}
        if upstream.status_code >= 500:
            return Response(ajax_fail(body.get("message") or "身份中台不可用"))
        if body.get("code") == 0:
            data = body.get("data") or {}
            row = staff_repo.find_sy_user_by_login_name(
                data.get("loginName") or _login_payload(request)[0]
            )
            if row:
                staff_repo.update_login_success(str(row["id"]), _client_ip(request))
            return Response(ajax_ok(obj=data, res_msg=body.get("message") or "登录成功"))
        return Response(ajax_fail(body.get("message") or "登录失败"))

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


def _bearer_token(request: Request) -> str:
    auth = (request.META.get("HTTP_AUTHORIZATION") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (
        request.META.get("HTTP_TOKEN")
        or request.headers.get("token")
        or ""
    ).strip()


def _java_usercenter_from_identity(data: dict) -> dict:
    """identity users/{id} 原子字段 → Java /vue/usercenter.ajax camelCase。"""
    return {
        "id": str(data.get("id") or ""),
        "userName": data.get("user_name") or "",
        "trueName": data.get("true_name") or "",
        "email": data.get("email") or "",
        "mobilePhoneNumber": data.get("mobile_phone_number") or "",
        "deptId": str(data.get("dept_id") or ""),
        "type": data.get("type") or "",
        "utooType": data.get("utoo_type") or "",
        "userStatus": data.get("user_status"),
        "accountType": data.get("account_type"),
        "ptType": data.get("pt_type") or "",
    }


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def main(request: Request, user=None):
    # 方案 B：identity 只提供原子 menu-ids / menus/all；树拼装在网关
    if not svc_identity_enabled():
        return Response(
            ajax_fail("身份中台未配置（请设置 IDENTITY_MID_SERVICE_URL / SVC_IDENTITY_URL）"),
            status=503,
        )
    token = _bearer_token(request)
    if not token:
        return ajax_response(False, res_msg="用户未登录或登录已失效，请重新登录")
    try:
        menus = menu_bff_service.build_utoo_admin_menu_tree(token=token, user=user)
    except menu_bff_service.UtooMenuBffError as exc:
        if exc.status >= 500:
            return Response(ajax_fail(str(exc)), status=exc.status)
        return ajax_response(False, res_msg=str(exc))
    return ajax_response(
        True,
        res_msg="获取菜单和用户名成功!",
        obj={
            "menus": filter_java_top_menus(menus or []),
            "userName": (user or {}).get("true_name") or (user or {}).get("user_name"),
        },
    )


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def usercenter(request: Request, user=None):
    # 方案 B：用户资料读 identity；不可用时 503，禁止网关直查 sy_users 兜底
    if not svc_identity_enabled():
        return Response(
            ajax_fail("身份中台未配置（请设置 IDENTITY_MID_SERVICE_URL / SVC_IDENTITY_URL）"),
            status=503,
        )
    user_id = str((user or {}).get("user_id") or (user or {}).get("sub") or "").strip()
    if not user_id:
        return ajax_response(False, res_msg="用户未登录或登录已失效，请重新登录")
    token = _bearer_token(request)
    if not token:
        return ajax_response(False, res_msg="用户未登录或登录已失效，请重新登录")
    upstream = identity_get(f"/api/v1/identity/users/{user_id}", token=token, channel="admin")
    if upstream.status_code >= 500:
        return Response(ajax_fail("身份中台不可用"), status=503)
    if upstream.status_code == 404:
        return ajax_response(False, res_msg="用户不存在")
    if upstream.status_code == 401:
        return ajax_response(False, res_msg="用户未登录或登录已失效，请重新登录")
    body = upstream.data if isinstance(upstream.data, dict) else {}
    data = body.get("data") if isinstance(body.get("data"), dict) else None
    if data is None and upstream.status_code >= 400:
        return ajax_response(False, res_msg=body.get("message") or body.get("detail") or "获取用户失败")
    if not isinstance(data, dict):
        return ajax_response(False, res_msg="获取用户失败")
    return ajax_response(True, obj=_java_usercenter_from_identity(data))


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@admin_ajax_view(require_staff=True)
def welcome(request: Request, user=None):
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
            user or {},
            token=_bearer_token(request),
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
        token=_bearer_token(request),
    )
    return Response(
        ajax_ok(
            obj=datatable_response(draw=params["draw"], total=total, rows=rows),
            res_msg="ok",
        )
    )
