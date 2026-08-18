from django.urls import resolve
from rest_framework.exceptions import PermissionDenied

from apps.identity.services.org import require_legacy_permission


def test_org_urls_registered():
    assert resolve("/api/v1/identity/users").func.view_class.__name__ == "UserListView"
    assert resolve("/api/v1/identity/users/u1/roles").func.view_class.__name__ == "UserRoleView"
    assert resolve("/api/v1/identity/departments").func.view_class.__name__ == "DepartmentTreeView"
    assert resolve("/api/v1/identity/roles/r1/menus").func.view_class.__name__ == "RoleMenuView"
    assert resolve("/api/v1/identity/menus/all").func.view_class.__name__ == "MenuAdminTreeView"
    assert resolve("/api/v1/identity/menus/m1").func.view_class.__name__ == "MenuDetailView"
    assert resolve("/api/v1/identity/auth/password").func.view_class.__name__ == "ChangeMyPasswordView"
    assert resolve("/api/v1/identity/auth/data-scope").func.view_class.__name__ == "DataScopeView"
    assert resolve("/api/v1/identity/users/u1/data-scope").func.view_class.__name__ == "DataScopeView"


def test_users_requires_jwt(client):
    r = client.get("/api/v1/identity/users", HTTP_X_CHANNEL="mall_qd")
    assert r.status_code in (401, 403)


def test_menus_all_requires_jwt(client):
    r = client.get("/api/v1/identity/menus/all", HTTP_X_CHANNEL="mall_qd")
    assert r.status_code in (401, 403)


def test_change_password_requires_jwt(client):
    r = client.post(
        "/api/v1/identity/auth/password",
        data={"old_password": "a", "new_password": "b"},
        content_type="application/json",
        HTTP_X_CHANNEL="mall_qd",
    )
    assert r.status_code in (401, 403)


def test_admin_filter_list_bypasses_legacy_url():
    require_legacy_permission({"scope": {"filter_list": 2}, "permissions": []}, "/sys/user/add.do")


def test_legacy_url_denied_for_non_admin():
    try:
        require_legacy_permission(
            {"scope": {"filter_list": 3}, "permissions": ["/saleOrder/submitOrder.ajax"]},
            "/sys/user/add.do",
        )
    except PermissionDenied:
        return
    raise AssertionError("expected PermissionDenied")
