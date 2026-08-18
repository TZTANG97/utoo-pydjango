from django.urls import resolve
from rest_framework.exceptions import PermissionDenied

from apps.identity.services.org import require_legacy_permission
from apps.identity.views_org import _tree


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


def test_menu_tree_skips_placeholder_root_and_keeps_real_tops():
    rows = [
        {"id": "0", "menu_super_id": "0", "menu_name": "系统菜单"},
        {"id": "sales", "menu_super_id": "0", "menu_name": "销售管理"},
        {"id": "order", "menu_super_id": "sales", "menu_name": "订单列表"},
        {"id": "orphan", "menu_super_id": "factory-only", "menu_name": "工厂子菜单"},
    ]
    tree = _tree(rows, "menu_super_id")
    names = [node["menu_name"] for node in tree]
    assert names == ["销售管理", "工厂子菜单"]
    assert [child["menu_name"] for child in tree[0]["children"]] == ["订单列表"]
    assert tree[1]["children"] == []


def test_dept_tree_treats_zero_parent_as_root():
    rows = [
        {"id": "root-a", "super_id": "0", "dept_name": "总部"},
        {"id": "child-a", "super_id": "root-a", "dept_name": "销售部"},
    ]
    tree = _tree(rows, "super_id")
    assert [node["dept_name"] for node in tree] == ["总部"]
    assert [child["dept_name"] for child in tree[0]["children"]] == ["销售部"]
